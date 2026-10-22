import io
import tempfile
import unittest
from pathlib import Path

import httpx
from PIL import Image

from backend.providers import ProviderUnavailable, groq_observe, web_detect
from backend.smoke import VisionBudget


class ProviderTests(unittest.TestCase):
    def setUp(self):
        raw = io.BytesIO()
        Image.new('RGB', (2, 2)).save(raw, 'PNG')
        self.image = raw.getvalue()
        self.folder = tempfile.TemporaryDirectory()
        self.addCleanup(self.folder.cleanup)
        self.budget = VisionBudget(Path(self.folder.name) / 'budget.sqlite3')

    def client(self, handler):
        client = httpx.Client(transport=httpx.MockTransport(handler))
        self.addCleanup(client.close)
        return client

    def test_no_match_is_cached_and_never_means_authentic(self):
        calls = []

        def handle(request):
            calls.append(request)
            return httpx.Response(200, json={'responses': [{}]})

        client = self.client(handle)
        result = web_detect(self.image, client, self.budget, {})
        self.assertEqual(result['outcome'], 'no_match')
        self.assertNotIn('authentic', str(result))
        self.assertEqual(web_detect(self.image, client, self.budget, {}), result)
        self.assertEqual(len(calls), 1)

    def test_retries_are_charged_even_when_all_requests_fail(self):
        calls, waits = [], []

        def handle(request):
            calls.append(request)
            return httpx.Response(429)

        with self.assertRaises(ProviderUnavailable):
            web_detect(self.image, self.client(handle), self.budget, {}, sleep=waits.append)
        self.assertEqual(len(calls), 3)
        self.assertEqual(waits, [2, 5])
        with self.budget.connect() as db:
            self.assertEqual(db.execute('SELECT used FROM budget').fetchone()[0], 3)

    def test_access_error_does_not_retry_or_expose_response(self):
        calls = []

        def handle(request):
            calls.append(request)
            return httpx.Response(403, text='private account detail')

        with self.assertRaisesRegex(ProviderUnavailable, '^HTTP_403$'):
            web_detect(self.image, self.client(handle), self.budget, {})
        self.assertEqual(len(calls), 1)

    def test_malformed_success_is_unavailable_not_no_match(self):
        with self.assertRaises(ProviderUnavailable):
            web_detect(self.image, self.client(lambda _: httpx.Response(200, json={})), self.budget, {})

    def test_web_full_match_and_similar_are_distinct(self):
        result = web_detect(self.image, self.client(lambda _: httpx.Response(200, json={
            'responses': [{'webDetection': {
                'fullMatchingImages': [{'url': 'https://example.org/full.jpg'}],
                'visuallySimilarImages': [{'url': 'https://example.org/similar.jpg'}]}}]})), self.budget, {})
        self.assertEqual(result['outcome'], 'conflict_candidate')
        self.assertEqual(len(result['full_matches']), 1)
        self.assertEqual(len(result['similar_images']), 1)

    def test_groq_invalid_json_does_not_pass_validation(self):
        with self.assertRaises(ProviderUnavailable):
            groq_observe(self.image, self.client(lambda _: httpx.Response(200, json={
                'choices': [{'message': {'content': '{"publish_allowed":true}'}}]})), 'test-key', 'test-model')
