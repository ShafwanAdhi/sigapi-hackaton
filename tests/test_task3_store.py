import unittest
from uuid import uuid4
from backend.analysis_store import AnalysisStore
from tests.test_store import DSN


@unittest.skipUnless(DSN,'Requires separate TEST_DATABASE_URL')
class AnalysisStoreTests(unittest.TestCase):
    def setUp(self):
        self.store=AnalysisStore(DSN)
        self.store.migrate()
        self.account='analysis-test-'+uuid4().hex

    def event(self,text):
        return dict(account_id=self.account,provider_message_id=uuid4().hex,sender_ref='alice',conversation_id='alice',
                    received_at='2026-10-23T15:00:00Z',text=text,media_refs=[],location=None,from_me=False)

    def ingest(self,text):
        self.store.accept(self.event(text));self.store.run_once(account=self.account,validate=lambda row:True)
        return self.store.active_report(self.account,'alice')

    def test_new_report_schedules_extraction_without_blocking_intake(self):
        r=self.ingest('terjadi kebakaran hutan hari ini jam delapan malam')
        self.assertTrue(r['task3_enabled'])
        job=self.store.claim_analysis(account=self.account)
        self.assertEqual(job['kind'],'extract')
        self.assertEqual(job['input_seq'],r['latest_seq'])

    def test_new_input_invalidates_old_analysis_and_receipt_replay_no_new_job(self):
        r=self.ingest('KETERANGAN: Api terlihat di pepohonan')
        old=self.store.claim_analysis(account=self.account)
        self.ingest('mulai hari ini jam delapan malam')
        self.assertFalse(self.store.is_current(old))
        self.assertFalse(self.store.commit_extraction(old,{},[]))
        self.assertIsNone(self.store.active_report(self.account,'alice')['analysis'])

    def test_stale_worker_lease_cannot_commit_even_same_revision(self):
        self.ingest('Api di hutan')
        old=self.store.claim_analysis(account=self.account)
        with self.store.connect() as db:
            db.execute("UPDATE analysis_jobs SET lease_until=now()-interval '1 second' WHERE id=%s",(old['id'],))
        new=self.store.claim_analysis(account=self.account)
        self.assertNotEqual(old['lease_token'],new['lease_token'])
        self.assertFalse(self.store.commit_extraction(old,{},[]))

    def test_old_reports_not_auto_opted_in_by_migration(self):
        from backend.store import Store
        old=Store(DSN)
        old.accept(self.event('KETERANGAN: Laporan lama'))
        old.run_once(account=self.account,validate=lambda row:True)
        r=old.active_report(self.account,'alice')
        self.assertFalse(r['task3_enabled'])
        self.assertIsNone(self.store.claim_analysis(account=self.account))

    def test_provider_attempts_and_cache_survive_new_store(self):
        key='test-'+uuid4().hex
        for _ in range(3):self.assertTrue(self.store.reserve_operation(key))
        self.assertFalse(AnalysisStore(DSN).reserve_operation(key))
        self.store.cache_result(key,{'fire_visible':True})
        self.assertEqual(AnalysisStore(DSN).cached_result(key),{'fire_visible':True})

    def test_applied_migrations_do_not_repeat_ddl_during_active_intake(self):
        class QuickLockStore(AnalysisStore):
            def connect(self):
                db=super().connect();db.execute("SET lock_timeout='200ms'");return db
        with self.store.connect() as db:
            db.execute('LOCK TABLE reports IN ROW SHARE MODE')
            QuickLockStore(DSN).migrate()
