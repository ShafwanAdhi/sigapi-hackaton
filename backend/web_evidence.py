"""Fallback between web services; local similarity never substitutes for web coverage."""

from backend.image_index import LocalImageIndex
from backend.providers import ProviderUnavailable
from backend.serpapi import SerpApiBudget, prepare_search_image, serpapi_detect


def check_image_evidence(data, local_index, *, serpapi=None, vision=None, vision_enabled=False):
    local = local_index.compare(data)
    attempts = []
    web = {'outcome': 'unavailable', 'provider': None}
    for name, provider in [('serpapi', serpapi), ('google_vision', vision if vision_enabled else None)]:
        if provider is None:
            attempts.append({'provider': name, 'outcome': 'unavailable',
                             'reason': 'DISABLED' if name == 'google_vision' and not vision_enabled else 'NOT_CONFIGURED'})
            continue
        try:
            evidence = provider()
            if not isinstance(evidence, dict) or evidence.get('outcome') not in ('no_match', 'weak_similarity', 'conflict_candidate'):
                raise ProviderUnavailable('INVALID_EVIDENCE_OUTCOME')
            web = dict(evidence, provider=name)
            attempts.append({'provider': name, 'outcome': web['outcome']})
            break  # Fallback only on failure, never to override a conflict.
        except ProviderUnavailable as exc:
            attempts.append({'provider': name, 'outcome': 'unavailable', 'reason': str(exc)})
    manual_required = web['outcome'] == 'unavailable'
    return {'local': local, 'web': web, 'attempts': attempts,
            'hold_public': manual_required or web['outcome'] == 'conflict_candidate'
                           or local['outcome'] == 'duplicate_candidate',
            'manual_review': {'required': manual_required,
                              'status': 'pending' if manual_required else 'not_requested',
                              'tools': ['Google Lens browser', 'TinEye browser'] if manual_required else []},
            'limitations': 'Smoke evidence only; hold_public=false is not publication authorization.'}
