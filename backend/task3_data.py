"""Fetch real source data; boundary remains disabled until local operator review."""
import csv
import hashlib
import io
import json
import math
import os
from datetime import datetime,timedelta,timezone
from email.utils import parsedate_to_datetime
from pathlib import Path
import httpx
from backend.geospatial import region_check
from backend.task3_config import ROOT

FIRMS_URL='https://firms.modaps.eosdis.nasa.gov/data/active_fire/viirs/csv/SUOMI_VIIRS_C2_SouthEast_Asia_48h.csv'
REGION_URL='https://nominatim.openstreetmap.org/search'


def save_json(path,value):
    path=Path(path);path.parent.mkdir(parents=True,exist_ok=True)
    temporary=path.with_suffix('.tmp');temporary.write_text(json.dumps(value,ensure_ascii=False,indent=2),encoding='utf-8');temporary.replace(path)


def bootstrap(path=None):
    path=Path(path or ROOT/'.runtime/task3/config.json')
    if path.exists():return path
    claw=json.loads((ROOT/'.runtime/openclaw-state/openclaw.json').read_text(encoding='utf-8'))
    senders=claw['plugins']['entries']['sigapi-validation-demo']['config']['allowSenders']
    save_json(path,{'distribution_enabled':False,'bot_number':os.environ.get('SIGAPI_BOT_NUMBER'),'inbound_senders':senders,
        'region_path':str(path.parent/'kota-malang.geojson'),'approved_region_sha256':None,
        'firms_path':str(path.parent/'firms.json'),'destinations':{}})
    return path


def parse_firms(raw,headers,now):
    stamp=headers.get('last-modified')
    if not stamp:raise ValueError('FIRMS_SOURCE_TIMESTAMP_REQUIRED')
    modified=parsedate_to_datetime(stamp).astimezone(timezone.utc)
    if not timedelta(minutes=-5)<=now-modified<=timedelta(hours=24):raise ValueError('FIRMS_SOURCE_STALE')
    start=modified-timedelta(hours=48);points=[]
    reader=csv.DictReader(io.StringIO(raw.decode('utf-8-sig')))
    if not {'latitude','longitude','acq_date','acq_time'}<=set(reader.fieldnames or []):raise ValueError('FIRMS_COLUMNS_INVALID')
    for row in reader:
        lat,lon=float(row['latitude']),float(row['longitude'])
        acquired=datetime.strptime(row['acq_date']+' '+row['acq_time'].zfill(4),'%Y-%m-%d %H%M').replace(tzinfo=timezone.utc)
        if not math.isfinite(lat) or not -90<=lat<=90 or not math.isfinite(lon) or not -180<=lon<=180:raise ValueError('FIRMS_COORDINATE_INVALID')
        if start<=acquired<=modified:
            points.append({'latitude':lat,'longitude':lon,'acquired_at':acquired.isoformat()})
    # Conservative interior of the South East Asia tile, including Kota Malang.
    return {'source':FIRMS_URL,'sensor':'VIIRS','source_modified_at':modified.isoformat(),
      'fetched_at':now.isoformat(),'coverage_start':start.isoformat(),'coverage_end':modified.isoformat(),
      'bbox':[105,-9,115,5],'points':points,'sha256':hashlib.sha256(raw).hexdigest(),
      'coverage_basis':'NASA regional 48h CSV; source modification time; conservative interior bbox',
      'limitations':'Satellite coverage/detection is imperfect. No match does not disprove fire.'}


def fetch_data(config,kind):
    cfg=config.read()
    with httpx.Client(timeout=60,headers={'User-Agent':'SIGAPI-demo/0.1 local-prototype'},follow_redirects=False) as client:
        if kind=='firms':
            response=client.get(FIRMS_URL);response.raise_for_status()
            result=parse_firms(response.content,response.headers,datetime.now(timezone.utc))
            save_json(cfg['firms_path'],result)
            return {'saved':True,'kind':kind,'source':result['source'],'point_count':len(result['points'])}
        response=client.get(REGION_URL,params={'q':'Kota Malang, Indonesia','format':'geojson','polygon_geojson':1,'limit':1})
        response.raise_for_status();feature=response.json()['features'][0]
        props=feature['properties'];name=props.get('display_name','')
        if not name.startswith('Kota Malang,'):raise ValueError('WRONG_REGION_RESULT')
        feature['properties']={'code':'35.73','name':'Kota Malang','source':'https://www.openstreetmap.org/'+str(props['osm_type'])+'/'+str(props['osm_id']),
           'version':datetime.now(timezone.utc).isoformat(),'attribution':'© OpenStreetMap contributors, ODbL',
           'limitations':'Community boundary candidate; operator review required; not an official administrative certification.'}
        if region_check(feature,-7.98,112.63)!='inside':raise ValueError('REGION_CANDIDATE_INVALID')
        save_json(cfg['region_path'],feature)
        cfg['approved_region_sha256']=None;save_json(config.path,cfg)
        return {'saved':True,'kind':kind,'approval_required':True,
                'sha256':hashlib.sha256(Path(cfg['region_path']).read_bytes()).hexdigest(),'source':feature['properties']['source']}


def approve_region(config,expected,reason):
    from backend.operator import reason_required
    reason_required(reason);cfg=config.read();raw=Path(cfg['region_path']).read_bytes()
    digest=hashlib.sha256(raw).hexdigest()
    if digest!=expected or region_check(json.loads(raw),-7.98,112.63)!='inside':raise ValueError('REGION_REVIEW_HASH_MISMATCH')
    cfg.update(approved_region_sha256=digest,region_review={'reason':reason,'at':datetime.now(timezone.utc).isoformat()})
    save_json(config.path,cfg)


def status(store,config):
    from backend.geospatial import firms_check
    now=datetime.now(timezone.utc)
    result={'distribution_enabled':bool(config.destinations()),'region_approved':bool(config.region()),
       'firms':firms_check(config.snapshot(),-7.98,112.63,now,now)['outcome'],
       'live_whatsapp_gate':'pending; requires distinct configured test destinations and observed receipts'}
    with store.connect() as db:
        for name in ('analysis_jobs','outbox'):result[name]=db.execute(f'SELECT state,count(*) n FROM {name} GROUP BY state').fetchall()
    return result
