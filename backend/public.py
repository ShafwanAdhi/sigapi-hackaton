"""Versioned public projections and anonymous, location-checked contributions."""
import hashlib
import io
import json
import math
import os
import re
from datetime import datetime, timezone
from pathlib import Path
from uuid import UUID, uuid4
from PIL import Image, ImageOps, UnidentifiedImageError
from fastapi import HTTPException
from pydantic import BaseModel, ConfigDict, Field, ValidationError
from psycopg.types.json import Jsonb
from backend.geospatial import distance_m
from backend.mvp_store import consume_limit


class VerificationInput(BaseModel):
    model_config = ConfigDict(extra='forbid', allow_inf_nan=False)
    request_id: UUID
    choice: str = Field(pattern=r'^(valid|invalid)$')
    latitude: float = Field(ge=-90,le=90)
    longitude: float = Field(ge=-180,le=180)
    accuracy_m: float = Field(gt=0,le=100)
    gps_fix_at: datetime
    location_version: int = Field(ge=1)
    description: str = Field(default='',max_length=2000)
    solved: bool = False


def public_incident(db, slug, *, lock=False):
    if not re.fullmatch(r'[a-f0-9]{32}',slug):
        raise HTTPException(404,'NOT_FOUND')
    row=db.execute('''SELECT i.id,i.location,i.location_version,p.projection,p.photo_key
      FROM incidents i JOIN public_incidents p ON p.incident_id=i.id
      WHERE i.slug=%s AND NOT p.withdrawn AND p.expires_at>now()'''+(' FOR UPDATE OF i,p' if lock else ''),(slug,)).fetchone()
    if not row:
        raise HTTPException(404,'NOT_FOUND')
    return row


def verification_summary(db, incident_id, location_version):
    row=db.execute('''SELECT count(*) FILTER(WHERE choice='valid') valid,
      count(*) FILTER(WHERE choice='invalid') invalid,
      max(created_at) FILTER(WHERE choice='valid' AND solved) solved_at,
      max(created_at) last_at FROM verification_events WHERE incident_id=%s AND location_version=%s''',
      (incident_id,location_version)).fetchone()
    summary='disputed' if row['valid'] and row['invalid'] else 'supporting_valid' if row['valid'] else 'supporting_invalid' if row['invalid'] else 'none'
    return {'summary':summary,'valid_count':row['valid'],'invalid_count':row['invalid'],
            'solved_claim_status':'claimed_solved' if row['solved_at'] else 'none',
            'solved_claimed_at':row['solved_at'],'last_contribution_at':row['last_at'],
            'source':'public_link','limitations':'Jumlah kontribusi bukan jumlah orang independen; bukan konfirmasi resmi.'}


def publish(db, report, incident):
    """Called only after a current normal eligible decision, never fast escalation."""
    category=report['facts'].get('category','unknown')
    label={'forest_land':'hutan/lahan','building':'bangunan'}.get(category,'kejadian')
    projection={'reference':'SIGAPI-'+str(incident['id'])[:8].upper(),
                'title':'Laporan kebakaran '+label,'category':category,
                'location_name':'Kota Malang','location':report['state']['location'],
                'observed_at':report['facts'].get('observed_at'),
                'summary':'Laporan warga yang memenuhi pemeriksaan awal. Belum dikonfirmasi resmi.'}
    db.execute('''INSERT INTO public_incidents(incident_id,location_version,projection) VALUES(%s,%s,%s)
      ON CONFLICT(incident_id) DO UPDATE SET projection=excluded.projection,
      location_version=excluded.location_version,photo_key=CASE WHEN public_incidents.location_version=excluded.location_version
      THEN public_incidents.photo_key ELSE NULL END,withdrawn=false''',
      (incident['id'],incident.get('location_version',1),Jsonb(projection)))


def overview(store,slug):
    with store.connect() as db:
        row=public_incident(db,slug)
        return dict(row['projection'],slug=slug,location_version=row['location_version'],
                    photo_url=('/api/laporan/'+slug+'/photo' if row['photo_key'] else None),
                    verification=verification_summary(db,row['id'],row['location_version']))


