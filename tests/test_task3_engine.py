import io
import tempfile
import unittest
from datetime import datetime,timezone
from pathlib import Path
from uuid import uuid4
from PIL import Image
from backend.analysis_store import AnalysisStore
from backend.analysis_engine import AnalysisEngine
from tests.test_store import DSN


NOW=datetime(2026,10,23,15,tzinfo=timezone.utc)

class ConfigFixture:
    def __init__(self,enabled=True,account='default'):self.enabled=enabled;self.account=account
    def region(self):
        return {'type':'Feature','properties':{'code':'35.73','source':'synthetic-test','version':'1'},
                'geometry':{'type':'Polygon','coordinates':[[[112,-8],[113,-8],[113,-7],[112,-7],[112,-8]]]}}
    def snapshot(self):
        return {'source':'https://firms.modaps.eosdis.nasa.gov/test','sensor':'VIIRS',
                'fetched_at':NOW.isoformat(),'coverage_start':'2026-10-20T00:00:00Z',
                'coverage_end':NOW.isoformat(),'bbox':[112,-8,113,-7],'points':[]}
    def destinations(self):
        import hashlib
        prefix='+628'+str(int(hashlib.sha256(self.account.encode()).hexdigest()[:10],16))[:9]
        return {r:{'number':prefix+str(i),'account_id':self.account} for i,r in enumerate(('community','authority'))} if self.enabled else {}
    def allowed(self,role,number,account):return self.destinations().get(role,{}).get('number')==number and account==self.account


class FakeServices:
    def __init__(self,web='no_match',fail=False):self.web_outcome=web;self.fail=fail
    def extract(self,sources,previous):
        if self.fail:return {'outcome':'unavailable','reason':'INJECTED_429'}
        s=sources[-1]
        return {'description_sources':[{'source_id':s['id'],'quote':s['text']}],
                'time_sources':[{'source_id':s['id'],'quote':s['text']}],
                'category':'forest_land','category_source':{'source_id':s['id'],'quote':'hutan'}}
    def observe(self,data):return {'outcome':'unavailable'} if self.fail else {'fire_visible':True,'smoke_visible':True,'image_quality':'clear','observations':['Api di pepohonan']}
    def web(self,data):return {'web':{'outcome':self.web_outcome},'attempts':[]}
    def consistency(self,sources,frames,metadata):
        return {'outcome':'unavailable' if self.fail else 'supported','reasons':[],'source_refs':[]}


