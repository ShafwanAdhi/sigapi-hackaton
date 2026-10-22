"""Decode local operator media before provider calls; never download arbitrary URLs."""

import json
import math
import shutil
import subprocess
from pathlib import Path

from backend.smoke import decode_photo


def frame_times(duration):
    if not math.isfinite(duration) or not 0 < duration <= 30:
        raise ValueError('VIDEO_DURATION_LIMIT_30_SECONDS')
    return [0, duration / 2, max(0, duration - 0.1)]


def sample_media(path: Path):
    size = path.stat().st_size
    if size > 20 * 1024 * 1024:
        raise ValueError('VIDEO_SIZE_LIMIT_20_MB')
    if path.suffix.lower() in {'.jpg', '.jpeg', '.png', '.webp'}:
        data = path.read_bytes()
        decode_photo(data)
        return [data]
    if path.suffix.lower() not in {'.mp4', '.mov', '.webm'}:
        raise ValueError('UNSUPPORTED_MEDIA')
    if not shutil.which('ffprobe') or not shutil.which('ffmpeg'):
        raise ValueError('FFMPEG_AND_FFPROBE_REQUIRED')
    try:
        probe = subprocess.run(['ffprobe', '-v', 'error', '-show_entries', 'format=duration',
                                '-of', 'json', str(path.resolve())],
                               capture_output=True, timeout=15, check=True)
        timestamps = frame_times(float(json.loads(probe.stdout)['format']['duration']))
        frames = []
        for timestamp in timestamps:
            result = subprocess.run(['ffmpeg', '-nostdin', '-v', 'error', '-ss', str(timestamp),
                '-i', str(path.resolve()), '-map', '0:v:0', '-frames:v', '1',
                '-vf', 'scale=1280:1280:force_original_aspect_ratio=decrease',
                '-f', 'image2pipe', '-c:v', 'mjpeg', 'pipe:1'],
                capture_output=True, timeout=30, check=True)
            decode_photo(result.stdout)
            frames.append(result.stdout)
        return frames
    except (subprocess.SubprocessError, ValueError, KeyError, TypeError):
        raise ValueError('INVALID_VIDEO_OR_DURATION') from None
