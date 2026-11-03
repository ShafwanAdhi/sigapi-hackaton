"""Lens search through SerpApi; never publish media at a public URL."""

import hashlib
import io
import time
from datetime import datetime, timezone
from urllib.parse import urlsplit

import httpx
from PIL import Image, ImageOps

from backend.providers import ProviderUnavailable
from backend.smoke import VisionBudget, decode_photo


class SerpApiBudget(VisionBudget):
    # Separate database; conservative 50 HTTP operations including uploads/retries.
    def reserve(self):
        try:
            super().reserve()
        except ValueError:
            raise ProviderUnavailable('SERPAPI_BUDGET_EXHAUSTED') from None


def prepare_search_image(data):
    decode_photo(data)
    with Image.open(io.BytesIO(data)) as original:
        oriented = ImageOps.exif_transpose(original).convert('RGB')
        clean = Image.new('RGB', oriented.size, 'white')
        clean.paste(oriented)
    clean.thumbnail((1280, 1280))
    for quality in (85, 70, 50, 30):
        buffer = io.BytesIO()
        clean.save(buffer, 'JPEG', quality=quality)
        if buffer.tell() <= 450_000:
            return buffer.getvalue()
    raise ProviderUnavailable('SEARCH_DERIVATIVE_TOO_LARGE')


def _request(client, budget, method, url, *, sleep, **kwargs):
    for attempt in range(3):
        budget.reserve()
        try:
            response = client.request(method, url, timeout=30, **kwargs)
        except httpx.TimeoutException:
            reason, retry = 'TIMEOUT', True
        except httpx.RequestError:
            raise ProviderUnavailable('NETWORK_UNAVAILABLE') from None
        else:
            if response.is_success:
                try:
                    value = response.json()
                    if not isinstance(value, dict) or 'error' in value:
                        raise ValueError()
                    return value
                except ValueError:
                    raise ProviderUnavailable('INVALID_SERPAPI_RESULT') from None
            reason = f'HTTP_{response.status_code}'
            retry = response.status_code == 429 or 500 <= response.status_code < 600
        if not retry or attempt == 2:
            raise ProviderUnavailable(reason)
        sleep((2, 5)[attempt])


def _matches(value, kind):
    metadata = value.get('search_metadata')
    if not isinstance(metadata, dict) or metadata.get('status') != 'Success' or not isinstance(value.get(kind), list):
        raise ProviderUnavailable('INVALID_SERPAPI_RESULT')
    matches = []
    for item in value[kind][:100]:
        if not isinstance(item, dict) or not isinstance(item.get('link'), str):
            raise ProviderUnavailable('INVALID_SERPAPI_REFERENCE')
        try:
            url = urlsplit(item['link'])
            if url.scheme not in ('http', 'https') or not url.hostname or url.username or url.password:
                raise ValueError()
        except ValueError:
            raise ProviderUnavailable('INVALID_SERPAPI_REFERENCE') from None
        match = {'url': item['link'][:4000]}
        for name in ('title', 'source'):
            if name in item:
                if not isinstance(item[name], str):
                    raise ProviderUnavailable('INVALID_SERPAPI_REFERENCE')
                match[name] = item[name][:2000]
        matches.append(match)
    return matches


def serpapi_detect(data, client, budget, key, *, sleep=time.sleep):
    decode_photo(data)
    if not key:
        raise ProviderUnavailable('SERPAPI_NOT_CONFIGURED')
    sha = hashlib.sha256(data).hexdigest()
    cache_key = 'serpapi-lens-v1:' + sha
    cached = budget.cached(cache_key)
    if cached is not None:
        return cached
    derivative = prepare_search_image(data)
    upload = _request(client, budget, 'POST', 'https://serpapi.com/image', sleep=sleep,
        data={'api_key': key}, files={'image': ('image.jpg', derivative, 'image/jpeg')})
    image_id = upload.get('image_id')
    if not isinstance(image_id, str) or not 1 <= len(image_id) <= 1000:
        raise ProviderUnavailable('INVALID_SERPAPI_UPLOAD')
    params = {'engine': 'google_lens', 'image_id': image_id, 'api_key': key, 'hl': 'id', 'type': 'exact_matches'}
    exact = _matches(_request(client, budget, 'GET', 'https://serpapi.com/search.json',
                             sleep=sleep, params=params), 'exact_matches')
    similar = []
    if not exact:
        params['type'] = 'visual_matches'
        similar = _matches(_request(client, budget, 'GET', 'https://serpapi.com/search.json',
                                   sleep=sleep, params=params), 'visual_matches')
    result = {
        'provider': 'serpapi', 'check_version': 'serpapi-lens-v1',
        'checked_at': datetime.now(timezone.utc).isoformat(), 'sha256': sha,
        'derivative_sha256': hashlib.sha256(derivative).hexdigest(),
        'outcome': 'conflict_candidate' if exact else 'weak_similarity' if similar else 'no_match',
        'exact_matches': exact, 'similar_images': similar,
    }
    budget.store(cache_key, result)
    return result
