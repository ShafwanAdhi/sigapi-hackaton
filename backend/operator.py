"""Explicit, audited local operator actions. Never erase original evidence."""
import secrets
from urllib.parse import urlparse
from uuid import uuid4
from psycopg.types.json import Jsonb


def reason_required(reason):
    if not isinstance(reason,str) or len(reason.strip())<10:raise ValueError('OPERATOR_REASON_MIN_10_CHARS')


def requeue(store,db,r):
    revision=r['revision']+1
    db.execute('UPDATE reports SET revision=%s,analysis=NULL WHERE id=%s',(revision,r['id']))
    db.execute("UPDATE analysis_jobs SET state='superseded' WHERE report_id=%s AND state='pending'",(r['id'],))
    store.enqueue(db,r['id'],revision,r['latest_seq'],'evidence')
    return revision


def review_evidence(store,report_id,key,reason,references):
    reason_required(reason)
    if not references or any(urlparse(url).scheme not in ('https','http') or not urlparse(url).netloc for url in references):
        raise ValueError('EVIDENCE_REFERENCES_REQUIRED')
    with store.connect() as db:
        r=db.execute('SELECT * FROM reports WHERE id=%s AND active FOR UPDATE',(report_id,)).fetchone()
        if not r or r['status']!='complete':raise ValueError('COMPLETE_ACTIVE_REPORT_REQUIRED')
        ev=db.execute("SELECT * FROM evidence_results WHERE report_id=%s AND revision=%s AND (evidence_key=%s OR %s='local_reuse' AND kind='frame')",(report_id,r['revision'],key,key)).fetchone()
        if not ev:raise ValueError('CURRENT_EVIDENCE_REQUIRED')
        revision=requeue(store,db,r)
        # Carry prior resolutions only for unchanged evidence; originals retain their revision.
        db.execute('''INSERT INTO manual_reviews(id,report_id,revision,evidence_key,reason,references_json)
          SELECT gen_random_uuid(),report_id,%s,evidence_key,reason,references_json FROM manual_reviews
          WHERE report_id=%s AND revision=%s''',(revision,report_id,r['revision']))
        db.execute('INSERT INTO manual_reviews(id,report_id,revision,evidence_key,reason,references_json) VALUES(%s,%s,%s,%s,%s,%s)',
                   (uuid4(),report_id,revision,key,reason,Jsonb(references)))
        store.audit(db,report_id,'EVIDENCE_REVIEWED',{'evidence_id':str(ev['id']),'key':key,'reason':reason,'references':references,'revision':revision},'operator')


def group_incident(store,report_id,target_id,reason):
    """target=None confirms a separate incident; a candidate UUID confirms a merge."""
    reason_required(reason)
    with store.connect() as db:
        # Same lock order as matching; serialize grouping within an account.
        identity=db.execute('SELECT account_id FROM reports WHERE id=%s',(report_id,)).fetchone()
        if not identity:raise ValueError('REPORT_NOT_FOUND')
        db.execute('SELECT pg_advisory_xact_lock(hashtextextended(%s,0))',('incidents:'+identity['account_id'],))
        r=db.execute('SELECT * FROM reports WHERE id=%s AND active FOR UPDATE',(report_id,)).fetchone()
        if not r or not r['incident_id']:raise ValueError('INCIDENT_REQUIRED')
        old=r['incident_id']
        if target_id:
            candidate=db.execute('SELECT 1 FROM report_incident_matches WHERE report_id=%s AND incident_id=%s',(report_id,target_id)).fetchone()
            if not candidate:raise ValueError('CANDIDATE_REQUIRED')
            dest=db.execute('SELECT * FROM incidents WHERE id=%s AND account_id=%s FOR UPDATE',(target_id,r['account_id'])).fetchone()
            if not dest:raise ValueError('SAME_ACCOUNT_INCIDENT_REQUIRED')
        else:
            count=db.execute('SELECT count(*) n FROM reports WHERE incident_id=%s',(old,)).fetchone()['n']
            if count>1:
                target_id=uuid4()
                db.execute('''INSERT INTO incidents(id,slug,location,observed_at,category,account_id)
                   VALUES(%s,%s,%s,%s,%s,%s)''',(target_id,secrets.token_hex(16),Jsonb(r['state']['location']),r['facts'].get('observed_at'),r['facts'].get('category','unknown'),r['account_id']))
            else:
                target_id=old
                db.execute('UPDATE incidents SET location=%s,observed_at=%s,category=%s WHERE id=%s',
                   (Jsonb(r['state']['location']),r['facts'].get('observed_at'),r['facts'].get('category','unknown'),old))
        db.execute('UPDATE reports SET incident_id=%s,incident_basis=%s WHERE id=%s',
                   (target_id,Jsonb({'location':r['state']['location'],'observed_at':r['facts'].get('observed_at'),'category':r['facts'].get('category','unknown')}),report_id))
        db.execute('UPDATE incidents SET pending_review=false,revision=revision+1 WHERE id=%s',(target_id,))
        db.execute('UPDATE report_incident_matches SET reviewed=true WHERE report_id=%s',(report_id,))
        db.execute("UPDATE outbox SET state='cancelled',reason='OPERATOR_REGROUPED' WHERE report_id=%s AND audience<>'reporter' AND state IN ('pending','leased')",(report_id,))
        requeue(store,db,r)
        store.audit(db,report_id,'INCIDENT_GROUP_REVIEWED',{'from':str(old),'to':str(target_id),'reason':reason},'operator')


def reconcile(store,outbox_id,reason,receipt=None,retry=False):
    reason_required(reason)
    if bool(receipt)==bool(retry):raise ValueError('CHOOSE_RECEIPT_OR_EXPLICIT_RETRY')
    if receipt and (not isinstance(receipt,str) or len(receipt)>300):raise ValueError('INVALID_RECEIPT')
    with store.connect() as db:
        row=db.execute("SELECT * FROM outbox WHERE id=%s AND state='unknown' FOR UPDATE",(outbox_id,)).fetchone()
        if not row:raise ValueError('UNKNOWN_OUTBOX_REQUIRED')
        db.execute('''UPDATE outbox SET state=%s,provider_message_id=%s,lease_token=NULL,lease_until=NULL,
          available_at=now(),reason='OPERATOR_RECONCILED' WHERE id=%s''',('pending' if retry else 'sent',receipt,outbox_id))
        store.audit(db,row['report_id'],'DELIVERY_RECONCILED',{'outbox_id':str(outbox_id),'reason':reason,'receipt':receipt,'retry':retry},'operator')


def inspect_report(store,report_id):
    with store.connect() as db:
        result={'report':db.execute('SELECT * FROM reports WHERE id=%s',(report_id,)).fetchone()}
        for name in ('evidence_results','policy_decisions','report_incident_matches','manual_reviews','analysis_jobs','outbox'):
            result[name]=db.execute(f'SELECT * FROM {name} WHERE report_id=%s',(report_id,)).fetchall()
        result['audit']=db.execute('SELECT * FROM audit_events WHERE subject_id=%s ORDER BY created_at',(report_id,)).fetchall()
    return result
