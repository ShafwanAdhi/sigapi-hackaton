"""Small operator-smoke collection, separate from future citizen reports."""

import hashlib
import io
from datetime import datetime, timezone

from PIL import Image, ImageOps

from backend.smoke import VisionBudget, decode_photo


def fingerprints(data):
    decode_photo(data)
    with Image.open(io.BytesIO(data)) as original:
        image = ImageOps.exif_transpose(original).convert('L').resize((9, 8), Image.Resampling.LANCZOS)
        low, high = image.getextrema()
        # Flat/low contrast photos share trivial hashes; don't suggest similarity.
        if high - low < 32:
            return hashlib.sha256(data).hexdigest(), None
        pixels = list(image.getdata())
        bits = 0
        for y in range(8):
            for x in range(8):
                bits = (bits << 1) | (pixels[y * 9 + x] > pixels[y * 9 + x + 1])
    return hashlib.sha256(data).hexdigest(), f'{bits:016x}'


class LocalImageIndex:
    def __init__(self, path):
        self.path = path
        self.database = VisionBudget(path)
        with self.database.connect() as db:
            db.execute('''CREATE TABLE IF NOT EXISTS image_index(
                reference TEXT PRIMARY KEY, sha TEXT NOT NULL, dhash TEXT, added_at TEXT NOT NULL)''')

    def add(self, reference, data):
        if not isinstance(reference, str) or not 1 <= len(reference) <= 200:
            raise ValueError('INVALID_IMAGE_REFERENCE')
        sha, dhash = fingerprints(data)
        with self.database.connect() as db:
            db.execute('INSERT OR IGNORE INTO image_index VALUES(?, ?, ?, ?)',
                       (reference, sha, dhash, datetime.now(timezone.utc).isoformat()))

    def compare(self, data):
        sha, dhash = fingerprints(data)
        exact, similar = [], []
        with self.database.connect() as db:
            rows = db.execute('SELECT reference, sha, dhash FROM image_index').fetchall()
        for reference, previous_sha, previous_hash in rows:
            if sha == previous_sha:
                exact.append(reference)
            elif dhash and previous_hash:
                distance = (int(dhash, 16) ^ int(previous_hash, 16)).bit_count()
                if distance <= 5:
                    similar.append({'reference': reference, 'hamming_distance': distance})
        return {'scope': 'operator_smoke', 'check_version': 'sha256-dhash-v1',
                'checked_at': datetime.now(timezone.utc).isoformat(), 'sha256': sha,
                'outcome': 'duplicate_candidate' if exact or similar else 'no_local_match',
                'exact_matches': exact, 'similar_matches': similar}
