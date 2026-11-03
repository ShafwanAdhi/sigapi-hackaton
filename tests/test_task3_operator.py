import unittest
from uuid import uuid4
from tests import test_task3_engine as helpers
from tests.test_task3_engine import FakeServices


class OperatorTests(helpers.EngineTests):
    def test_confirmed_correction_updates_incident_matching_anchors(self):
        from backend.operator import group_incident
        from psycopg.types.json import Jsonb
        self.complete();r=self.run_analysis(FakeServices())
        corrected={'latitude':-7.96,'longitude':112.62}
        with self.store.connect() as db:
            state=dict(r['state'],location=corrected);facts=dict(r['facts'],observed_at='2026-10-23T12:00:00+00:00',category='building')
            db.execute('UPDATE reports SET state=%s,facts=%s WHERE id=%s',(Jsonb(state),Jsonb(facts),r['id']))
            db.execute('UPDATE incidents SET pending_review=true WHERE id=%s',(r['incident_id'],))
        group_incident(self.store,r['id'],None,'Confirmed corrected point and observation time')
        with self.store.connect() as db:inc=db.execute('SELECT * FROM incidents WHERE id=%s',(r['incident_id'],)).fetchone()
        self.assertEqual(inc['location'],corrected)
        from datetime import timezone
        self.assertEqual(inc['observed_at'].astimezone(timezone.utc).isoformat(),'2026-10-23T12:00:00+00:00')
        self.assertEqual(inc['category'],'building')
        from backend.analysis_engine import AnalysisEngine
        with self.store.connect() as db:
            candidates=AnalysisEngine._find_candidates(db,r,corrected,'2026-10-23T12:00:00+00:00')
            self.assertIn(inc['id'],[x[0]['id'] for x in candidates])
            outdated=AnalysisEngine._find_candidates(db,r,r['state']['location'],'2026-10-23T12:00:00+00:00')
            self.assertNotIn(inc['id'],[x[0]['id'] for x in outdated])

    def test_review_keeps_original_evidence_and_requires_reason(self):
        from backend.operator import review_evidence
        self.complete();r=self.run_analysis(FakeServices('conflict_candidate'))
        with self.store.connect() as db:
            ev=db.execute("SELECT * FROM evidence_results WHERE report_id=%s AND revision=%s AND kind='frame'",(r['id'],r['revision'])).fetchone()
        with self.assertRaises(ValueError):review_evidence(self.store,r['id'],ev['evidence_key'],'',[])
        review_evidence(self.store,r['id'],ev['evidence_key'],'Operator confirms permission and context',['https://example.org/evidence'])
        r=self.run_analysis(FakeServices('conflict_candidate'))
        self.assertEqual(r['analysis']['decision']['action'],'eligible')
        with self.store.connect() as db:
            original=db.execute('SELECT result FROM evidence_results WHERE id=%s',(ev['id'],)).fetchone()
        self.assertEqual(original['result']['web_evidence']['web']['outcome'],'conflict_candidate')

    def test_unknown_delivery_requires_operator_receipt_or_explicit_retry(self):
        from backend.operator import reconcile
        self.complete();r=self.run_analysis(FakeServices())
        with self.store.connect() as db:
            row=db.execute("SELECT * FROM outbox WHERE report_id=%s AND audience='authority'",(r['id'],)).fetchone()
            token=uuid4();db.execute("UPDATE outbox SET state='leased',lease_token=%s,lease_until=now()+interval '1 minute' WHERE id=%s",(token,row['id']))
        self.assertTrue(self.store.start_send(row['id'],token))
        self.store.finish_send(row['id'],token)
        with self.assertRaises(ValueError):reconcile(self.store,row['id'],'','receipt')
        reconcile(self.store,row['id'],'Checked WhatsApp delivery history','receipt')
        with self.store.connect() as db:self.assertEqual(db.execute('SELECT state FROM outbox WHERE id=%s',(row['id'],)).fetchone()['state'],'sent')
