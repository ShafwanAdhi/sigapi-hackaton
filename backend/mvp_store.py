"""Application state shared by the transport, APIs and workers."""
import hashlib
import json
import os
import time
from uuid import uuid4
from argon2 import PasswordHasher
from psycopg.types.json import Jsonb
from backend.analysis_store import AnalysisStore
from backend.geospatial import region_check
from fastapi import HTTPException


PASSWORDS = PasswordHasher(time_cost=2, memory_cost=19456, parallelism=1)


def consume_limit(db, key, maximum, seconds):
    row = db.execute("""INSERT INTO rate_limits(key,attempts,expires_at)
      VALUES(%s,1,now()+(%s * interval '1 second')) ON CONFLICT(key) DO UPDATE SET
      attempts=CASE WHEN rate_limits.expires_at<=now() THEN 1 ELSE rate_limits.attempts+1 END,
      expires_at=CASE WHEN rate_limits.expires_at<=now() THEN excluded.expires_at ELSE rate_limits.expires_at END
      RETURNING attempts""", (key, seconds)).fetchone()
    return row['attempts'] <= maximum


class DatabaseConfig:
    """No filesystem configuration may silently override dashboard changes."""
    def __init__(self, store):
        self.store = store

    def read(self):
        with self.store.connect() as db:
            return db.execute("SELECT value FROM app_settings WHERE key='service'").fetchone()['value']

    def region(self):
        with self.store.connect() as db:
            row = db.execute("SELECT geometry,approved_sha256 FROM regions WHERE code='35.73'").fetchone()
        if not row or not row['geometry'] or not row['approved_sha256']:
            return None
        raw = json.dumps(row['geometry'], sort_keys=True, separators=(',', ':')).encode()
        return row['geometry'] if hashlib.sha256(raw).hexdigest() == row['approved_sha256'] else None

    def snapshot(self):
        with self.store.connect() as db:
            return db.execute("SELECT snapshot FROM regions WHERE code='35.73'").fetchone()['snapshot']

    def destinations(self):
        if not self.read().get('distribution_enabled') or not self.region():
            return {}
        bot = os.environ.get('SIGAPI_BOT_NUMBER')
        with self.store.connect() as db:
            rows = db.execute("SELECT * FROM destinations WHERE region_code='35.73' AND active AND authorized").fetchall()
        return {str(r['id']):dict(r, id=str(r['id'])) for r in rows if r['number'] != bot}

    def allowed(self, role, number, account):
        return any(r['role'] == role and r['number'] == number and r['account_id'] == account
                   for r in self.destinations().values())


