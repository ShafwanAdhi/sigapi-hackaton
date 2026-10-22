import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from backend.media import frame_times, sample_media


class MediaTests(unittest.TestCase):
    def test_video_duration_boundaries(self):
        for seconds in [0, -1, 30.01, float('nan'), float('inf')]:
            with self.subTest(seconds=seconds), self.assertRaises(ValueError):
                frame_times(seconds)
        self.assertEqual(frame_times(30), [0, 15, 29.9])
        self.assertEqual(len(frame_times(0.1)), 3)

    def test_video_limit_rejected_before_external_process(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / 'video.mp4'
            with path.open('wb') as file:
                file.truncate(20 * 1024 * 1024 + 1)
            with patch('backend.media.subprocess.run') as run:
                with self.assertRaises(ValueError):
                    sample_media(path)
                run.assert_not_called()

    def test_corrupt_photo_is_not_sent_to_providers(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / 'photo.jpg'
            path.write_bytes(b'corrupt')
            with self.assertRaises(ValueError):
                sample_media(path)
