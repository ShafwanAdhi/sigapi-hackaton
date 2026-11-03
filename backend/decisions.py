"""Deterministic demo policy; eligibility is not authenticity or official verification."""

def decide(*,complete,region,risk,category,time_valid,frames,web,firms,grouping,local_conflict=False,consistency=None):
    reasons=[]
    if not complete:reasons.append('INCOMPLETE')
    if region!='inside':reasons.append('REGION_'+region.upper())
    if not time_valid:reasons.append('TIME_NEEDS_CLARIFICATION')
    if category not in ('forest_land','building'):reasons.append('CATEGORY_UNKNOWN')
    if not frames or any(f.get('image_quality')!='clear' or not (f.get('fire_visible') or f.get('smoke_visible')) for f in frames):
        reasons.append('MEDIA_UNCLEAR_OR_CONTRADICTORY')
    if not web or len(web)!=len(frames) or any(w not in ('no_match','weak_similarity','reviewed_conflict') for w in web):reasons.append('WEB_CONFLICT_OR_UNAVAILABLE')
    if local_conflict:reasons.append('LOCAL_REUSE_NEEDS_REVIEW')
    if firms not in ('matched','no_match'):reasons.append('FIRMS_UNAVAILABLE')
    if not grouping:reasons.append('INCIDENT_REVIEW_PENDING')
    if consistency is not None and consistency!='supported':reasons.append('CONSISTENCY_'+consistency.upper())
    return {'action':'held' if reasons else 'eligible','reasons':reasons,
            'escalate':bool(complete and region=='inside' and risk=='high'),
            'destinations':[] if reasons else ['authority']+(['community'] if category=='forest_land' else []),
            'policy_version':'demo-policy-v1'}
