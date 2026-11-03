"""Durable extraction/evidence queue with input and lease fencing."""
import json
import re
import os
from uuid import uuid4
from psycopg.types.json import Jsonb
from backend.store import Store
from backend.conversation import advance
from backend.facts import resolve_time, threat_claim, redact


class AnalysisStore(Store):
    task3=True

    def __init__(self,dsn,config=None):
        super().__init__(dsn)
        from backend.task3_config import Task3Config
        self.config=config or Task3Config()

    @staticmethod
    def is_free_text(text):
        s=text.strip().upper()
        return bool(s and s not in ('REPORT','LAPOR','BARU','LANJUT','HALO','HAI','HI','STATUS','GANTI LOKASI')
                    and not s.startswith(('KONFIRMASI LOKASI','IZIN KONTAK','TRACK','KETERANGAN:')))

    @staticmethod
    def natural_reply(text):
        return (text.replace('Kirim KETERANGAN: diikuti penjelasan kejadian (minimal 10 karakter)',
                   'Ceritakan kejadian dengan kalimat biasa (minimal 10 karakter)')
                    .replace('dan KETERANGAN: penjelasan kejadian.','dan ceritakan apa yang terbakar serta kapan terlihat.')
                    .replace('dan KETERANGAN: untuk melanjutkan','dan cerita kejadian untuk melanjutkan'))

    def on_intake(self,db,report_id,seq):
        r=db.execute('SELECT * FROM reports WHERE id=%s FOR UPDATE',(report_id,)).fetchone()
        if not r['task3_enabled']:return
        db.execute('UPDATE reports SET latest_seq=%s WHERE id=%s',(seq,report_id))
        db.execute("UPDATE analysis_jobs SET state='superseded' WHERE report_id=%s AND state='pending'",(report_id,))
        self.enqueue(db,report_id,r['revision'],seq,'extract')

    @staticmethod
    def status_reply(db,r):
        decision=(r['analysis'] or {}).get('decision',{})
        checked=r['analysis_revision']==r['revision'] and bool(decision)
        text='Data: '+r['status']+'. Pemeriksaan: '+(decision['action'] if checked else 'menunggu; belum ada hasil terbaru')+'.'
        rows=db.execute("SELECT audience,state FROM outbox WHERE report_id=%s AND audience<>'reporter' ORDER BY created_at",(r['id'],)).fetchall()
        if rows:text+=' Pengiriman uji: '+', '.join(x['audience']+'='+x['state'] for x in rows)+'.'
        else:text+=' Belum dikirim ke kontak komunitas/otoritas.'
        return text[:1100]+' Ini pemeriksaan awal, bukan konfirmasi resmi.'

    @staticmethod
    def enqueue(db,report_id,revision,seq,kind):
        db.execute('''INSERT INTO analysis_jobs(id,report_id,revision,input_seq,kind)
            VALUES(%s,%s,%s,%s,%s) ON CONFLICT DO NOTHING''',(uuid4(),report_id,revision,seq,kind))

    def opt_in(self,report_id):
        with self.connect() as db:
            r=db.execute("SELECT * FROM reports WHERE id=%s AND lifecycle='open' FOR UPDATE",(report_id,)).fetchone()
            if not r:raise ValueError('ACTIVE_REPORT_NOT_FOUND')
            seq=db.execute('SELECT max(seq) n FROM inbound_events WHERE report_id=%s',(report_id,)).fetchone()['n']
            if not seq:raise ValueError('NO_INPUT')
            revision=r['revision']+1
            db.execute('UPDATE reports SET task3_enabled=true,latest_seq=%s,revision=%s,analysis=NULL WHERE id=%s',(seq,revision,report_id))
            db.execute("UPDATE analysis_jobs SET state='superseded' WHERE report_id=%s AND state='pending'",(report_id,))
            self.enqueue(db,report_id,revision,seq,'extract')
            self.audit(db,report_id,'ANALYSIS_OPT_IN',{})

    @staticmethod
    def audit(db,subject,action,details,actor='system'):
        db.execute('INSERT INTO audit_events VALUES(%s,%s,%s,%s,%s,now())',(uuid4(),subject,actor,action,Jsonb(details)))

    def claim_analysis(self,account=None,report_id=None):
        with self.connect() as db:
            j=db.execute('''SELECT j.* FROM analysis_jobs j JOIN reports r ON r.id=j.report_id WHERE
              (j.state='pending' OR (j.state='running' AND j.lease_until<now())) AND j.available_at<=now()
              AND (%s::text IS NULL OR r.account_id=%s) AND r.lifecycle='open'
              AND NOT EXISTS(SELECT 1 FROM inbound_events e WHERE e.account_id=r.account_id AND e.sender_ref=r.sender_ref AND NOT e.processed)
              AND (%s::uuid IS NULL OR r.id=%s)
              ORDER BY CASE WHEN j.kind='extract' THEN 0 ELSE 1 END,j.created_at
              FOR UPDATE OF j SKIP LOCKED LIMIT 1''',(account,account,report_id,report_id)).fetchone()
            if not j:return None
            return db.execute("UPDATE analysis_jobs SET state='running',lease_token=%s,lease_until=now()+interval '3 minutes',attempts=attempts+1 WHERE id=%s RETURNING *",(uuid4(),j['id'])).fetchone()

    def renew(self,job):
        with self.connect() as db:
            return db.execute("UPDATE analysis_jobs SET lease_until=now()+interval '3 minutes' WHERE id=%s AND lease_token=%s AND state='running' AND lease_until>now()",(job['id'],job['lease_token'])).rowcount==1

    def is_current(self,job,db=None):
        if db is None:
            with self.connect() as conn:return self.is_current(job,conn)
        return bool(db.execute('''SELECT 1 FROM reports r JOIN analysis_jobs j ON j.report_id=r.id
          WHERE j.id=%s AND j.state='running' AND j.lease_token=%s AND j.lease_until>now()
          AND r.lifecycle='open' AND r.task3_enabled AND r.revision=%s AND r.latest_seq=%s
          AND NOT EXISTS(SELECT 1 FROM inbound_events e WHERE e.account_id=r.account_id
             AND e.sender_ref=r.sender_ref AND e.seq>r.latest_seq AND NOT e.processed)''',
          (job['id'],job['lease_token'],job['revision'],job['input_seq'])).fetchone())

    def end_analysis(self,job,state,db=None):
        if db is None:
            with self.connect() as connection:return self.end_analysis(job,state,connection)
        db.execute("""UPDATE analysis_jobs j SET state=CASE WHEN %s='superseded' AND EXISTS(
          SELECT 1 FROM reports r WHERE r.id=j.report_id AND r.lifecycle='open'
          AND r.revision=%s AND r.latest_seq=%s AND EXISTS(SELECT 1 FROM inbound_events e
            WHERE e.account_id=r.account_id AND e.sender_ref=r.sender_ref AND NOT e.processed))
          THEN 'pending' ELSE %s END,lease_until=NULL
          WHERE j.id=%s AND j.lease_token=%s AND j.state='running'""",
          (state,job['revision'],job['input_seq'],state,job['id'],job['lease_token']))

    def snapshot(self,job):
        with self.connect() as db:
            r=db.execute('SELECT * FROM reports WHERE id=%s',(job['report_id'],)).fetchone()
            sources=db.execute('SELECT id,payload FROM inbound_events WHERE report_id=%s AND seq<=%s ORDER BY seq',(r['id'],job['input_seq'])).fetchall()
            result=[]
            for row in sources:
                text=row['payload'].get('text','').strip()
                if self.is_free_text(text) or text.upper().startswith('KETERANGAN:'):
                    result.append({'id':str(row['id']),'text':text,'received_at':row['payload']['received_at']})
            return r,result

    @staticmethod
    def notify(db,r,source_key,text):
        db.execute('''INSERT INTO outbox(id,report_id,account_id,sender_ref,text,source_key,report_revision,input_seq)
          VALUES(%s,%s,%s,%s,%s,%s,%s,%s) ON CONFLICT(source_key) DO NOTHING''',
          (uuid4(),r['id'],r['account_id'],r['sender_ref'],('SIGAPI · ' if os.environ.get('SIGAPI_RUN_MODE')=='pilot' else '[UJI] ')+'Laporan '+str(r['id'])[:8]+': '+text[:1200],source_key,r['revision'],r['latest_seq']))

    def commit_extraction(self,job,result,sources):
        with self.connect() as db:
            db.execute('SELECT id FROM analysis_jobs WHERE id=%s FOR UPDATE',(job['id'],))
            r=db.execute('SELECT * FROM reports WHERE id=%s FOR UPDATE',(job['report_id'],)).fetchone()
            if not self.is_current(job,db):return False
            state=dict(r['state']);prior=r['facts']
            times=[dict(id=ref['source_id'],text=ref['quote'],received_at=next(s['received_at'] for s in sources if s['id']==ref['source_id'])) for ref in result.get('time_sources',[])]
            facts={'extraction':result,'observed_at':resolve_time(times),'category':result.get('category','unknown'),
                   'risk':threat_claim(sources),'extraction_outcome':result.get('outcome','success'),
                   'input_evidence':{'media_ids':state['media_ids'],'location':state['location']}}
            if state.get('description_source') in (None,'ai') and result.get('description_sources'):
                state['description']=' '.join(ref['quote'] for ref in result['description_sources'])[:4000]
                state['description_source']='ai'
            state,_=advance(state,{'id':str(job['id']),'text':'','media':[],'location':None})
            changed=state.get('description')!=r['state'].get('description') or facts!=prior
            meaningful=any(facts.get(k)!=prior.get(k) for k in ('observed_at','category','input_evidence')) or facts['risk']['level']!=prior.get('risk',{}).get('level') or not r['state'].get('description') and bool(state.get('description'))
            revision=r['revision']+int(changed)
            db.execute('UPDATE reports SET state=%s,status=%s,facts=%s,revision=%s,analysis=NULL,clarification_count=CASE WHEN %s THEN 0 ELSE clarification_count END WHERE id=%s',
                       (Jsonb(state),state['status'],Jsonb(facts),revision,meaningful,r['id']))
            r=dict(r,state=state,status=state['status'],facts=facts,revision=revision)
            self.evidence(db,dict(job,revision=revision),'extraction','sources',dict(facts,job_revision=job['revision']))
            if facts['risk'].get('reason')=='THREAT_NEEDS_CONFIRMATION':
                self.notify(db,r,f'threat-question:{r["id"]}:{revision}:{r["latest_seq"]}',
                    'Apakah saat ini ada orang terjebak/terancam, perlu evakuasi, atau api mengancam rumah/fasilitas? Jelaskan kondisi saat ini secara eksplisit.')
            if state['status']=='complete':self.enqueue(db,r['id'],revision,r['latest_seq'],'evidence')
            else:
                _,reply=advance(state,{'id':str(job['id']),'text':'','media':[],'location':None})
                self.notify(db,r,f'extract:{r["id"]}:{revision}:{r["latest_seq"]}',self.natural_reply(reply))
            db.execute("UPDATE analysis_jobs SET state='done',lease_until=NULL WHERE id=%s",(job['id'],))
            return True

    @staticmethod
    def evidence(db,job,kind,key,result):
        db.execute('''INSERT INTO evidence_results(id,report_id,revision,input_seq,kind,evidence_key,result)
          VALUES(%s,%s,%s,%s,%s,%s,%s) ON CONFLICT DO NOTHING''',
          (uuid4(),job['report_id'],job['revision'],job['input_seq'],kind,key,Jsonb(result)))

    def reserve_operation(self,key):
        with self.connect() as db:
            db.execute('INSERT INTO provider_operations(operation_key) VALUES(%s) ON CONFLICT DO NOTHING',(key,))
            return db.execute('UPDATE provider_operations SET attempts=attempts+1 WHERE operation_key=%s AND attempts<3',(key,)).rowcount==1

    def cached_result(self,key):
        with self.connect() as db:
            r=db.execute('SELECT result FROM provider_operations WHERE operation_key=%s',(key,)).fetchone()
            return r['result'] if r else None

    def cache_result(self,key,result):
        with self.connect() as db:
            db.execute('INSERT INTO provider_operations(operation_key,result) VALUES(%s,%s) ON CONFLICT(operation_key) DO UPDATE SET result=excluded.result',(key,Jsonb(result)))

    def claim_outbox(self,accounts,senders,*,public_reporters=False):
        with self.connect() as db:
            db.execute("UPDATE outbox SET state='unknown',reason='SEND_LEASE_EXPIRED' WHERE state='sending' AND lease_until<now()")
            row=db.execute('''SELECT o.* FROM outbox o WHERE o.account_id=ANY(%s) AND
              (o.sender_ref=ANY(%s) OR (%s AND o.audience='reporter' AND EXISTS(
                SELECT 1 FROM inbound_events e WHERE e.account_id=o.account_id AND e.sender_ref=o.sender_ref
                AND (e.seq=o.event_seq OR e.report_id=o.report_id))))
              AND o.available_at<=now() AND (o.state='pending' OR (o.state='leased' AND o.lease_until<now()))
              AND NOT EXISTS(SELECT 1 FROM outbox earlier WHERE earlier.account_id=o.account_id AND earlier.sender_ref=o.sender_ref
                AND (earlier.created_at,earlier.id)<(o.created_at,o.id) AND earlier.state IN ('pending','leased','sending'))
              ORDER BY o.created_at,o.id FOR UPDATE OF o SKIP LOCKED LIMIT 1''',(accounts,senders,public_reporters)).fetchone()
            if not row:return None
            return db.execute("UPDATE outbox SET state='leased',lease_token=%s,lease_until=now()+interval '60 seconds' WHERE id=%s RETURNING *",(uuid4(),row['id'])).fetchone()

    def start_send(self,id,token):
        with self.connect() as db:
            identity=db.execute('SELECT report_id FROM outbox WHERE id=%s',(id,)).fetchone()
            if not identity:return False
            r=db.execute('SELECT * FROM reports WHERE id=%s FOR UPDATE',(identity['report_id'],)).fetchone() if identity['report_id'] else None
            row=db.execute('SELECT * FROM outbox WHERE id=%s FOR UPDATE',(id,)).fetchone()
            if not row or row['state']!='leased' or row['lease_token']!=token:return False
            valid=True
            if row['report_revision'] is not None:
                valid=bool(r and r['lifecycle']=='open' and r['revision']==row['report_revision'] and r['latest_seq']==row['input_seq'])
                if r and db.execute('SELECT 1 FROM inbound_events WHERE account_id=%s AND sender_ref=%s AND seq>%s AND NOT processed LIMIT 1',(r['account_id'],r['sender_ref'],r['latest_seq'])).fetchone():valid=False
            if row['audience']!='reporter':
                valid=valid and self.config.allowed(row['audience'],row['sender_ref'],row['account_id'])
                if row['destination_version'] is not None:
                    destination=self.config.destinations().get(row['destination_id'])
                    valid=valid and bool(destination and destination.get('version')==row['destination_version'])
                valid=valid and bool(r and row['sender_ref']!=r['sender_ref'])
                incident=db.execute('SELECT revision,pending_review FROM incidents WHERE id=%s',(row['incident_id'],)).fetchone()
                valid=valid and bool(incident and incident['revision']==row['incident_revision'])
                from backend.geospatial import region_check
                loc=r['state'].get('location') if r else None
                valid=valid and bool(r and r['status']=='complete' and r['state']['location_confirmed'] and loc
                    and region_check(self.config.region(),loc['latitude'],loc['longitude'])=='inside')
                if valid and row['escalation']:
                    source_rows=db.execute('SELECT id,payload FROM inbound_events WHERE report_id=%s ORDER BY seq',(r['id'],)).fetchall()
                    valid=row['audience']=='authority' and threat_claim([{'id':str(s['id']),'text':s['payload'].get('text','')} for s in source_rows])['level']=='high'
                elif valid:
                    decision=(r['analysis'] or {}).get('decision',{})
                    valid=bool(r['analysis_revision']==r['revision'] and decision.get('action')=='eligible'
                       and row['audience'] in decision.get('destinations',[]) and not incident['pending_review'])
                if valid and row['audience']=='authority':
                    # Include current contact only at send admission. Never persist it in public cards.
                    text=row['text'].split('\nKontak pelapor:')[0]
                    if r['state']['consent_contact']:text+='\nKontak pelapor: '+r['sender_ref']
                    db.execute('UPDATE outbox SET text=%s WHERE id=%s',(text[:1500],id))
                if valid:
                    db.execute('SELECT pg_advisory_xact_lock(hashtextextended(%s,0))',('send-rate:'+row['sender_ref'],))
                    count=db.execute("SELECT count(*) n FROM audit_events WHERE action='DELIVERY_ADMITTED' AND details->>'recipient'=%s AND created_at>now()-interval '10 minutes'",(row['sender_ref'],)).fetchone()['n']
                    if count>=5:
                        db.execute("UPDATE outbox SET state='pending',available_at=now()+interval '1 minute',reason='RATE_LIMITED' WHERE id=%s",(id,))
                        return False
            if not valid:
                db.execute("UPDATE outbox SET state='cancelled',reason='STALE_OR_DISABLED' WHERE id=%s",(id,));return False
            started=db.execute("UPDATE outbox SET state='sending',lease_until=now()+interval '60 seconds' WHERE id=%s AND lease_until>now()",(id,)).rowcount==1
            if started and row['audience']!='reporter':self.audit(db,row['report_id'],'DELIVERY_ADMITTED',{'recipient':row['sender_ref'],'outbox_id':str(id)})
            return started

    def finish_send(self,id,token,message_id=None):
        with self.connect() as db:
            row=db.execute('SELECT * FROM outbox WHERE id=%s FOR UPDATE',(id,)).fetchone()
            if not row or row['lease_token']!=token or row['state']!='sending':return False
            db.execute('UPDATE outbox SET state=%s,provider_message_id=%s,reason=%s WHERE id=%s',
                       ('sent' if message_id else 'unknown',message_id,None if message_id else 'SEND_RESULT_UNKNOWN',id))
            if row['audience']!='reporter':
                r=db.execute('SELECT * FROM reports WHERE id=%s',(row['report_id'],)).fetchone()
                text=('Berhasil dikirim ke kontak uji '+row['audience']+'.' if message_id else 'Hasil pengiriman ke kontak uji '+row['audience']+' belum dapat dipastikan; operator perlu memeriksa.')
                self.notify(db,r,'delivery-result:'+str(id),text)
                self.audit(db,r['id'],'DELIVERY_RESULT',{'outbox_id':str(id),'state':'sent' if message_id else 'unknown'})
            return True

    def admitted_text(self,id,token):
        with self.connect() as db:
            r=db.execute("SELECT text FROM outbox WHERE id=%s AND lease_token=%s AND state='sending'",(id,token)).fetchone()
            return r['text'] if r else None
