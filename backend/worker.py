"""Persistent jobs are claimed from PostgreSQL; no in-memory background tasks."""

import time
from pathlib import Path
from PIL import Image

from backend.media import sample_media


def validate_media(row, root):
    root = Path(root).resolve()
    path = (root / row['storage_key']).resolve()
    if path.parent != root or not path.is_file():
        return False
    try:
        sample_media(path)
        if row['kind'] == 'image':
            with Image.open(path) as image:
                return {'JPEG': 'image/jpeg', 'PNG': 'image/png', 'WEBP': 'image/webp'}.get(image.format, False)
        with path.open('rb') as file:
            header = file.read(32)
        if header[4:8] == b'ftyp':
            return 'video/quicktime' if header[8:12] == b'qt  ' else 'video/mp4'
        if header[:4] == b'\x1aE\xdf\xa3':
            return 'video/webm'
        return False
    except (ValueError, OSError):
        return False


def run_worker(store, root, *, once=False):
    while True:
        try:
            if hasattr(store,'beat'):store.beat('intake')
            worked = store.run_once(validate=lambda row: validate_media(row, root))
        except Exception:
            print('Worker job gagal; detail input/credential tidak dicetak. Periksa jobs.reason lokal.', flush=True)
            worked = False
        if once:
            return
        if not worked:
            time.sleep(1)
