"""Versioned pilot polygon and provenance-aware FIRMS snapshots."""
import math
from datetime import datetime, timedelta, timezone
from shapely.geometry import shape, Point
from shapely.errors import GEOSException


def utc(value):
    d=datetime.fromisoformat(value.replace('Z','+00:00')) if isinstance(value,str) else value
    if d.tzinfo is None:raise ValueError('NAIVE_TIME')
    return d.astimezone(timezone.utc)


def distance_m(lat1,lon1,lat2,lon2):
    p1,p2=map(math.radians,(lat1,lat2));a=math.sin((p2-p1)/2)**2+math.cos(p1)*math.cos(p2)*math.sin(math.radians(lon2-lon1)/2)**2
    return 6371008.8*2*math.asin(math.sqrt(min(1,max(0,a))))


def region_check(feature,latitude,longitude):
    try:
        if feature['properties']['code']!='35.73' or not feature['properties'].get('source') or not feature['properties'].get('version'):return 'unavailable'
        geometry=shape(feature['geometry'])
        if not geometry.is_valid or geometry.is_empty or geometry.geom_type not in ('Polygon','MultiPolygon'):return 'unavailable'
        p=Point(longitude,latitude)
        if geometry.boundary.distance(p)<1e-8:return 'boundary'
        return 'inside' if geometry.contains(p) else 'outside'
    except (KeyError,ValueError,TypeError,AttributeError,GEOSException):return 'unavailable'


def firms_check(snapshot,latitude,longitude,observed_at,now=None):
    unavailable={'outcome':'unavailable','reason':'MISSING_OR_INVALID_SNAPSHOT','check_version':'firms-snapshot-v1'}
    try:
        now=utc(now or datetime.now(timezone.utc));observed_at=utc(observed_at)
        fetched=utc(snapshot['fetched_at']);start=utc(snapshot['coverage_start']);end=utc(snapshot['coverage_end'])
        bbox=snapshot['bbox']
        if not snapshot['source'].startswith('https://firms.modaps.eosdis.nasa.gov/') or not snapshot['sensor']:return unavailable
        if fetched>now+timedelta(minutes=5) or now-fetched>timedelta(hours=24):return unavailable | {'reason':'STALE_SNAPSHOT'}
        if not (bbox[0]<=longitude<=bbox[2] and bbox[1]<=latitude<=bbox[3]):return unavailable | {'reason':'AREA_NOT_COVERED'}
        search_start=observed_at-timedelta(hours=24)
        # The rolling feed ends at its source modification, not at HTTP download.
        # Future observations cannot exist yet; an event newer than the source must wait.
        if (observed_at>now+timedelta(minutes=5) or start>search_start or end<observed_at
            or end>fetched+timedelta(minutes=5) or fetched-end>timedelta(hours=24)):
            return unavailable | {'reason':'TIME_NOT_COVERED'}
        matches=[]
        for row in snapshot['points']:
            acquired=utc(row['acquired_at']);lat=float(row['latitude']);lon=float(row['longitude'])
            if not math.isfinite(lat) or not -90<=lat<=90 or not math.isfinite(lon) or not -180<=lon<=180:return unavailable
            if not start<=acquired<=end:return unavailable
            dist=distance_m(latitude,longitude,lat,lon)
            if abs((acquired-observed_at).total_seconds())<=86400 and dist<=3000:
                matches.append({'latitude':lat,'longitude':lon,'acquired_at':acquired.isoformat(),'distance_m':round(dist)})
        return {'outcome':'matched' if matches else 'no_match','matches':matches,
                'source':snapshot['source'],'sensor':snapshot['sensor'],'fetched_at':snapshot['fetched_at'],
                'coverage_start':snapshot['coverage_start'],'coverage_end':snapshot['coverage_end'],
                'check_version':'firms-snapshot-v1','limitations':'Only source coverage through coverage_end is checked within +/-24h; future observations unavailable. Hotspot is supporting evidence, not proof.'}
    except (KeyError,TypeError,ValueError,IndexError,OverflowError):return unavailable
