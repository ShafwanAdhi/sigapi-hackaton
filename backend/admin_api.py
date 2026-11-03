"""Region-scoped operational endpoints. Mutations reuse backend workflows."""
import io
import re
from pathlib import Path
from uuid import UUID,uuid4
from datetime import datetime
from fastapi import APIRouter,HTTPException,Request,Query
from fastapi.responses import FileResponse
from pydantic import BaseModel,ConfigDict,Field
from backend.facts import redact
from backend.public import verification_summary,sanitize_photo
from backend.operator import requeue,review_evidence,group_incident,reconcile


class Action(BaseModel):
    model_config=ConfigDict(extra='forbid')
    action:str=Field(pattern=r'^(recheck|review_evidence|group|publish_photo|withdraw_public|reconcile)$')
    expected_revision:int=Field(ge=1)
    reason:str=Field(min_length=10,max_length=1000)
    evidence_key:str|None=Field(default=None,max_length=300)
    references:list[str]=Field(default_factory=list,max_length=10)
    target_id:UUID|None=None
    media_id:UUID|None=None
    outbox_id:UUID|None=None
    receipt:str|None=Field(default=None,max_length=300)
    retry:bool=False


def scoped_report(db,report_id,user,*,lock=False):
    row=db.execute('SELECT * FROM reports WHERE id=%s AND region_code=%s'+(' FOR UPDATE' if lock else ''),
                   (report_id,user['region_code'])).fetchone()
    if not row:raise HTTPException(404,'NOT_FOUND')
    return row


def report_card(row):
    result={k:row[k] for k in ('id','status','created_at','region_code','revision','incident_id','lifecycle')}
    result['location']=row['state'].get('location')
    result['category']=row['facts'].get('category','unknown')
    result['risk']=row['facts'].get('risk',{}).get('level','unknown')
    result['decision']=(row['analysis'] or {}).get('decision',{})
    return result


