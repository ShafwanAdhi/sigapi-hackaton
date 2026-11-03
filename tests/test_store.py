import os
import unittest
from uuid import uuid4

from dotenv import dotenv_values

from backend.store import Store


DSN = os.environ.get('TEST_DATABASE_URL') or dotenv_values('.env', interpolate=False).get('TEST_DATABASE_URL')


@unittest.skipUnless(DSN, 'Requires dedicated TEST_DATABASE_URL; never use demo DB for tests')
class StoreTests(unittest.TestCase):
    def setUp(self):
        self.store = Store(DSN)
        self.store.migrate()
        self.account = 'test-' + uuid4().hex

    def event(self, text='KETERANGAN: Api membakar pohon', sender='alice', **extra):
        return dict(account_id=self.account, provider_message_id=uuid4().hex, sender_ref=sender,
                    conversation_id=sender, received_at='2026-10-23T12:00:00Z', text=text,
                    location=None, media_refs=[], from_me=False) | extra

    def ingest(self, event):
        receipt = self.store.accept(event)
        self.assertTrue(self.store.run_once(account=self.account, validate=lambda row: True))
        return receipt

    def report(self, sender='alice'):
        return self.store.active_report(self.account, sender)

    def test_replay_preserves_receipt_and_creates_one_job_and_reply(self):
        event = self.event()
        first = self.ingest(event)
        self.assertEqual(self.store.accept(event), first)
        with self.store.connect() as db:
            self.assertEqual(db.execute('SELECT count(*) n FROM jobs WHERE account_id=%s', (self.account,)).fetchone()['n'], 1)
            self.assertEqual(db.execute('SELECT count(*) n FROM outbox WHERE account_id=%s', (self.account,)).fetchone()['n'], 1)

    def test_restart_pin_confirmation_and_sender_isolation(self):
        self.ingest(self.event())
        self.ingest(self.event(sender='bob', text='KETERANGAN: Asap di tempat lain'))
        original = self.report()
        self.store = Store(DSN)
        self.ingest(self.event(text='', location={'latitude': -1, 'longitude': 110}))
        self.ingest(self.event(text='KONFIRMASI LOKASI 1'))
        self.assertEqual(self.report()['id'], original['id'])
        self.assertTrue(self.report()['state']['location_confirmed'])
        self.assertIsNone(self.report('bob')['state']['location'])

    def test_expired_worker_lease_is_recovered_and_old_token_cannot_commit(self):
        self.store.accept(self.event())
        old = self.store.claim_job(account=self.account)
        with self.store.connect() as db:
            db.execute("UPDATE jobs SET lease_until=now()-interval '1 second' WHERE id=%s", (old['id'],))
        new = self.store.claim_job(account=self.account)
        self.assertNotEqual(old['lease_token'], new['lease_token'])
        self.assertFalse(self.store.process_job(old, lambda row: True))
        self.assertTrue(self.store.process_job(new, lambda row: True))

    def test_stale_analysis_is_rejected_after_report_revision_changes(self):
        self.ingest(self.event())
        report = self.report()
        self.ingest(self.event(text='KETERANGAN: Koreksi api mulai terlihat pagi ini'))
        self.assertFalse(self.store.save_analysis(report['id'], report['revision'], {'result': 'old'}))
        self.assertIsNone(self.report()['analysis'])

    def test_explicit_new_choice_archives_old_without_deleting_it(self):
        self.ingest(self.event())
        old = self.report()
        self.ingest(self.event(text='REPORT'))
        self.assertEqual(self.report()['id'], old['id'])
        self.ingest(self.event(text='BARU'))
        self.assertNotEqual(self.report()['id'], old['id'])
        with self.store.connect() as db:
            self.assertFalse(db.execute('SELECT active FROM reports WHERE id=%s', (old['id'],)).fetchone()['active'])

    def test_outbox_unknown_is_not_automatically_retried(self):
        self.ingest(self.event())
        item = self.store.claim_outbox([self.account], ['alice'])
        self.assertTrue(self.store.start_send(item['id'], item['lease_token']))
        with self.store.connect() as db:
            db.execute("UPDATE outbox SET lease_until=now()-interval '1 second' WHERE id=%s", (item['id'],))
        self.assertIsNone(self.store.claim_outbox([self.account], ['alice']))
        with self.store.connect() as db:
            self.assertEqual(db.execute('SELECT state FROM outbox WHERE id=%s', (item['id'],)).fetchone()['state'], 'unknown')

    def test_outbox_preserves_sender_order_while_first_is_leased(self):
        self.ingest(self.event())
        self.ingest(self.event(text='KETERANGAN: Api meluas ke pohon lain'))
        first = self.store.claim_outbox([self.account], ['alice'])
        self.assertIsNone(self.store.claim_outbox([self.account], ['alice']))
        self.assertTrue(self.store.start_send(first['id'], first['lease_token']))
        self.assertTrue(self.store.finish_send(first['id'], first['lease_token'], 'sent-1'))
        self.assertIsNotNone(self.store.claim_outbox([self.account], ['alice']))

    def test_same_pin_new_provenance_invalidates_analysis_revision(self):
        self.ingest(self.event(location={'latitude': -1, 'longitude': 110}))
        old = self.report()
        self.ingest(self.event(location={'latitude': -1, 'longitude': 110}))
        self.assertGreater(self.report()['revision'], old['revision'])
        self.assertFalse(self.store.save_analysis(old['id'], old['revision'], {}))

    def test_two_workers_cannot_claim_later_message_from_same_sender(self):
        self.store.accept(self.event())
        self.store.accept(self.event(text='KETERANGAN: Api meluas ke arah timur'))
        first = self.store.claim_job(account=self.account)
        self.assertIsNone(Store(DSN).claim_job(account=self.account))
        self.assertTrue(self.store.process_job(first, lambda row: True))
        self.assertIsNotNone(Store(DSN).claim_job(account=self.account))
