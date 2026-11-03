"""Bounded NASA refresh and explicit scoped retention; never purge at startup."""
import time
from datetime import datetime,timedelta,timezone
from pathlib import Path
from psycopg.types.json import Jsonb
import httpx
from backend.task3_data import FIRMS_URL,parse_firms
from backend.operator import requeue


def fetch_snapshot():
    with httpx.Client(timeout=30,follow_redirects=False,headers={'User-Agent':'SIGAPI/0.1'}) as client:
        response=client.get(FIRMS_URL);response.raise_for_status()
        return parse_firms(response.content,response.headers,datetime.now(timezone.utc))


def refresh_firms(store,*,fetch=fetch_snapshot):
    try:
        snapshot=fetch()
        from backend.geospatial import firms_check
        # The real parser already enforces source, timestamp, bounds and finite values.
        if not isinstance(snapshot,dict) or not snapshot.get('sha256') or not snapshot.get('source','').startswith('https://firms.modaps.eosdis.nasa.gov/'):
            raise ValueError('INVALID_SNAPSHOT')
        with store.connect() as db:
            db.execute('SELECT pg_advisory_xact_lock(76431004)')
            old=db.execute("SELECT snapshot FROM regions WHERE code='35.73' FOR UPDATE").fetchone()['snapshot']
            if old and old.get('sha256')==snapshot['sha256']:return {'outcome':'unchanged','requeued':0}
            db.execute("UPDATE regions SET snapshot=%s,updated_at=now() WHERE code='35.73'",(Jsonb(snapshot),))
            rows=db.execute("SELECT * FROM reports WHERE region_code='35.73' AND lifecycle='open' AND status='complete' AND analysis->'decision'->'reasons' ? 'FIRMS_UNAVAILABLE' FOR UPDATE").fetchall()
            count=0
            for report in rows:
                loc=report['state'].get('location');observed=report['facts'].get('observed_at')
                if not loc or not observed:continue
                result=firms_check(snapshot,loc['latitude'],loc['longitude'],observed)
                if result['outcome']!='unavailable':requeue(store,db,report);count+=1
            store.audit(db,None,'FIRMS_REFRESHED',{'sha256':snapshot['sha256'],'coverage_end':snapshot['coverage_end'],'requeued':count})
        store.beat('firms',{'outcome':'available','coverage_end':snapshot['coverage_end']})
        return {'outcome':'available','requeued':count}
    except Exception:
        store.beat('firms',{'outcome':'unavailable'})
        return {'outcome':'unavailable','requeued':0}


