import hashlib
import io
import math
import tempfile
import unittest
from datetime import datetime,timedelta,timezone
from uuid import uuid4
from PIL import Image
from fastapi.testclient import TestClient
from psycopg.types.json import Jsonb
from tests.test_store import DSN
from backend.mvp_store import MvpStore
from backend.web_api import create_web_app


class PhotoResourceTests(unittest.TestCase):
    def test_large_compressed_raster_rejected_before_decode(self):
        from backend.public import sanitize_photo
        from fastapi import HTTPException
        from unittest.mock import patch
        data=io.BytesIO()
        Image.new('RGB',(5000,5000)).save(data,'PNG')
        with patch('PIL.PngImagePlugin.PngImageFile.load',side_effect=AssertionError('must not decode')):
            with self.assertRaises(HTTPException) as result:
                sanitize_photo(data.getvalue())
        self.assertEqual(result.exception.status_code,422)


@unittest.skipUnless(DSN, 'Requires separate test database')
class PublicVerificationTests(unittest.TestCase):
    def setUp(self):
        self.store=MvpStore(DSN); self.store.migrate()
        self.folder=tempfile.TemporaryDirectory(); self.addCleanup(self.folder.cleanup)
        self.client=TestClient(create_web_app(self.store,self.folder.name))
        self.incident=uuid4(); self.slug=uuid4().hex
        with self.store.connect() as db:
            db.execute("INSERT INTO incidents(id,slug,location) VALUES(%s,%s,%s)",
                       (self.incident,self.slug,Jsonb({'latitude':0,'longitude':0})))
            db.execute("INSERT INTO public_incidents(incident_id,location_version,projection) VALUES(%s,1,%s)",
                       (self.incident,Jsonb({'reference':'SIGAPI-TEST','title':'Laporan kebakaran','location':{'latitude':0,'longitude':0}})))
        self.url='/api/laporan/'+self.slug

    def payload(self, distance=100, **changes):
        return {'request_id':str(uuid4()),'choice':'valid','latitude':str(math.degrees(distance/6371008.8)),
                'longitude':'0','accuracy_m':'20','gps_fix_at':datetime.now(timezone.utc).isoformat(),
                'location_version':'1','description':'Terlihat dari tempat aman','solved':'true'}|changes

    def submit(self, data):
        return self.client.post(self.url+'/verifications', data=data)

    def test_real_receipt_replay_and_conflicting_payload(self):
        data=self.payload(); first=self.submit(data)
        self.assertEqual(first.status_code,201,first.text)
        self.assertEqual(self.submit(data).json()['receipt_id'],first.json()['receipt_id'])
        self.assertEqual(self.submit(data|{'description':'Different'}).status_code,409)
        overview=self.client.get(self.url).json()
        self.assertEqual(overview['verification']['summary'],'supporting_valid')
        self.assertEqual(overview['verification']['solved_claim_status'],'claimed_solved')
        for forbidden in ('sender_ref','accuracy_m','gps_fix_at','photo_key'):
            self.assertNotIn(forbidden,str(overview))

    def test_gps_boundary_and_rejected_attempts_do_not_become_invalid_events(self):
        for distance, expected in ((1999,201),(2000,201),(2001,422)):
            response=self.submit(self.payload(distance))
            self.assertEqual(response.status_code,expected,(distance,response.text))
        for changes in ({'latitude':'NaN'},{'accuracy_m':'101'},
                        {'gps_fix_at':(datetime.now(timezone.utc)-timedelta(seconds=61)).isoformat()},
                        {'gps_fix_at':(datetime.now(timezone.utc)+timedelta(seconds=6)).isoformat()}):
            self.assertEqual(self.submit(self.payload(**changes)).status_code,422)
        with self.store.connect() as db:
            self.assertEqual(db.execute('SELECT count(*) n FROM verification_events WHERE incident_id=%s',(self.incident,)).fetchone()['n'],2)

    def test_invalid_cannot_claim_solved_and_mixed_votes_remain_disputed(self):
        self.assertEqual(self.submit(self.payload()).status_code,201)
        self.assertEqual(self.submit(self.payload(choice='invalid')).status_code,201)
        summary=self.client.get(self.url).json()['verification']
        self.assertEqual(summary['summary'],'disputed')
        with self.store.connect() as db:
            self.assertFalse(db.execute("SELECT solved FROM verification_events WHERE incident_id=%s AND choice='invalid'",(self.incident,)).fetchone()['solved'])

    def test_unpublished_expired_and_stale_location_reject_submission(self):
        self.assertEqual(self.client.get('/api/laporan/'+uuid4().hex).status_code,404)
        with self.store.connect() as db:
            db.execute('UPDATE incidents SET location_version=2 WHERE id=%s',(self.incident,))
        self.assertEqual(self.submit(self.payload()).status_code,409)
        with self.store.connect() as db:
            db.execute('UPDATE public_incidents SET withdrawn=true WHERE incident_id=%s',(self.incident,))
        self.assertEqual(self.client.get(self.url).status_code,404)
        self.assertEqual(self.submit(self.payload()).status_code,404)

    def test_tenth_attempt_allowed_and_eleventh_rejected(self):
        for _ in range(10): self.assertEqual(self.submit(self.payload(2001)).status_code,422)
        self.assertEqual(self.submit(self.payload()).status_code,429)

    def test_optional_photo_is_decoded_and_private(self):
        data=self.payload(); picture=io.BytesIO(); Image.new('RGB',(20,20),'red').save(picture,'JPEG')
        response=self.client.post(self.url+'/verifications',data=data,files={'photo':('image.jpg',picture.getvalue(),'image/jpeg')})
        self.assertEqual(response.status_code,201,response.text)
        with self.store.connect() as db:
            key=db.execute('SELECT photo_key FROM verification_events WHERE incident_id=%s',(self.incident,)).fetchone()['photo_key']
        self.assertTrue(key)
        self.assertEqual(self.client.get('/api/laporan/'+self.slug+'/media/'+key).status_code,404)
