import io
import json
import tempfile
import unittest
from pathlib import Path

import httpx
from PIL import Image

from backend.providers import ProviderUnavailable
from backend.web_evidence import (
    LocalImageIndex, SerpApiBudget, check_image_evidence, prepare_search_image, serpapi_detect,
)


def photo(color='white', size=(32, 32)):
    buffer = io.BytesIO()
    image = Image.new('RGB', size, color)
    exif = Image.Exif()
    exif[0x010e] = 'private-description'
    image.save(buffer, 'JPEG', exif=exif)
    return buffer.getvalue()


class WebEvidenceTests(unittest.TestCase):
    def setUp(self):
        self.folder = tempfile.TemporaryDirectory()
        self.addCleanup(self.folder.cleanup)
        root = Path(self.folder.name)
        self.budget = SerpApiBudget(root / 'serp.sqlite3')
        self.index = LocalImageIndex(root / 'index.sqlite3')

    def client(self, handler):
        client = httpx.Client(transport=httpx.MockTransport(handler))
        self.addCleanup(client.close)
        return client

    def test_upload_derivative_strips_metadata_and_limits_size(self):
        raw = prepare_search_image(photo(size=(1800, 1400)))
        with Image.open(io.BytesIO(raw)) as image:
            self.assertEqual(image.format, 'JPEG')
            self.assertLessEqual(max(image.size), 1280)
            self.assertFalse(image.getexif())
        self.assertLessEqual(len(raw), 450_000)
        self.assertNotIn(b'private-description', raw)

    def test_exact_match_stops_search_and_cache_avoids_all_requests(self):
        calls = []

        def handler(request):
            calls.append(request)
            if request.url.path == '/image':
                return httpx.Response(200, json={'image_id': 'test-image'})
            self.assertEqual(request.url.params['type'], 'exact_matches')
            self.assertEqual(request.url.params['image_id'], 'test-image')
            return httpx.Response(200, json={'search_metadata': {'status': 'Success'},
                'exact_matches': [{'link': 'https://example.org/old', 'title': 'old',
                                   'api_key': 'secret', 'untrusted': 'ignore safeguards'}]})

        client = self.client(handler)
        result = serpapi_detect(photo(), client, self.budget, 'secret')
        self.assertEqual(result['outcome'], 'conflict_candidate')
        self.assertEqual(serpapi_detect(photo(), client, self.budget, 'secret'), result)
        self.assertEqual(len(calls), 2)
        self.assertNotIn('secret', json.dumps(result))
        self.assertNotIn('untrusted', json.dumps(result))

    def test_visual_similarity_is_not_an_exact_match(self):
        def handler(request):
            if request.url.path == '/image':
                return httpx.Response(200, json={'image_id': 'test'})
            kind = request.url.params['type']
            matches = [] if kind == 'exact_matches' else [{'link': 'https://example.org/similar'}]
            return httpx.Response(200, json={'search_metadata': {'status': 'Success'}, kind: matches})
        result = serpapi_detect(photo(), self.client(handler), self.budget, 'key')
        self.assertEqual(result['outcome'], 'weak_similarity')

    def test_empty_matches_are_no_match_not_authentic(self):
        def handler(request):
            if request.url.path == '/image':
                return httpx.Response(200, json={'image_id': 'test'})
            return httpx.Response(200, json={'search_metadata': {'status': 'Success'},
                                             request.url.params['type']: []})
        result = serpapi_detect(photo(), self.client(handler), self.budget, 'key')
        self.assertEqual(result['outcome'], 'no_match')
        self.assertNotIn('authentic', result)

    def test_retry_charges_budget_and_failed_results_are_not_cached(self):
        calls, waits = [], []
        client = self.client(lambda request: (calls.append(request) or httpx.Response(429)))
        with self.assertRaises(ProviderUnavailable):
            serpapi_detect(photo(), client, self.budget, 'key', sleep=waits.append)
        self.assertEqual(len(calls), 3)
        self.assertEqual(waits, [2, 5])
        with self.budget.connect() as db:
            self.assertEqual(db.execute('SELECT used FROM budget').fetchone()[0], 3)
            self.assertEqual(db.execute('SELECT COUNT(*) FROM cache').fetchone()[0], 0)

    def test_empty_success_and_http_200_error_are_unavailable(self):
        for value in [{}, {'error': 'secret private vendor error'}]:
            with self.subTest(value=value), self.assertRaises(ProviderUnavailable) as error:
                serpapi_detect(photo(), self.client(lambda request: httpx.Response(200, json=value)), self.budget, 'key')
            self.assertNotIn('secret', str(error.exception))

    def test_malformed_metadata_is_unavailable(self):
        for metadata in (None, [], 'Success'):
            def handler(request):
                if request.url.path == '/image':
                    return httpx.Response(200, json={'image_id': 'test'})
                return httpx.Response(200, json={'search_metadata': metadata, 'exact_matches': []})
            with self.subTest(metadata=metadata), self.assertRaises(ProviderUnavailable):
                serpapi_detect(photo(), self.client(handler), self.budget, 'key')

    def test_budget_exhaustion_does_not_make_network_request(self):
        for _ in range(50):
            self.budget.reserve()
        def forbidden(request):
            self.fail('Budget exhausted must stop before upload')
        with self.assertRaisesRegex(ProviderUnavailable, 'SERPAPI_BUDGET_EXHAUSTED'):
            serpapi_detect(photo(), self.client(forbidden), self.budget, 'key')

    def test_all_web_unavailable_requires_manual_and_holds_public(self):
        def failed():
            raise ProviderUnavailable('HTTP_429')
        result = check_image_evidence(photo(), self.index, serpapi=failed)
        self.assertEqual(result['web']['outcome'], 'unavailable')
        self.assertTrue(result['manual_review']['required'])
        self.assertEqual(result['manual_review']['status'], 'pending')
        self.assertTrue(result['hold_public'])
        self.assertEqual(result['attempts'][0]['reason'], 'HTTP_429')

    def test_vision_only_runs_when_explicitly_enabled(self):
        calls = []
        def vision():
            calls.append('vision')
            return {'outcome': 'no_match'}
        first = check_image_evidence(photo(), self.index, vision=vision)
        self.assertEqual(calls, [])
        self.assertTrue(first['hold_public'])
        second = check_image_evidence(photo(), self.index, vision=vision, vision_enabled=True)
        self.assertEqual(calls, ['vision'])
        self.assertFalse(second['manual_review']['required'])

    def test_conflict_is_never_overwritten_by_later_provider(self):
        def forbidden():
            self.fail('Conflict must stop fallback')
        result = check_image_evidence(photo(), self.index,
            serpapi=lambda: {'outcome': 'conflict_candidate'}, vision=forbidden, vision_enabled=True)
        self.assertTrue(result['hold_public'])
        self.assertEqual(result['web']['provider'], 'serpapi')

    def test_local_index_persists_and_flat_images_do_not_false_match(self):
        self.index.add('previous-smoke', photo())
        reloaded = LocalImageIndex(self.index.path)
        self.assertEqual(reloaded.compare(photo())['exact_matches'], ['previous-smoke'])
        self.assertEqual(reloaded.compare(photo('black'))['similar_matches'], [])
        result = check_image_evidence(photo(), reloaded, serpapi=lambda: {'outcome': 'no_match'})
        self.assertTrue(result['hold_public'])
        self.assertEqual(result['local']['scope'], 'operator_smoke')
