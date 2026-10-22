import unittest
from fastapi.testclient import TestClient

from backend.internal import create_app


class InternalSmokeTests(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(create_app('x' * 32))
        self.headers = {'Authorization': 'Bearer ' + 'x' * 32}
        self.event = dict(account_id='demo', provider_message_id='m1', sender_ref='sender1',
                          conversation_id='chat1', received_at='2026-10-22T14:00:00Z', text='uji')

    def test_token_required_and_no_public_docs(self):
        self.assertEqual(self.client.post('/internal/whatsapp/events', json=self.event).status_code, 401)
        self.assertEqual(self.client.get('/docs').status_code, 404)

    def test_smoke_reply_labels_test_without_echoing_private_text(self):
        self.event['text'] = 'nomor pribadi 08123456789'
        self.event['location'] = {'latitude': -1.0, 'longitude': 110.0}
        result = self.client.post('/internal/whatsapp/events', json=self.event, headers=self.headers)
        self.assertEqual(result.status_code, 200)
        self.assertIn('UJI', result.json()['reply_text'])
        self.assertNotIn('08123456789', result.text)
        self.assertTrue(result.json()['received']['location'])

    def test_invalid_coordinates_and_text_limit_rejected(self):
        for change in [{'location': {'latitude': 91, 'longitude': 110}}, {'text': 'a' * 4001}]:
            with self.subTest(change=change):
                result = self.client.post('/internal/whatsapp/events', json=self.event | change, headers=self.headers)
                self.assertEqual(result.status_code, 422)
                self.assertNotIn('sender1', result.text)

    def test_self_message_does_not_produce_reply(self):
        result = self.client.post('/internal/whatsapp/events', json=self.event | {'from_me': True}, headers=self.headers)
        self.assertIsNone(result.json()['reply_text'])

    def test_empty_service_token_fails_closed(self):
        with self.assertRaises(ValueError):
            create_app('')
