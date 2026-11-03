import unittest
from uuid import uuid4
from unittest.mock import patch
from tests.test_store import DSN
from tests.test_task3_engine import FakeServices
from tests import test_task3_engine as fixtures
from backend.analysis_engine import AnalysisEngine


@unittest.skipUnless(DSN,'Requires separate test database')
class WorkflowRegressionTests(unittest.TestCase):
    setUp=fixtures.EngineTests.setUp
    ingest=fixtures.EngineTests.ingest
    complete=fixtures.EngineTests.complete
    run_analysis=fixtures.EngineTests.run_analysis

    def test_new_draft_does_not_strand_previous_report_analysis(self):
        old=self.complete()
        self.ingest('REPORT');new=self.ingest('BARU')
        self.assertNotEqual(old['id'],new['id'])
        engine=AnalysisEngine(self.store,self.root,self.config,services=FakeServices(),now=lambda:fixtures.NOW)
        self.assertTrue(engine.run_once(report_id=old['id']))
        self.assertTrue(engine.run_once(report_id=old['id']))
        with self.store.connect() as db:
            result=db.execute('SELECT analysis FROM reports WHERE id=%s',(old['id'],)).fetchone()['analysis']
        self.assertEqual(result['decision']['action'],'eligible')

    def test_unclassified_new_input_defers_analysis_instead_of_losing_old_report_job(self):
        report=self.complete();self.ingest('REPORT')
        job=self.store.claim_analysis(report_id=report['id'])
        self.store.accept(dict(account_id=self.account,provider_message_id=uuid4().hex,sender_ref=self.sender,
          conversation_id=self.sender,received_at=fixtures.NOW.isoformat(),text='BARU',media_refs=[],location=None,from_me=False))
        engine=AnalysisEngine(self.store,self.root,self.config,services=FakeServices(),now=lambda:fixtures.NOW)
        engine._end(job,'superseded')
        with self.store.connect() as db:
            state=db.execute('SELECT state FROM analysis_jobs WHERE id=%s',(job['id'],)).fetchone()['state']
        self.assertEqual(state,'pending')

    def test_multiple_authorities_have_independent_delivery_identity(self):
        self.complete()
        original=self.config.destinations
        def multiple():
            base=original();authority=dict(base['authority'],role='authority')
            return {'authority-a':authority,'authority-b':dict(authority,number='+15551230002'),
                    'community':dict(base['community'],role='community')}
        self.config.destinations=multiple
        report=self.run_analysis(FakeServices())
        with self.store.connect() as db:
            rows=db.execute('SELECT destination_id FROM delivery_events WHERE report_id=%s',(report['id'],)).fetchall()
        self.assertEqual({r['destination_id'] for r in rows},{'authority-a','authority-b','community'})

    def test_conflicting_consistency_is_retained_and_holds_community(self):
        self.complete()
        services=FakeServices()
        services.consistency=lambda *args:{'outcome':'conflict','reasons':['Text contradicts media'],'source_refs':[]}
        report=self.run_analysis(services)
        self.assertEqual(report['analysis']['decision']['action'],'held')
        self.assertIn('CONSISTENCY_CONFLICT',report['analysis']['decision']['reasons'])

    def test_bad_frame_does_not_prevent_remaining_frames_being_checked(self):
        self.complete();services=FakeServices();observations=[]
        def observe(data):
            observations.append(data)
            if len(observations)==1: raise ValueError('BROKEN_FRAME')
            return {'fire_visible':True,'smoke_visible':True,'image_quality':'clear'}
        services.observe=observe
        from tests.test_web_evidence import photo
        with patch('backend.analysis_engine.sample_media',return_value=[photo(),photo(),photo()]):
            report=self.run_analysis(services)
        self.assertEqual(len(observations),3)
        self.assertEqual(report['analysis']['decision']['action'],'held')

    def test_normal_eligibility_publishes_safe_projection_and_records_run(self):
        self.complete();report=self.run_analysis(FakeServices())
        with self.store.connect() as db:
            projection=db.execute('SELECT projection FROM public_incidents WHERE incident_id=%s',(report['incident_id'],)).fetchone()
            count=db.execute('SELECT count(*) n FROM analysis_runs WHERE report_id=%s',(report['id'],)).fetchone()['n']
        self.assertIsNotNone(projection)
        self.assertNotIn(self.sender,str(projection))
        self.assertEqual(count,1)