def sanitize_photo(raw):
    if len(raw)>10*1024*1024:
        raise HTTPException(413,'PHOTO_TOO_LARGE')
    try:
        with Image.open(io.BytesIO(raw)) as im:
            if im.format not in ('JPEG','PNG','WEBP') or im.width*im.height>25_000_000:
                raise ValueError()
            im.load()
            output=ImageOps.exif_transpose(im).convert('RGB')
            output.thumbnail((1280,1280))
            buf=io.BytesIO();output.save(buf,'JPEG',quality=85)
            return buf.getvalue()
    except (ValueError,OSError,UnidentifiedImageError,Image.DecompressionBombError):
        raise HTTPException(422,'INVALID_PHOTO') from None


def submit(store,root,slug,values,photo,address):
    with store.connect() as db:
        public_incident(db,slug)
    # Commit rejected-attempt counters independently of the event transaction.
    salt=os.environ.get('SIGAPI_RATE_SALT','local-test-rate-salt')
    identity=hashlib.sha256((salt+'|'+address+'|'+slug).encode()).hexdigest()
    with store.connect() as db:
        allowed=consume_limit(db,'public:'+identity,10,600)
    try:
        form=VerificationInput.model_validate(values)
    except ValidationError as exc:
        fields={str(e['loc'][0]) for e in exc.errors() if e['loc']}
        code='INACCURATE_LOCATION' if 'accuracy_m' in fields else 'INVALID_LOCATION' if fields&{'latitude','longitude','gps_fix_at'} else 'INVALID_INPUT'
        raise HTTPException(422,code) from None
    form.solved=form.choice=='valid' and form.solved
    if form.gps_fix_at.tzinfo is None:
        raise HTTPException(422,'INVALID_LOCATION')
    digest=hashlib.sha256(json.dumps(form.model_dump(mode='json'),sort_keys=True).encode()+hashlib.sha256(photo or b'').digest()).hexdigest()
    photo_path=None
    try:
        with store.connect() as db:
            row=public_incident(db,slug,lock=True)
            old=db.execute('SELECT id,payload_hash FROM verification_events WHERE incident_id=%s AND request_id=%s',
                           (row['id'],form.request_id)).fetchone()
            if old:
                if old['payload_hash']!=digest:
                    raise HTTPException(409,'REQUEST_ID_CONFLICT')
                return {'receipt_id':str(old['id']),'replayed':True}
            if not allowed:
                raise HTTPException(429,'RATE_LIMITED')
            if form.location_version!=row['location_version']:
                raise HTTPException(409,'INCIDENT_LOCATION_CHANGED')
            age=(datetime.now(timezone.utc)-form.gps_fix_at).total_seconds()
            if age < -5 or age>60:
                raise HTTPException(422,'STALE_LOCATION')
            loc=row['location'];distance=distance_m(form.latitude,form.longitude,loc['latitude'],loc['longitude'])
            if distance>2000+1e-6:
                raise HTTPException(422,'OUT_OF_RADIUS')
            event_id=uuid4();photo_key=None
            if photo:
                normalized=sanitize_photo(photo)
                photo_key='verification-'+str(event_id)+'.jpg'
                photo_path=Path(root)/photo_key
                with photo_path.open('xb') as out:
                    out.write(normalized)
            db.execute('''INSERT INTO verification_events(id,request_id,incident_id,location_version,
              choice,latitude,longitude,accuracy_m,gps_fix_at,distance_m,description,solved,photo_key,payload_hash)
              VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)''',
              (event_id,form.request_id,row['id'],row['location_version'],form.choice,form.latitude,form.longitude,
               form.accuracy_m,form.gps_fix_at,distance,form.description,form.solved,photo_key,digest))
        return {'receipt_id':str(event_id),'replayed':False}
    except Exception:
        if photo_path:photo_path.unlink(missing_ok=True)
        raise
