import io
import tempfile
import unittest
from unittest.mock import patch
from pathlib import Path
from uuid import uuid4

from fastapi.testclient import TestClient
from PIL import Image

from backend.intake_api import create_intake_app
from backend.worker import validate_media
from tests.test_store import DSN


@unittest.skipUnless(DSN, 'Requires TEST_DATABASE_URL')
class IntakeApiTests(unittest.TestCase):
    def setUp(self):
        from backend.store import Store
        self.store = Store(DSN)
        self.store.migrate()
        self.folder = tempfile.TemporaryDirectory()
        self.addCleanup(self.folder.cleanup)
        self.root = Path(self.folder.name)
        self.client = TestClient(create_intake_app('x' * 32, self.store, self.root))
        self.auth = {'Authorization': 'Bearer ' + 'x' * 32}
        self.account = 'api-test-' + uuid4().hex
        self.event = dict(account_id=self.account, provider_message_id=uuid4().hex, sender_ref='alice',
                          conversation_id='alice', received_at='2026-10-23T12:00:00Z', text='KETERANGAN: Api membakar pohon')

    def upload(self, data):
        return self.client.post('/internal/media', content=data, headers=self.auth | {
            'X-Account-Id': self.account, 'X-Sender-Ref': 'alice',
            'X-Provider-Message-Id': self.event['provider_message_id'], 'X-Media-Slot': '0', 'X-Media-Kind': 'image',
            'Content-Type': 'image/jpeg'})

    def test_receipt_202_is_committed_before_worker_and_replay_is_same(self):
        r = self.client.post('/internal/whatsapp/events', json=self.event, headers=self.auth)
        self.assertEqual(r.status_code, 202)
        receipt = r.json()
        self.assertEqual(receipt['mode'], 'intake')
        replay = self.client.post('/internal/whatsapp/events', json=self.event, headers=self.auth)
        self.assertEqual(replay.json(), receipt)
        self.assertIsNone(self.store.active_report(self.account, 'alice'))

    def test_media_upload_and_three_message_complete_report_without_contact_consent(self):
        buffer = io.BytesIO(); Image.new('RGB', (32, 32)).save(buffer, 'JPEG')
        upload = self.upload(buffer.getvalue())
        self.assertEqual(upload.status_code, 201)
        media_id = upload.json()['id']
        self.assertEqual(self.upload(buffer.getvalue()).json()['id'], media_id)
        event = self.event | {'media_refs': [{'id': media_id}]}
        for change in [{}, {'provider_message_id':uuid4().hex, 'text':'', 'media_refs':[], 'location':{'latitude':-1,'longitude':110}},
                       {'provider_message_id':uuid4().hex, 'text':'KONFIRMASI LOKASI 1', 'media_refs':[]}]:
            self.assertEqual(self.client.post('/internal/whatsapp/events', json=event | change, headers=self.auth).status_code, 202)
            self.store.run_once(account=self.account, validate=lambda row: validate_media(row, self.root))
        report = self.store.active_report(self.account, 'alice')
        self.assertEqual(report['status'], 'complete')
        self.assertFalse(report['state']['consent_contact'])
        with self.store.connect() as db:
            row = db.execute('SELECT content_type FROM media WHERE id=%s', (media_id,)).fetchone()
        self.assertEqual(row['content_type'], 'image/jpeg')

    def test_database_failure_never_returns_accepted_receipt(self):
        import psycopg
        with patch.object(self.store, 'connect', side_effect=psycopg.OperationalError()):
            response = self.client.post('/internal/whatsapp/events', json=self.event, headers=self.auth)
        self.assertEqual(response.status_code, 503)
        self.assertNotIn('receipt_id', response.json())

    def test_corrupt_photo_stays_incomplete_and_foreign_media_rejected(self):
        media_id = self.upload(b'corrupt-jpeg').json()['id']
        foreign = self.event | {'sender_ref':'bob', 'media_refs':[{'id':media_id}]}
        self.assertEqual(self.client.post('/internal/whatsapp/events', json=foreign, headers=self.auth).status_code, 422)
        self.client.post('/internal/whatsapp/events', json=self.event | {'media_refs':[{'id':media_id}]}, headers=self.auth)
        self.store.run_once(account=self.account, validate=lambda row: validate_media(row, self.root))
        self.assertEqual(self.store.active_report(self.account, 'alice')['state']['media_ids'], [])

    def test_paths_urls_unknown_keys_unauthorized_and_large_body_rejected(self):
        for ref in [{'path':'../secret'}, {'url':'https://example.com/image.jpg'}]:
            r = self.client.post('/internal/whatsapp/events', json=self.event | {'media_refs':[ref]}, headers=self.auth)
            self.assertEqual(r.status_code, 422)
        self.assertEqual(self.client.post('/internal/media', content=b'x').status_code, 401)
        self.assertEqual(self.client.get('/docs').status_code, 401)
        self.assertEqual(self.client.post('/internal/whatsapp/events', json=self.event | {'text':'x'*4001}, headers=self.auth).status_code, 422)