class MvpStore(AnalysisStore):
    def __init__(self, dsn, config=None):
        super().__init__(dsn, config)
        if config is None:
            self.config = DatabaseConfig(self)
        self._last_beat={}

    def beat(self,service,details=None):
        if not details and time.monotonic()-self._last_beat.get(service,0)<30:return
        with self.connect() as db:
            db.execute('''INSERT INTO service_heartbeats(service,details) VALUES(%s,%s) ON CONFLICT(service)
              DO UPDATE SET last_seen=now(),details=excluded.details''',(service,Jsonb(details or {})))
        self._last_beat[service]=time.monotonic()

    def reserve_operation(self,key):
        from backend.providers import ProviderUnavailable
        provider='groq' if 'groq.com' in key else 'serpapi' if 'serpapi.com' in key else 'vision'
        limit=int(os.environ.get('SIGAPI_'+provider.upper()+'_DAILY_REQUESTS','100' if provider=='groq' else '50' if provider=='serpapi' else '0'))
        with self.connect() as db:
            db.execute('INSERT INTO provider_operations(operation_key) VALUES(%s) ON CONFLICT DO NOTHING',(key,))
            operation=db.execute('SELECT attempts FROM provider_operations WHERE operation_key=%s FOR UPDATE',(key,)).fetchone()
            if operation['attempts']>=3:return False
            allowed=consume_limit(db,'provider:'+provider,limit,86400)
            if allowed:db.execute('UPDATE provider_operations SET attempts=attempts+1 WHERE operation_key=%s',(key,))
        if not allowed:raise ProviderUnavailable('PROVIDER_DAILY_BUDGET_EXHAUSTED')
        return True

    def create_admin(self, username, password, region_code, role='city_admin'):
        if len(password) < 14 or not 3 <= len(username) <= 100:
            raise ValueError('USERNAME_OR_PASSWORD_TOO_SHORT')
        with self.connect() as db:
            user_id = uuid4()
            db.execute('INSERT INTO admin_users(id,username,password_hash,region_code,role) VALUES(%s,%s,%s,%s,%s)',
                       (user_id, username, PASSWORDS.hash(password), region_code, role))
            self.audit(db, user_id, 'ADMIN_CREATED', {'region_code':region_code}, 'system_cli')
        return user_id

    def set_region(self, feature, *, approve=False):
        if region_check(feature, -7.98, 112.63) != 'inside':
            raise ValueError('INVALID_PILOT_REGION')
        digest = hashlib.sha256(json.dumps(feature, sort_keys=True, separators=(',', ':')).encode()).hexdigest()
        with self.connect() as db:
            db.execute("UPDATE regions SET geometry=%s,approved_sha256=%s,updated_at=now() WHERE code='35.73'",
                       (Jsonb(feature), digest if approve else None))
            self.audit(db, None, 'REGION_CONFIGURED', {'sha256':digest,'approved':approve}, 'system_cli')
        return digest

    def set_settings(self, changes, actor='system_cli'):
        with self.connect() as db:
            cfg = db.execute("SELECT value FROM app_settings WHERE key='service' FOR UPDATE").fetchone()['value']
            cfg.update(changes)
            if cfg.get('public_intake') and not cfg.get('live_gate_passed'):
                raise ValueError('LIVE_GATE_REQUIRED')
            db.execute("UPDATE app_settings SET value=%s WHERE key='service'", (Jsonb(cfg),))
            self.audit(db, None, 'SETTINGS_CHANGED', {'keys':sorted(changes)}, actor)

    def allow_new_report(self, db, source):
        return consume_limit(db, 'reports:'+source['account_id']+':'+source['sender_ref'],
                             int(os.environ.get('SIGAPI_REPORTS_PER_DAY', '5')), 86400)

    def safety_reply(self,text,report,source):
        from backend.safety import advice
        from backend.facts import threat_claim
        high=threat_claim([{'id':str(source['id']),'text':source['payload'].get('text','')}])['level']=='high'
        if high or (report and report['status']!='complete'):
            text+=' '+advice(high_risk=high,contact=self.config.read().get('emergency_contact'))
        return text[:1350]

    def admit(self, account, sender, message_id):
        cfg=self.config.read()
        team=set(filter(None,os.environ.get('SIGAPI_TEST_SENDERS','').split(',')))
        if not cfg.get('public_intake') and sender not in team:
            raise HTTPException(403,'PUBLIC_INTAKE_DISABLED')
        with self.connect() as db:
            db.execute('SELECT pg_advisory_xact_lock(hashtextextended(%s,0))',('admission:'+account+':'+message_id,))
            old=db.execute('SELECT sender_ref FROM intake_admissions WHERE account_id=%s AND message_id=%s',(account,message_id)).fetchone()
            if old:
                if old['sender_ref']!=sender:raise HTTPException(422,'EVENT_IDENTITY_CONFLICT')
                return
            allowed=consume_limit(db,'messages:'+account+':'+sender,int(os.environ.get('SIGAPI_MESSAGES_PER_WINDOW','20')),600)
            pending=db.execute("SELECT count(*) n FROM jobs WHERE state IN ('pending','running')").fetchone()['n']
            if allowed and pending<500:
                db.execute('INSERT INTO intake_admissions(account_id,message_id,sender_ref) VALUES(%s,%s,%s)',(account,message_id,sender))
        if not allowed:raise HTTPException(429,'SENDER_RATE_LIMITED')
        if pending>=500:raise HTTPException(503,'QUEUE_CAPACITY_REACHED')

    def claim_outbox(self,accounts,senders,*,public_reporters=False):
        approved=[d['number'] for d in self.destinations().values() if d['account_id'] in accounts]
        with self.connect() as db:
            approved += [r['number'] for r in db.execute('SELECT number FROM destinations WHERE active AND authorized AND account_id=ANY(%s)',(accounts,)).fetchall()]
        return super().claim_outbox(accounts,list(set(senders+approved)),public_reporters=public_reporters)

    def start_send(self,id,token):
        with self.connect() as db:
            row=db.execute('SELECT * FROM outbox WHERE id=%s',(id,)).fetchone()
        if not row or row['audience']!='configuration_test':return super().start_send(id,token)
        with self.connect() as db:
            row=db.execute('SELECT * FROM outbox WHERE id=%s FOR UPDATE',(id,)).fetchone()
            if row['state']!='leased' or row['lease_token']!=token:return False
            dest=db.execute('SELECT * FROM destinations WHERE id::text=%s',(row['destination_id'],)).fetchone()
            valid=bool(dest and dest['active'] and dest['authorized'] and dest['version']==row['destination_version']
                       and dest['number']==row['sender_ref'] and dest['account_id']==row['account_id'])
            if not valid:
                db.execute("UPDATE outbox SET state='cancelled',reason='DESTINATION_CHANGED' WHERE id=%s",(id,));return False
            if not consume_limit(db,'test-send:'+row['sender_ref'],5,600):
                db.execute("UPDATE outbox SET state='pending',available_at=now()+interval '10 minutes' WHERE id=%s",(id,));return False
            started=bool(db.execute("UPDATE outbox SET state='sending',lease_until=now()+interval '60 seconds' WHERE id=%s AND lease_until>now() RETURNING id",(id,)).fetchone())
            if started:self.audit(db,dest['id'],'TEST_SEND_ADMITTED',{'outbox_id':str(id)})
            return started

    def finish_send(self,id,token,message_id=None):
        with self.connect() as db:
            row=db.execute('SELECT * FROM outbox WHERE id=%s',(id,)).fetchone()
        if not row or row['audience']!='configuration_test':return super().finish_send(id,token,message_id)
        with self.connect() as db:
            changed=bool(db.execute("UPDATE outbox SET state=%s,provider_message_id=%s WHERE id=%s AND lease_token=%s AND state='sending' RETURNING id",('sent' if message_id else 'unknown',message_id,id,token)).fetchone())
            if changed:self.audit(db,None,'TEST_SEND_RESULT',{'outbox_id':str(id),'state':'sent' if message_id else 'unknown'})
        return changed

    def track_reply(self,db,source,command):
        parts=command.split()
        owner=(source['account_id'],source['sender_ref'])
        if len(parts)>2:return 'Laporan tidak tersedia untuk nomor ini.'
        if len(parts)==2:
            token=parts[1].lower()
            import re
            if not re.fullmatch(r'[a-f0-9-]{8,36}',token):return 'Laporan tidak tersedia untuk nomor ini.'
            rows=db.execute('SELECT * FROM reports WHERE account_id=%s AND sender_ref=%s AND id::text LIKE %s ORDER BY created_at DESC LIMIT 2',owner+(token+'%',)).fetchall()
            if len(rows)!=1:return 'Laporan tidak tersedia untuk nomor ini.'
        else:
            rows=db.execute('SELECT * FROM reports WHERE account_id=%s AND sender_ref=%s ORDER BY created_at DESC LIMIT 5',owner).fetchall()
            if not rows:return 'Belum ada laporan milik nomor ini.'
            if len(rows)>1:return 'Laporan Anda: '+', '.join(str(r['id'])[:8]+' ('+r['status']+')' for r in rows)+'. Ketik TRACK ID untuk rincian.'
        report=rows[0];decision=(report['analysis'] or {}).get('decision',{})
        text='Laporan '+str(report['id'])[:8]+'. Data: '+report['status']+'. Pemeriksaan: '+decision.get('action','menunggu')+'.'
        if report['incident_id']:
            incident=db.execute('SELECT * FROM incidents WHERE id=%s',(report['incident_id'],)).fetchone()
            delivery=db.execute("SELECT audience,state,provider_message_id FROM outbox WHERE incident_id=%s AND incident_revision=%s AND audience<>'reporter' ORDER BY created_at",(incident['id'],incident['revision'])).fetchall()
            if delivery:
                sent=sum(r['state']=='sent' and bool(r['provider_message_id']) for r in delivery)
                text+=' Pengiriman '+str(sent)+'/'+str(len(delivery))+' tujuan memiliki receipt. '+', '.join(r['audience']+'='+r['state'] for r in delivery)+'.'
            else:text+=' Belum ada pengiriman ke tujuan.'
            from backend.public import verification_summary
            summary=verification_summary(db,incident['id'],incident['location_version'])
            text+=' Konfirmasi publik: '+summary['summary']+'. Klaim selesai: '+summary['solved_claim_status']+'.'
            if summary['solved_claimed_at']:text+=' Waktu klaim publik: '+summary['solved_claimed_at'].isoformat()+'.'
        else:text+=' Belum ada pengiriman atau konfirmasi publik.'
        return text[:1350]+' Pengiriman dan klaim publik bukan konfirmasi penanganan resmi.'
