import tempfile
import unittest
from uuid import uuid4
from fastapi.testclient import TestClient
from psycopg.types.json import Jsonb
from tests.test_store import DSN
from backend.mvp_store import MvpStore
from backend.intake_api import create_intake_app


@unittest.skipUnless(DSN,'Requires separate test database')
class PublicTransportTests(unittest.TestCase):
    def setUp(self):
        self.store=MvpStore(DSN);self.store.migrate()
        self.account='public-'+uuid4().hex;self.sender='+1555'+str(int(uuid4().hex[:8],16)).zfill(10)
        self.folder=tempfile.TemporaryDirectory();self.addCleanup(self.folder.cleanup)
        self.client=TestClient(create_intake_app('x'*32,self.store,self.folder.name))
        self.headers={'Authorization':'Bearer '+'x'*32}

    def event(self,text):
        return {'account_id':self.account,'sender_ref':self.sender,'provider_message_id':uuid4().hex,
                'conversation_id':self.sender,'text':text,'received_at':'2026-11-03T12:00:00Z','media_refs':[],'from_me':False}

    def test_admission_is_idempotent_and_identity_conflicts_are_rejected(self):
        # Test configuration enables public admission without contacting WhatsApp.
        self.store.set_settings({'live_gate_passed':True,'public_intake':True})
        try:
            e=self.event('REPORT');body={k:e[k] for k in ('account_id','sender_ref','provider_message_id')}
            for _ in range(20):
                self.assertEqual(self.client.post('/internal/admission',json=body,headers=self.headers).status_code,200)
            self.assertEqual(self.client.post('/internal/admission',json=body|{'sender_ref':'+15559999999'},headers=self.headers).status_code,422)
        finally:self.store.set_settings({'public_intake':False,'live_gate_passed':False})

    def test_dynamic_reporter_claim_cannot_send_unrelated_arbitrary_outbox(self):
        e=self.event('REPORT');self.store.accept(e)
        self.store.run_once(account=self.account,validate=lambda _:True)
        with self.store.connect() as db:
            db.execute("INSERT INTO outbox(id,account_id,sender_ref,text) VALUES(%s,%s,'+15550987654','arbitrary')",(uuid4(),self.account))
        response=self.client.post('/internal/outbox/claim',json={'accounts':[self.account],'senders':[],'public_reporters':True},headers=self.headers)
        self.assertEqual(response.status_code,200,response.text)
        self.assertEqual(response.json()['item']['sender_ref'],self.sender)
        again=self.client.post('/internal/outbox/claim',json={'accounts':[self.account],'senders':[],'public_reporters':True},headers=self.headers)
        self.assertIsNone(again.json()['item'])

    def test_track_only_reads_historical_reports_owned_by_sender(self):
        first=self.event('KETERANGAN: Api terlihat di hutan');self.store.accept(first)
        self.store.run_once(account=self.account,validate=lambda _:True)
        old=self.store.active_report(self.account,self.sender)
        with self.store.connect() as db:
            db.execute('UPDATE reports SET active=false WHERE id=%s',(old['id'],))
        with self.store.connect() as db:
            message=self.store.track_reply(db,{'account_id':self.account,'sender_ref':self.sender},'TRACK '+str(old['id']))
            unknown=self.store.track_reply(db,{'account_id':self.account,'sender_ref':'+15550000000'},'TRACK '+str(old['id']))
            missing=self.store.track_reply(db,{'account_id':self.account,'sender_ref':'+15550000000'},'TRACK '+str(uuid4()))
        self.assertIn(str(old['id'])[:8],message)
        self.assertEqual(unknown,missing)
