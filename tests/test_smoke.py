import io
import tempfile
import unittest
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from PIL import Image

from backend.smoke import VisionBudget, decode_photo, parse_observation


class SmokeSafetyTests(unittest.TestCase):
    def test_budget_survives_restart_and_counts_failed_attempts(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / 'budget.sqlite3'
            VisionBudget(path).reserve()
            budget = VisionBudget(path)
            for _ in range(49):
                budget.reserve()
            with self.assertRaisesRegex(ValueError, 'VISION_BUDGET_EXHAUSTED'):
                budget.reserve()

    def test_budget_concurrent_reservations_cannot_exceed_fifty(self):
        with tempfile.TemporaryDirectory() as folder:
            budget = VisionBudget(Path(folder) / 'budget.sqlite3')

            def reserve(_):
                try:
                    budget.reserve()
                    return 1
                except ValueError:
                    return 0

            with ThreadPoolExecutor(max_workers=8) as pool:
                self.assertEqual(sum(pool.map(reserve, range(60))), 50)

    def test_successful_web_result_is_cached_without_spending_again(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / 'budget.sqlite3'
            budget = VisionBudget(path)
            budget.reserve()
            budget.store('abc', {'outcome': 'no_match'})
            self.assertEqual(VisionBudget(path).cached('abc'), {'outcome': 'no_match'})

    def test_photo_decoded_instead_of_trusting_filename(self):
        with self.assertRaises(ValueError):
            decode_photo(b'not a photo')
        raw = io.BytesIO()
        Image.new('RGB', (2, 2)).save(raw, 'PNG')
        self.assertEqual(decode_photo(raw.getvalue()), 'image/png')
        with self.assertRaises(ValueError):
            decode_photo(b'x' * (10 * 1024 * 1024 + 1))

    def test_model_output_must_be_strict_and_cannot_decide_routing(self):
        good = {'fire_visible': False, 'smoke_visible': False,
                'image_quality': 'unclear', 'observations': ['Gambar buram']}
        self.assertEqual(parse_observation(good).image_quality, 'unclear')
        for bad in [dict(good, publish_allowed=True), dict(good, fire_visible='true'),
                    dict(good, image_quality='authentic')]:
            with self.subTest(bad=bad), self.assertRaises(ValueError):
                parse_observation(bad)


if __name__ == '__main__':
    unittest.main()
