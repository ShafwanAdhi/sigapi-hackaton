import io
import json
import os
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from backend import cli
from backend.providers import ProviderUnavailable
from tests.test_web_evidence import photo


class CliFallbackTests(unittest.TestCase):
    def run_smoke(self, provider='both', env=None, groq_failure=False, frame_count=1):
        with tempfile.TemporaryDirectory() as folder:
            with patch.object(cli, 'RUNTIME', Path(folder)), patch.dict(os.environ, env or {}, clear=True), \
                 patch('backend.media.sample_media', return_value=[photo()] * frame_count), \
                 patch.object(cli, 'groq_observe', side_effect=ProviderUnavailable('HTTP_429') if groq_failure else None,
                              return_value={'fire_visible': False}), \
                 patch.object(cli, 'web_detect') as vision, redirect_stdout(io.StringIO()):
                status = cli.provider_smoke(SimpleNamespace(image='unused.jpg', case='no_fire', provider=provider))
                files = list(Path(folder).glob('smoke-*.json'))
                self.assertEqual(len(files), 1)
                result = json.loads(files[0].read_text(encoding='utf-8'))
                vision.assert_not_called()
                return status, result['frames'][0]

    def test_default_missing_web_config_preserves_manual_pending_evidence(self):
        status, frame = self.run_smoke()
        self.assertEqual(status, 1)
        self.assertIn('groq', frame)
        self.assertTrue(frame['evidence']['hold_public'])
        self.assertEqual(frame['evidence']['manual_review']['status'], 'pending')

    def test_groq_failure_does_not_discard_web_evidence(self):
        status, frame = self.run_smoke(groq_failure=True)
        self.assertEqual(status, 1)
        self.assertEqual(frame['groq']['outcome'], 'unavailable')
        self.assertIn('evidence', frame)

    def test_explicit_vision_still_requires_opt_in(self):
        status, frame = self.run_smoke(provider='vision')
        self.assertEqual(status, 1)
        self.assertEqual(frame['evidence']['attempts'][-1]['reason'], 'DISABLED')

    def test_video_groq_frames_are_spaced_for_free_plan(self):
        with patch('time.sleep') as sleep:
            status, _ = self.run_smoke(provider='groq', frame_count=3)
        self.assertEqual(status, 0)
        self.assertEqual([call.args[0] for call in sleep.call_args_list], [35, 35])

    def test_primary_success_does_not_call_google_even_if_enabled(self):
        with patch.object(cli, 'serpapi_detect', return_value={'outcome': 'no_match'}) as search:
            status, frame = self.run_smoke(env={'SERPAPI_API_KEY': 'test', 'ENABLE_GOOGLE_VISION': 'true'})
        self.assertEqual(status, 0)
        search.assert_called_once()
        self.assertEqual(frame['evidence']['web']['provider'], 'serpapi')

    def test_unavailable_primary_uses_enabled_backup(self):
        with patch.object(cli, 'serpapi_detect', side_effect=ProviderUnavailable('HTTP_429')), \
             patch.object(cli, 'vision_check', return_value={'outcome': 'conflict_candidate'}) as backup:
            status, frame = self.run_smoke(env={'SERPAPI_API_KEY': 'test', 'ENABLE_GOOGLE_VISION': 'true'})
        backup.assert_called_once()
        self.assertEqual(status, 0)  # completed check can still discover a conflict
        self.assertTrue(frame['evidence']['hold_public'])
        self.assertEqual(frame['evidence']['web']['provider'], 'google_vision')