def install_admin_routes(app,store,root):
    router=APIRouter(prefix='/api/admin')

    @router.get('/overview')
    def overview(request:Request):
        region=request.state.admin['region_code']
        with store.connect() as db:
            counts=db.execute("""SELECT count(*) total,
              count(*) FILTER(WHERE created_at>=(date_trunc('day',now() AT TIME ZONE 'Asia/Jakarta') AT TIME ZONE 'Asia/Jakarta')) today,
              count(*) FILTER(WHERE status<>'complete') incomplete,
              count(*) FILTER(WHERE analysis IS NULL OR analysis->'decision'->>'action'<>'eligible') unverified,
              count(*) FILTER(WHERE EXISTS(SELECT 1 FROM outbox o JOIN incidents i ON i.id=o.incident_id WHERE o.incident_id=reports.incident_id AND o.incident_revision=i.revision AND o.audience<>'reporter' AND o.state='sent' AND nullif(o.provider_message_id,'') IS NOT NULL)
                AND NOT EXISTS(SELECT 1 FROM outbox o JOIN incidents i ON i.id=o.incident_id WHERE o.incident_id=reports.incident_id AND o.incident_revision=i.revision
                  AND o.audience<>'reporter' AND (o.state<>'sent' OR nullif(o.provider_message_id,'') IS NULL))) forwarded
              FROM reports WHERE region_code=%s""",(region,)).fetchone()
            rows=db.execute('SELECT * FROM reports WHERE region_code=%s ORDER BY created_at DESC LIMIT 8',(region,)).fetchall()
        return {'region_code':region,'counts':counts,'recent':[report_card(r) for r in rows]}

    @router.get('/report-list')
    def reports(request:Request,q:str=Query(default='',max_length=100),status:str=Query(default='',max_length=30),
                category:str=Query(default='',max_length=30),since:datetime|None=None,until:datetime|None=None,
                limit:int=Query(default=30,ge=1,le=100),offset:int=Query(default=0,ge=0)):
        params=(request.state.admin['region_code'],q,'%'+q+'%',status,status,category,category,since,since,until,until)
        where="""region_code=%s AND (%s='' OR id::text ILIKE %s) AND (%s='' OR status=%s)
          AND (%s='' OR facts->>'category'=%s) AND (%s::timestamptz IS NULL OR created_at>=%s)
          AND (%s::timestamptz IS NULL OR created_at<=%s)"""
        with store.connect() as db:
            total=db.execute('SELECT count(*) n FROM reports WHERE '+where,params).fetchone()['n']
            rows=db.execute('SELECT * FROM reports WHERE '+where+' ORDER BY created_at DESC,id LIMIT %s OFFSET %s',params+(limit,offset)).fetchall()
        return {'items':[report_card(r) for r in rows],'total':total,'limit':limit,'offset':offset}

    @router.get('/reports/{id}')
    def detail(id:UUID,request:Request):
        with store.connect() as db:
            r=scoped_report(db,id,request.state.admin)
            state=dict(r['state'])
            if state.get('description'):state['description']=redact(state['description'])
            result={'report':dict(report_card(r),state=state,facts=r['facts'],analysis=r['analysis'])}
            if r['state'].get('consent_contact'):result['report']['contact']=r['sender_ref']
            result['sources']=[{'id':s['id'],'text':redact(s['payload'].get('text','')),'received_at':s['created_at']} for s in
                db.execute('SELECT id,payload,created_at FROM inbound_events WHERE report_id=%s ORDER BY seq',(id,)).fetchall()]
            result['evidence']=db.execute('SELECT id,kind,evidence_key,result,created_at FROM evidence_results WHERE report_id=%s ORDER BY created_at DESC LIMIT 100',(id,)).fetchall()
            result['media']=db.execute('SELECT id,kind,content_type,validation_status FROM media WHERE id=ANY(%s::uuid[])',(r['state'].get('media_ids',[]),)).fetchall()
            result['candidates']=db.execute('SELECT incident_id,distance_m,time_delta_s,explanation,reviewed FROM report_incident_matches WHERE report_id=%s',(id,)).fetchall()
            result['deliveries']=db.execute('''SELECT id,audience,destination_id,state,reason,created_at,provider_message_id FROM outbox
              WHERE (report_id=%s OR (incident_id IS NOT NULL AND incident_id=%s)) AND audience<>'reporter' ORDER BY created_at DESC''',(id,r['incident_id'])).fetchall()
            result['audit']=db.execute('SELECT actor,action,created_at,details FROM audit_events WHERE subject_id=%s ORDER BY created_at DESC LIMIT 100',(id,)).fetchall()
            if r['incident_id']:
                incident=db.execute('SELECT id,slug,revision,location_version FROM incidents WHERE id=%s',(r['incident_id'],)).fetchone()
                result['incident']=incident
                result['verification']=verification_summary(db,incident['id'],incident['location_version'])
                result['contributions']=db.execute('SELECT id,choice,description,solved,source,created_at,location_version FROM verification_events WHERE incident_id=%s ORDER BY created_at DESC LIMIT 100',(incident['id'],)).fetchall()
        return result

    @router.get('/media/{id}')
    def media(id:UUID,request:Request):
        with store.connect() as db:
            row=db.execute('''SELECT m.storage_key,m.content_type FROM media m WHERE m.id=%s AND EXISTS(
              SELECT 1 FROM reports r WHERE r.region_code=%s AND r.state->'media_ids' ? m.id::text)''',
              (id,request.state.admin['region_code'])).fetchone()
        if not row:raise HTTPException(404,'NOT_FOUND')
        path=(root/row['storage_key']).resolve()
        if path.parent!=root or not path.is_file():raise HTTPException(404,'NOT_FOUND')
        return FileResponse(path,media_type=row['content_type'],headers={'Cache-Control':'no-store'})

    @router.get('/map')
    def map_data(request:Request,since:datetime|None=None):
        with store.connect() as db:
            region=request.state.admin['region_code']
            rows=db.execute("SELECT * FROM reports WHERE region_code=%s AND state->'location' IS NOT NULL AND (%s::timestamptz IS NULL OR created_at>=%s) ORDER BY created_at DESC LIMIT 1000",(region,since,since)).fetchall()
            cfg=db.execute('SELECT geometry,snapshot FROM regions WHERE code=%s',(region,)).fetchone()
        points=[];seen=set()
        for row in rows:
            card=report_card(row);key=str(row['incident_id'] or row['id'])
            if not card['location'] or key in seen:continue
            seen.add(key);points.append(card)
        from shapely.geometry import shape,Point
        snapshot=dict(cfg['snapshot'] or {})
        if snapshot.get('points'):
            geometry=shape(cfg['geometry']['geometry']) if cfg['geometry'] else None
            snapshot['points']=[p for p in snapshot['points'] if geometry and geometry.contains(Point(p['longitude'],p['latitude']))]
        return {'reports':points,'boundary':cfg['geometry'],'firms':snapshot or None}

    @router.get('/runtime')
    def runtime(request:Request):
        with store.connect() as db:
            region=request.state.admin['region_code']
            settings=db.execute("SELECT value FROM app_settings WHERE key='service'").fetchone()['value']
            jobs=db.execute('''SELECT j.state,count(*) count FROM analysis_jobs j JOIN reports r ON r.id=j.report_id
              WHERE r.region_code=%s GROUP BY j.state''',(region,)).fetchall()
            destinations=db.execute('SELECT count(*) n FROM destinations WHERE region_code=%s AND active AND authorized',(region,)).fetchone()['n']
            snapshot=db.execute('SELECT snapshot FROM regions WHERE code=%s',(region,)).fetchone()['snapshot']
            heartbeats=db.execute('SELECT service,last_seen,details FROM service_heartbeats ORDER BY service').fetchall()
        return {'settings':settings,'analysis_jobs':jobs,'approved_destinations':destinations,
                'firms':{k:v for k,v in (snapshot or {}).items() if k!='points'},
                'region_approved':bool(store.config.region()),'heartbeats':heartbeats,'live_gate':'passed' if settings.get('live_gate_passed') else 'pending'}

    @router.post('/reports/{id}/actions')
    def action(id:UUID,body:Action,request:Request):
        user=request.state.admin
        with store.connect() as db:
            if body.action=='group':
                identity=scoped_report(db,id,user)
                db.execute('SELECT pg_advisory_xact_lock(hashtextextended(%s,0))',('incidents:'+identity['account_id'],))
            r=scoped_report(db,id,user,lock=True)
            if r['revision']!=body.expected_revision:raise HTTPException(409,'REPORT_CHANGED')
            if body.target_id and not db.execute('SELECT 1 FROM incidents WHERE id=%s AND region_code=%s',(body.target_id,user['region_code'])).fetchone():raise HTTPException(404,'NOT_FOUND')
            if body.outbox_id and not db.execute('SELECT 1 FROM outbox WHERE id=%s AND (report_id=%s OR incident_id=%s)',(body.outbox_id,id,r['incident_id'])).fetchone():raise HTTPException(404,'NOT_FOUND')
            if body.action=='recheck':
                if r['status']=='complete':requeue(store,db,r)
                else:
                    revision=r['revision']+1
                    db.execute('UPDATE reports SET task3_enabled=true,revision=%s,analysis=NULL WHERE id=%s',(revision,id))
                    store.enqueue(db,id,revision,r['latest_seq'],'extract')
            elif body.action=='withdraw_public':
                db.execute('UPDATE public_incidents SET withdrawn=true WHERE incident_id=%s',(r['incident_id'],))
            elif body.action=='publish_photo':
                if not r['incident_id'] or str(body.media_id) not in r['state'].get('media_ids',[]):raise HTTPException(422,'REPORT_MEDIA_REQUIRED')
                source=db.execute("SELECT storage_key FROM media WHERE id=%s AND kind='image' AND validation_status='valid'",(body.media_id,)).fetchone()
                if not source:raise HTTPException(422,'VALID_IMAGE_REQUIRED')
                path=(root/source['storage_key']).resolve()
                if path.parent!=root or not path.is_file():raise HTTPException(404,'NOT_FOUND')
                normalized=sanitize_photo(path.read_bytes())
                key='public-'+str(uuid4())+'.jpg'
                with (root/key).open('xb') as out:out.write(normalized)
                if not db.execute('UPDATE public_incidents SET photo_key=%s WHERE incident_id=%s AND NOT withdrawn RETURNING incident_id',(key,r['incident_id'])).fetchone():
                    (root/key).unlink(missing_ok=True)
                    raise HTTPException(422,'PUBLIC_PROJECTION_REQUIRED')
            elif body.action in ('review_evidence','group','reconcile'):
                try:
                    if body.action=='review_evidence':review_evidence(store,id,body.evidence_key,body.reason,body.references,connection=db,actor=str(user['id']))
                    elif body.action=='group':group_incident(store,id,body.target_id,body.reason,connection=db,actor=str(user['id']))
                    else:
                        if not body.outbox_id:raise ValueError('OUTBOX_REQUIRED')
                        reconcile(store,body.outbox_id,body.reason,receipt=body.receipt,retry=body.retry,connection=db,actor=str(user['id']))
                except ValueError as exc:raise HTTPException(422,str(exc)) from None
            else:raise HTTPException(422,'INVALID_ACTION')
            store.audit(db,id,'ADMIN_'+body.action.upper(),{'reason':body.reason,'region_code':user['region_code']},str(user['id']))
        return {'recorded':True}

    app.include_router(router)