@unittest.skipUnless(DSN,'Requires separate test DB')
class EngineTests(unittest.TestCase):
    def setUp(self):
        self.folder=tempfile.TemporaryDirectory();self.addCleanup(self.folder.cleanup)
        self.root=Path(self.folder.name);self.account='engine-'+uuid4().hex;self.config=ConfigFixture(account=self.account)
        self.store=AnalysisStore(DSN,config=self.config);self.store.migrate()
        self.sender='engine-'+uuid4().hex

    def ingest(self,text='',**extra):
        e=dict(account_id=self.account,provider_message_id=uuid4().hex,sender_ref=self.sender,conversation_id=self.sender,
               received_at=NOW.isoformat(),text=text,media_refs=[],location=None,from_me=False)|extra
        if extra.pop('photo',False):pass
        self.store.accept(e)
        # Only process this sender's job, preserving independent test rows.
        while True:
            j=self.store.claim_job(account=self.account)
            if not j:break
            self.store.process_job(j,lambda row:True)
        return self.store.active_report(self.account,self.sender)

    def complete(self,threat=False,natural=False):
        self.ingest('REPORT')
        mid=uuid4();message=uuid4().hex
        buf=io.BytesIO();Image.new('RGB',(32,32),'orange').save(buf,'JPEG')
        path=self.root/(str(mid)+'.jpg');path.write_bytes(buf.getvalue())
        import hashlib
        with self.store.connect() as db:
            db.execute('''INSERT INTO media(id,account_id,sender_ref,provider_message_id,slot,kind,sha256,storage_key,content_type)
                VALUES(%s,%s,%s,%s,0,'image',%s,%s,'image/jpeg')''',
                (mid,self.account,self.sender,message,hashlib.sha256(buf.getvalue()).hexdigest(),path.name))
        self.ingest('',provider_message_id=message,media_refs=[{'id':str(mid)}])
        self.ingest('',location={'latitude':-7.95,'longitude':112.6})
        self.ingest('KONFIRMASI LOKASI 1')
        return self.ingest(('' if natural else 'KETERANGAN: ')+'Kebakaran hutan hari ini pukul 20.00'+('. Ada orang terjebak' if threat else ''))

    def run_analysis(self,services):
        engine=AnalysisEngine(self.store,self.root,self.config,services=services,now=lambda:NOW)
        for _ in range(8):
            if not engine.run_once(report_id=self.store.active_report(self.account,self.sender)['id']):break
        return self.store.active_report(self.account,self.sender)

    def test_complete_report_real_storage_evidence_and_two_unique_deliveries(self):
        self.complete();r=self.run_analysis(FakeServices())
        self.assertEqual(r['analysis']['decision']['action'],'eligible')
        with self.store.connect() as db:
            rows=db.execute('SELECT * FROM delivery_events WHERE report_id=%s',(r['id'],)).fetchall()
            self.assertEqual(len(rows),2)
            self.assertEqual({d['destination_id'] for d in rows},{'community','authority'})
        self.run_analysis(FakeServices())
        with self.store.connect() as db:self.assertEqual(db.execute('SELECT count(*) n FROM delivery_events WHERE report_id=%s',(r['id'],)).fetchone()['n'],2)

    def test_natural_description_completes_without_command_and_records_references(self):
        r=self.complete(natural=True);self.assertNotEqual(r['status'],'complete')
        r=self.run_analysis(FakeServices())
        self.assertEqual(r['status'],'complete');self.assertEqual(r['state']['description_source'],'ai')
        self.assertTrue(r['analysis']['decision']['evidence_refs'])

    def test_partial_frame_failure_is_held(self):
        from unittest.mock import patch
        self.complete()
        class Partial(FakeServices):
            count=0
            def observe(self,data):
                self.count+=1
                return super().observe(data) if self.count==1 else {'outcome':'unavailable'}
        import backend.analysis_engine as module
        original=module.sample_media
        with patch.object(module,'sample_media',side_effect=lambda path:original(path)*3):
            r=self.run_analysis(Partial())
        self.assertEqual(len(r['analysis']['frames']),3)
        self.assertEqual(r['analysis']['decision']['action'],'held')

    def test_stale_evidence_worker_cannot_supersede_reclaimed_job(self):
        self.complete();self.run_analysis(FakeServices())
        r=self.store.active_report(self.account,self.sender)
        self.store.opt_in(r['id'])
        engine=AnalysisEngine(self.store,self.root,self.config,services=FakeServices(),now=lambda:NOW)
        engine.run_once(report_id=r['id']) # extraction schedules evidence
        old=self.store.claim_analysis(report_id=r['id']);r,sources=self.store.snapshot(old)
        with self.store.connect() as db:db.execute("UPDATE analysis_jobs SET lease_until=now()-interval '1 second' WHERE id=%s",(old['id'],))
        replacement=self.store.claim_analysis(report_id=r['id'])
        engine._analyze(old,r,sources)
        self.assertTrue(self.store.is_current(replacement))

    def test_fast_provisional_incident_rechecks_candidates_when_time_becomes_known(self):
        self.complete();self.ingest('KETERANGAN: Kebakaran hutan hari ini pukul 14.00')
        first=self.run_analysis(FakeServices())
        self.sender='second-'+uuid4().hex
        self.complete(threat=True)
        self.ingest('KETERANGAN: Kebakaran hutan hari ini pukul 14.00. Ada orang terjebak')
        second=self.run_analysis(FakeServices())
        with self.store.connect() as db:
            candidate=db.execute('SELECT * FROM report_incident_matches WHERE report_id=%s AND incident_id=%s',(second['id'],first['incident_id'])).fetchone()
        self.assertIsNotNone(candidate)
        self.assertIn('INCIDENT_REVIEW_PENDING',second['analysis']['decision']['reasons'])

    def test_conflicting_web_holds_public_but_threat_escalates(self):
        self.complete(threat=True);r=self.run_analysis(FakeServices('conflict_candidate'))
        self.assertEqual(r['analysis']['decision']['action'],'held')
        with self.store.connect() as db:
            rows=db.execute('SELECT o.audience,o.text FROM outbox o JOIN delivery_events d ON d.outbox_id=o.id WHERE d.report_id=%s',(r['id'],)).fetchall()
        self.assertTrue(rows);self.assertTrue(all(d['audience']=='authority' for d in rows))
        self.assertTrue(all('BELUM TERVERIFIKASI' in d['text'] for d in rows))

    def test_fast_escalation_survives_extraction_revision_and_is_sendable(self):
        self.complete(threat=True);r=self.run_analysis(FakeServices('conflict_candidate'))
        with self.store.connect() as db:
            row=db.execute("SELECT * FROM outbox WHERE report_id=%s AND audience='authority' ORDER BY created_at DESC LIMIT 1",(r['id'],)).fetchone()
            token=uuid4();db.execute("UPDATE outbox SET state='leased',lease_token=%s,lease_until=now()+interval '1 minute' WHERE id=%s",(token,row['id']))
        self.assertTrue(self.store.start_send(row['id'],token))
        self.assertTrue(self.store.finish_send(row['id'],token,'receipt-test'))
        self.assertFalse(self.store.start_send(row['id'],token))

    def test_http_start_returns_current_consent_text_not_claimed_card(self):
        from fastapi.testclient import TestClient
        from backend.intake_api import create_intake_app
        self.complete();self.ingest('IZIN KONTAK YA');r=self.run_analysis(FakeServices())
        client=TestClient(create_intake_app('x'*32,self.store,self.root))
        headers={'Authorization':'Bearer '+'x'*32}
        number=self.config.destinations()['authority']['number']
        item=client.post('/internal/outbox/claim',headers=headers,json={'accounts':[self.account],'senders':[number]}).json()['item']
        self.assertNotIn('Kontak pelapor:',item['text'])
        response=client.post('/internal/outbox/'+item['id']+'/start',headers=headers,json={'lease_token':item['lease_token']}).json()
        self.assertTrue(response['started']);self.assertIn('Kontak pelapor: '+self.sender,response['text'])

    def test_sixth_distribution_waits_after_five_admissions(self):
        self.complete();r=self.run_analysis(FakeServices())
        engine=AnalysisEngine(self.store,self.root,self.config,services=FakeServices(),now=lambda:NOW)
        for i in range(6):
            with self.store.connect() as db:
                inc=db.execute('UPDATE incidents SET revision=%s WHERE id=%s RETURNING *',(i+1,r['incident_id'])).fetchone()
                engine._queue(db,r,inc,'authority')
                row=db.execute("SELECT * FROM outbox WHERE report_id=%s AND audience='authority' AND incident_revision=%s",(r['id'],i+1)).fetchone()
                token=uuid4();db.execute("UPDATE outbox SET state='leased',lease_token=%s,lease_until=now()+interval '1 minute' WHERE id=%s",(token,row['id']))
            started=self.store.start_send(row['id'],token)
            self.assertEqual(started,i<5)
            if started:self.store.finish_send(row['id'],token,'fixture-receipt-'+str(i))
        with self.store.connect() as db:
            final=db.execute('SELECT state,reason FROM outbox WHERE id=%s',(row['id'],)).fetchone()
        self.assertEqual(final,{'state':'pending','reason':'RATE_LIMITED'})

    def test_provider_down_does_not_suppress_explicit_threat(self):
        self.complete(threat=True);r=self.run_analysis(FakeServices(fail=True))
        with self.store.connect() as db:
            rows=db.execute('SELECT destination_id FROM delivery_events WHERE report_id=%s',(r['id'],)).fetchall()
        self.assertTrue(rows);self.assertEqual({d['destination_id'] for d in rows},{'authority'})

    def test_distribution_disabled_and_consent_revoke_before_send(self):
        self.config.enabled=False;self.complete();r=self.run_analysis(FakeServices())
        with self.store.connect() as db:self.assertEqual(db.execute('SELECT count(*) n FROM delivery_events WHERE report_id=%s',(r['id'],)).fetchone()['n'],0)
        self.config.enabled=True
        # New input forces fresh revision; a queued distribution must not send after correction.
        self.ingest('IZIN KONTAK YA');r=self.run_analysis(FakeServices())
        with self.store.connect() as db:
            item=db.execute("SELECT * FROM outbox WHERE report_id=%s AND audience='authority' ORDER BY created_at DESC LIMIT 1",(r['id'],)).fetchone()
            db.execute("UPDATE outbox SET state='leased',lease_token=%s,lease_until=now()+interval '1 minute' WHERE id=%s",(uuid4(),item['id']))
            item=db.execute('SELECT * FROM outbox WHERE id=%s',(item['id'],)).fetchone()
        self.ingest('IZIN KONTAK TIDAK')
        self.assertFalse(self.store.start_send(item['id'],item['lease_token']))
