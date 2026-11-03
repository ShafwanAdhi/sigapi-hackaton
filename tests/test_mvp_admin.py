import unittest
from uuid import uuid4
from psycopg.types.json import Jsonb
from tests import test_mvp_auth as fixtures


class DashboardTests(fixtures.AdminAuthTests):
    def test_historical_receipt_and_cancelled_current_destination_are_not_complete(self):
        self.login()
        before=self.client.get('/api/admin/overview').json()['counts']['forwarded']
        report=self.report();incident=uuid4()
        with self.store.connect() as db:
            db.execute('INSERT INTO incidents(id,revision) VALUES(%s,2)',(incident,))
            db.execute('UPDATE reports SET incident_id=%s WHERE id=%s',(incident,report))
            db.execute("INSERT INTO outbox(id,report_id,account_id,sender_ref,text,audience,incident_id,incident_revision,state,provider_message_id) VALUES(%s,%s,'fixture','+15551234567','fixture','authority',%s,1,'sent','old-receipt')",(uuid4(),report,incident))
        self.assertEqual(self.client.get('/api/admin/overview').json()['counts']['forwarded'],before)
        with self.store.connect() as db:
            for state,receipt in [('sent','current-receipt'),('cancelled',None)]:
                db.execute("INSERT INTO outbox(id,report_id,account_id,sender_ref,text,audience,incident_id,incident_revision,state,provider_message_id) VALUES(%s,%s,'fixture','+15551234567','fixture','authority',%s,2,%s,%s)",(uuid4(),report,incident,state,receipt))
        self.assertEqual(self.client.get('/api/admin/overview').json()['counts']['forwarded'],before)

    def report(self,region='35.73',consent=False):
        report_id=uuid4()
        with self.store.connect() as db:
            db.execute("INSERT INTO regions(code,name) VALUES(%s,'Test') ON CONFLICT DO NOTHING",(region,))
            db.execute("INSERT INTO reports(id,account_id,sender_ref,conversation_id,state,region_code) VALUES(%s,%s,'+15550123456','private-chat',%s,%s)",
                       (report_id,'admin-'+uuid4().hex,Jsonb({'consent_contact':consent,'media_ids':[]}),region))
        return report_id

    def test_report_detail_is_region_scoped_and_contact_requires_consent(self):
        self.login();own=self.report();foreign=self.report('35.74')
        detail=self.client.get('/api/admin/reports/'+str(own))
        self.assertEqual(detail.status_code,200,detail.text)
        self.assertNotIn('+15550123456',detail.text)
        self.assertNotIn('private-chat',detail.text)
        self.assertEqual(self.client.get('/api/admin/reports/'+str(foreign)).status_code,404)

    def test_review_requires_expected_revision_and_audit_reason(self):
        headers=self.login();own=self.report()
        stale=self.client.post('/api/admin/reports/'+str(own)+'/actions',headers=headers,
            json={'action':'recheck','expected_revision':999,'reason':'Operator requested check'})
        self.assertEqual(stale.status_code,409,stale.text)
        invalid=self.client.post('/api/admin/reports/'+str(own)+'/actions',headers=headers,
            json={'action':'recheck','expected_revision':1,'reason':'short'})
        self.assertEqual(invalid.status_code,422)

    def test_overview_map_and_runtime_are_real_and_authenticated(self):
        self.login();self.report()
        for path in ('overview','map','runtime'):
            response=self.client.get('/api/admin/'+path)
            self.assertEqual(response.status_code,200,response.text)
        overview=self.client.get('/api/admin/overview').json()
        self.assertGreaterEqual(overview['counts']['incomplete'],1)
        self.assertEqual(overview['region_code'],'35.73')

    def test_cross_origin_login_is_rejected(self):
        response=self.client.post('/api/admin/auth/login',headers={'Origin':'https://attacker.example'},
                                  json={'username':self.username,'password':self.password})
        self.assertEqual(response.status_code,403)

    def test_authorized_test_send_is_idempotent_and_revocation_cancels_admission(self):
        headers=self.login()
        destination=self.client.post('/api/admin/destinations',headers=headers,json={
          'name':'Authorized fixture','number':'+15550123456','role':'authority',
          'categories':['building'],'active':True,'authorized':True}).json()
        body={'request_id':str(uuid4())}
        url='/api/admin/destinations/'+destination['id']+'/test'
        first=self.client.post(url,headers=headers,json=body)
        self.assertEqual(first.status_code,202,first.text)
        self.assertEqual(self.client.post(url,headers=headers,json=body).json()['outbox_id'],first.json()['outbox_id'])
        with self.store.connect() as db:
            db.execute('UPDATE destinations SET active=false,version=version+1 WHERE id=%s',(destination['id'],))
            row=db.execute('SELECT * FROM outbox WHERE id=%s',(first.json()['outbox_id'],)).fetchone()
            token=uuid4();db.execute("UPDATE outbox SET state='leased',lease_token=%s,lease_until=now()+interval '1 minute' WHERE id=%s",(token,row['id']))
        self.assertFalse(self.store.start_send(row['id'],token))
