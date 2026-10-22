"""Task 1 only: provider smoke checks, never publication decisions."""

import io
import json
import sqlite3
from contextlib import contextmanager
from pathlib import Path

from PIL import Image, UnidentifiedImageError
from pydantic import BaseModel, ConfigDict, Field
from typing import Literal


class Observation(BaseModel):
    model_config = ConfigDict(extra='forbid', strict=True)
    fire_visible: bool
    smoke_visible: bool
    image_quality: Literal['clear', 'unclear']
    observations: list[str] = Field(min_length=1, max_length=10)


def parse_observation(value):
    return Observation.model_validate(value)


def decode_photo(data: bytes) -> str:
    if not data or len(data) > 10 * 1024 * 1024:
        raise ValueError('PHOTO_SIZE_LIMIT')
    try:
        with Image.open(io.BytesIO(data)) as image:
            if image.format not in {'JPEG', 'PNG', 'WEBP'} or image.width * image.height > 25_000_000:
                raise ValueError('UNSUPPORTED_PHOTO')
            mime = Image.MIME[image.format]
            image.verify()
        with Image.open(io.BytesIO(data)) as image:
            image.load()
        return mime
    except (OSError, UnidentifiedImageError, Image.DecompressionBombError) as exc:
        raise ValueError('INVALID_PHOTO') from exc


class VisionBudget:
    # ponytail: SQLite untuk gerbang smoke satu mesin; intake memakai PostgreSQL pada Task 2.
    def __init__(self, path: Path):
        self.path = path
        path.parent.mkdir(parents=True, exist_ok=True)
        with self.connect() as db:
            db.executescript('''
                CREATE TABLE IF NOT EXISTS budget(id INTEGER PRIMARY KEY CHECK(id=1), used INTEGER NOT NULL);
                INSERT OR IGNORE INTO budget VALUES(1, 0);
                CREATE TABLE IF NOT EXISTS cache(key TEXT PRIMARY KEY, result TEXT NOT NULL);
            ''')

    @contextmanager
    def connect(self):
        db = sqlite3.connect(self.path, timeout=30)
        try:
            with db:
                yield db
        finally:
            db.close()

    def reserve(self):
        with self.connect() as db:
            if db.execute('UPDATE budget SET used=used+1 WHERE id=1 AND used<50').rowcount != 1:
                raise ValueError('VISION_BUDGET_EXHAUSTED')

    def cached(self, key):
        with self.connect() as db:
            row = db.execute('SELECT result FROM cache WHERE key=?', (key,)).fetchone()
        return json.loads(row[0]) if row else None

    def store(self, key, result):
        with self.connect() as db:
            db.execute('INSERT OR REPLACE INTO cache VALUES(?, ?)', (key, json.dumps(result)))