def purge(store,media_root,*,dry_run=True,now=None,gateway_root=None):
    """Expire an incident and all its sources seven days after its earliest source."""
    now=now or datetime.now(timezone.utc);cutoff=now-timedelta(days=7)
    root=Path(media_root).resolve();files=[]
    with store.connect() as db:
        db.execute('SELECT pg_advisory_xact_lock(76431005)')
        incidents=[r['id'] for r in db.execute('''SELECT id FROM incidents WHERE created_at<%s OR id IN
          (SELECT incident_id FROM reports WHERE incident_id IS NOT NULL AND (created_at<%s OR id IN
            (SELECT report_id FROM inbound_events WHERE created_at<%s)))''',(cutoff,cutoff,cutoff)).fetchall()]
        reports=db.execute('SELECT id,state FROM reports WHERE created_at<%s OR incident_id=ANY(%s::uuid[]) OR id IN (SELECT report_id FROM inbound_events WHERE created_at<%s)',(cutoff,incidents,cutoff)).fetchall()
        ids=[r['id'] for r in reports];media_ids=[mid for r in reports for mid in r['state'].get('media_ids',[])]
        media=db.execute('''SELECT id,storage_key FROM media WHERE id=ANY(%s::uuid[]) OR
          (created_at<%s AND NOT EXISTS(SELECT 1 FROM reports r WHERE r.state->'media_ids' ? media.id::text))''',(media_ids,cutoff)).fetchall()
        files.extend(r['storage_key'] for r in media)
        files.extend(r['photo_key'] for r in db.execute('SELECT photo_key FROM public_incidents WHERE incident_id=ANY(%s::uuid[])',(incidents,)).fetchall() if r['photo_key'])
        files.extend(r['photo_key'] for r in db.execute('SELECT photo_key FROM verification_events WHERE incident_id=ANY(%s::uuid[]) OR created_at<%s',(incidents,cutoff)).fetchall() if r['photo_key'])
        result={'dry_run':dry_run,'reports':len(ids),'incidents':len(incidents),'media':len(files)}
        if dry_run:return result
        for key in set(files):
            db.execute('INSERT INTO file_deletions(storage_key) VALUES(%s) ON CONFLICT DO NOTHING',(key,))
        db.execute("UPDATE reports SET lifecycle='expired' WHERE id=ANY(%s::uuid[])",(ids,))
        outbox=[r['id'] for r in db.execute('SELECT id FROM outbox WHERE report_id=ANY(%s::uuid[]) OR incident_id=ANY(%s::uuid[]) OR created_at<%s',(ids,incidents,cutoff)).fetchall()]
        db.execute('DELETE FROM delivery_events WHERE outbox_id=ANY(%s::uuid[]) OR report_id=ANY(%s::uuid[])',(outbox,ids))
        db.execute('DELETE FROM outbox WHERE id=ANY(%s::uuid[])',(outbox,))
        db.execute('DELETE FROM report_incident_matches WHERE report_id=ANY(%s::uuid[]) OR incident_id=ANY(%s::uuid[])',(ids,incidents))
        for table in ('manual_reviews','evidence_results','policy_decisions','report_fingerprints','analysis_jobs','analysis_runs'):
            db.execute('DELETE FROM '+table+' WHERE report_id=ANY(%s::uuid[])',(ids,))
        events=[r['seq'] for r in db.execute('SELECT seq FROM inbound_events WHERE report_id=ANY(%s::uuid[]) OR created_at<%s',(ids,cutoff)).fetchall()]
        db.execute('DELETE FROM consent_events WHERE event_seq=ANY(%s::bigint[]) OR report_id=ANY(%s::uuid[])',(events,ids))
        db.execute('DELETE FROM jobs WHERE event_seq=ANY(%s::bigint[])',(events,))
        db.execute('DELETE FROM inbound_events WHERE seq=ANY(%s::bigint[])',(events,))
        db.execute('DELETE FROM verification_events WHERE incident_id=ANY(%s::uuid[]) OR created_at<%s',(incidents,cutoff))
        db.execute('DELETE FROM public_incidents WHERE incident_id=ANY(%s::uuid[])',(incidents,))
        db.execute('DELETE FROM reports WHERE id=ANY(%s::uuid[])',(ids,))
        db.execute('DELETE FROM incidents WHERE id=ANY(%s::uuid[])',(incidents,))
        db.execute('DELETE FROM media WHERE id=ANY(%s::uuid[])',([r['id'] for r in media],))
        db.execute('DELETE FROM audit_events WHERE created_at<%s OR subject_id=ANY(%s::uuid[])',(cutoff,ids+incidents))
        db.execute('DELETE FROM intake_admissions WHERE created_at<%s',(cutoff,))
        db.execute('DELETE FROM rate_limits WHERE expires_at<now()')
        db.execute('DELETE FROM admin_sessions WHERE expires_at<now()')
        # Retain spent operation counters; never reset paid-provider retry budgets.
        db.execute('UPDATE provider_operations SET result=NULL WHERE created_at<%s',(cutoff,))
        store.audit(db,None,'RETENTION_PURGE',result,'system_retention')
    with store.connect() as db:
        pending=db.execute('SELECT storage_key FROM file_deletions').fetchall()
    for item in pending:
        key=item['storage_key']
        path=(root/key).resolve()
        if path.parent!=root:continue
        try:
            path.unlink(missing_ok=True)
        except OSError:
            continue
        with store.connect() as db:
            db.execute('DELETE FROM file_deletions WHERE storage_key=%s',(key,))
    # Remove orphan derivatives/temporary uploads only; arbitrary config files stay.
    for path in root.iterdir():
        if path.is_file() and (path.name.startswith(('public-','verification-')) or path.suffix=='.part') and path.stat().st_mtime<cutoff.timestamp():
            path.unlink()
    if gateway_root:
        gateway=Path(gateway_root).resolve()
        for relative in ('logs','state/agents/main/sessions','state/media/inbound'):
            directory=gateway/relative
            if directory.is_dir():
                for path in directory.rglob('*'):
                    actual=path.resolve()
                    permitted=relative=='state/media/inbound' or actual.suffix in ('.log','.jsonl')
                    if actual.is_relative_to(directory.resolve()) and actual.is_file() and permitted and actual.stat().st_mtime<cutoff.timestamp():actual.unlink()
        spool=gateway/'transport-spool'
        if spool.is_dir():
            import re,shutil
            for path in spool.iterdir():
                if re.fullmatch('[a-f0-9]{64}',path.name) and path.is_dir() and not path.is_symlink():
                    entries=list(path.iterdir())
                    if entries and all(p.stat().st_mtime<cutoff.timestamp() for p in entries):
                        actual=path.resolve()
                        if actual.parent==spool.resolve():shutil.rmtree(actual)
    return result


def run_scheduler(store,root,*,once=False,retention=False,gateway_root=None):
    last_refresh=0.;first=True
    if retention:
        with store.connect() as db:
            db.execute("INSERT INTO app_settings(key,value) VALUES('retention_next_due',%s) ON CONFLICT DO NOTHING",
                       (Jsonb({'at':(datetime.now(timezone.utc)+timedelta(days=1)).isoformat()}),))
    while True:
        store.beat('scheduler')
        if time.monotonic()-last_refresh>=3600 or last_refresh==0:
            refresh_firms(store);last_refresh=time.monotonic()
        # Persist the due date across backups/restarts; never purge on startup.
        if retention and not first:
            with store.connect() as db:
                due=db.execute("SELECT value FROM app_settings WHERE key='retention_next_due'").fetchone()['value']['at']
            if datetime.now(timezone.utc)>=datetime.fromisoformat(due):
                purge(store,root,dry_run=False,gateway_root=gateway_root)
                with store.connect() as db:
                    db.execute("UPDATE app_settings SET value=%s WHERE key='retention_next_due'",
                               (Jsonb({'at':(datetime.now(timezone.utc)+timedelta(days=1)).isoformat()}),))
        first=False
        if once:return
        time.sleep(30)
