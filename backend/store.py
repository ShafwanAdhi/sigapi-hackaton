"""PostgreSQL durable intake, ordered jobs, and fenced reply outbox."""

import json
import os
from pathlib import Path
from uuid import uuid4

import psycopg
from psycopg.rows import dict_row
from psycopg.types.json import Jsonb

from backend.conversation import advance, new_state


class Store:
    def __init__(self, dsn):
        if not dsn:
            raise ValueError('DATABASE_URL_REQUIRED')
        self.dsn = dsn

    def connect(self):
        return psycopg.connect(self.dsn, row_factory=dict_row, connect_timeout=5)

    def migrate(self):
        with self.connect() as db:
            db.execute("SELECT pg_advisory_xact_lock(76431002)")
            exists=db.execute("SELECT to_regclass('public.schema_versions') AS name").fetchone()['name']
            applied={row['version'] for row in db.execute('SELECT version FROM schema_versions').fetchall()} if exists else set()
            for migration in sorted((Path(__file__).parent / 'migrations').glob('*.sql')):
                version=int(migration.stem.split('_')[0])
                if version in applied:continue
                db.execute(migration.read_text(encoding='utf-8'))
                applied.add(version)

    def accept(self, event):
        with self.connect() as db:
            # Also serializes duplicate requests while checking media ownership.
            db.execute('SELECT pg_advisory_xact_lock(hashtextextended(%s,0))',
                       (json.dumps([event['account_id'], event['provider_message_id']]),))
            existing = db.execute('SELECT id,sender_ref FROM inbound_events WHERE account_id=%s AND provider_message_id=%s',
                                  (event['account_id'], event['provider_message_id'])).fetchone()
            if existing:
                if existing['sender_ref'] != event['sender_ref']:
                    raise ValueError('EVENT_IDENTITY_CONFLICT')
                return {'receipt_id': str(existing['id']), 'persistent_intake': True, 'mode': 'intake'}
            for ref in event.get('media_refs', []):
                row = db.execute('SELECT id FROM media WHERE id=%s AND account_id=%s AND sender_ref=%s AND provider_message_id=%s',
                                 (ref['id'], event['account_id'], event['sender_ref'], event['provider_message_id'])).fetchone()
                if row is None:
                    raise ValueError('MEDIA_NOT_OWNED')
            event_id = uuid4()
            seq = db.execute('''INSERT INTO inbound_events(id,account_id,provider_message_id,sender_ref,conversation_id,payload)
                                VALUES(%s,%s,%s,%s,%s,%s) RETURNING seq''',
                             (event_id, event['account_id'], event['provider_message_id'], event['sender_ref'],
                              event['conversation_id'], Jsonb(event))).fetchone()['seq']
            db.execute('INSERT INTO jobs(id,event_seq,account_id,sender_ref) VALUES(%s,%s,%s,%s)',
                       (uuid4(), seq, event['account_id'], event['sender_ref']))
        return {'receipt_id': str(event_id), 'persistent_intake': True, 'mode': 'intake'}

    def active_report(self, account, sender):
        with self.connect() as db:
            return db.execute('SELECT * FROM reports WHERE account_id=%s AND sender_ref=%s AND active', (account, sender)).fetchone()

    def save_analysis(self, report_id, revision, result):
        with self.connect() as db:
            return db.execute('UPDATE reports SET analysis=%s,analysis_revision=%s WHERE id=%s AND revision=%s',
                              (Jsonb(result), revision, report_id, revision)).rowcount == 1

    def claim_job(self, account=None):
        with self.connect() as db:
            row = db.execute('''SELECT j.* FROM jobs j WHERE
              (j.state='pending' OR (j.state='running' AND j.lease_until<now())) AND j.available_at<=now()
              AND (%s::text IS NULL OR j.account_id=%s)
              AND NOT EXISTS(SELECT 1 FROM jobs earlier WHERE earlier.account_id=j.account_id
                 AND earlier.sender_ref=j.sender_ref AND earlier.event_seq<j.event_seq
                 AND earlier.state NOT IN ('done','failed'))
              ORDER BY j.event_seq FOR UPDATE OF j SKIP LOCKED LIMIT 1''', (account, account)).fetchone()
            if not row:
                return None
            return db.execute("""UPDATE jobs SET state='running',lease_token=%s,
                 lease_until=now()+interval '3 minutes',attempts=attempts+1 WHERE id=%s RETURNING *""",
                              (uuid4(), row['id'])).fetchone()

    def process_job(self, job, validate):
        with self.connect() as db:
            source = db.execute('SELECT * FROM inbound_events WHERE seq=%s', (job['event_seq'],)).fetchone()
            refs = source['payload'].get('media_refs', [])
            media = [db.execute('SELECT * FROM media WHERE id=%s', (r['id'],)).fetchone() for r in refs]
        outcomes = [(row, validate(row)) for row in media]  # bounded decode outside report transaction
        with self.connect() as db:
            current = db.execute('SELECT * FROM jobs WHERE id=%s FOR UPDATE', (job['id'],)).fetchone()
            if current['state'] != 'running' or current['lease_token'] != job['lease_token']:
                return False
            if not db.execute('SELECT lease_until>now() AS valid FROM jobs WHERE id=%s', (job['id'],)).fetchone()['valid']:
                return False
            account, sender = source['account_id'], source['sender_ref']
            db.execute('SELECT pg_advisory_xact_lock(hashtextextended(%s,0))', (json.dumps([account, sender]),))
            for row, valid in outcomes:
                db.execute('UPDATE media SET validation_status=%s,reason=%s,content_type=%s WHERE id=%s',
                           ('valid' if valid else 'invalid', None if valid else 'DECODE_REJECTED',
                            valid if isinstance(valid, str) else row['content_type'], row['id']))
            report = db.execute('SELECT * FROM reports WHERE account_id=%s AND sender_ref=%s AND active FOR UPDATE', (account, sender)).fetchone()
            event = source['payload']
            command = event.get('text', '').strip().upper()
            created = False
            if command.startswith('TRACK'):
                reply = (self.track_reply(db,source,command) if hasattr(self,'track_reply') else
                         'TRACK belum tersedia pada tahap ini. Tidak ada informasi laporan orang lain yang ditampilkan.')
            elif command == 'STATUS':
                reply = ('Status data: ' + report['status'] + '; belum diverifikasi atau dipublikasikan.' if report
                         else 'Belum ada draft. Ketik REPORT untuk memulai laporan.')
                if report and getattr(self,'task3',False) and report['task3_enabled']:
                    reply=self.status_reply(db,report)
            elif not report and command in ('HALO', 'HAI', 'HI', '') and not refs and not event.get('location'):
                reply = 'Ketik REPORT untuk memulai, lalu kirim foto/video, pin lokasi kejadian dan KETERANGAN: penjelasan kejadian.'
            else:
                reset = report and command == 'BARU' and report['state'].get('pending_new')
                if reset:
                    db.execute('UPDATE reports SET active=false WHERE id=%s', (report['id'],))
                    report = None
                created = report is None
                if created:
                    if hasattr(self,'allow_new_report') and not self.allow_new_report(db,source):
                        db.execute('INSERT INTO outbox(id,event_seq,account_id,sender_ref,text) VALUES(%s,%s,%s,%s,%s)',
                                   (uuid4(),source['seq'],account,sender,'Batas laporan baru hari ini tercapai. Tidak ada laporan baru disimpan. Jika darurat, hubungi layanan darurat setempat.'))
                        db.execute('UPDATE inbound_events SET processed=true WHERE seq=%s',(source['seq'],))
                        db.execute("UPDATE jobs SET state='done',lease_until=NULL WHERE id=%s",(job['id'],))
                        return True
                    report = db.execute('''INSERT INTO reports(id,account_id,sender_ref,conversation_id,state)
                        VALUES(%s,%s,%s,%s,%s) RETURNING *''',
                                        (uuid4(), account, sender, source['conversation_id'], Jsonb(new_state()))).fetchone()
                input_event = dict(id=str(source['id']), text='' if created and command in ('REPORT','LAPOR','BARU') else event.get('text',''),
                                   location=event.get('location'), media=[str(row['id']) for row, valid in outcomes if valid])
                state, reply = advance(report['state'], input_event)
                if getattr(self, 'task3', False) and (created or report['task3_enabled']):
                    db.execute('UPDATE reports SET task3_enabled=true WHERE id=%s',(report['id'],))
                    if self.is_free_text(event.get('text','')):
                        state['questions_count'] = report['state'].get('questions_count',0)
                        reply = 'Pesan tersimpan; saya sedang membaca keterangan dan waktu kejadian.'
                facts = ['description','description_source','location','location_source','location_version',
                         'location_confirmed','confirmation_source','media_ids','consent_contact']
                changed = any(state.get(k) != report['state'].get(k) for k in facts)
                revision = report['revision'] + int(changed)
                db.execute('UPDATE reports SET state=%s,status=%s,revision=%s,updated_at=now() WHERE id=%s',
                           (Jsonb(state), state['status'], revision, report['id']))
                if changed and report.get('incident_id') and any(state.get(k)!=report['state'].get(k) for k in ('location','media_ids','description')):
                    db.execute('UPDATE public_incidents SET withdrawn=true WHERE incident_id=%s',(report['incident_id'],))
                if state['consent_record'] is not None:
                    db.execute('INSERT INTO consent_events(event_seq,report_id,allowed) VALUES(%s,%s,%s)',
                               (source['seq'], report['id'], state['consent_record']))
            report_id = report['id'] if report else None
            if getattr(self,'task3',False) and (report is None or created or report['task3_enabled']):
                reply=self.natural_reply(reply)
            if hasattr(self,'safety_reply'):reply=self.safety_reply(reply,report,source)
            prefix = f"[UJI] Laporan {str(report_id)[:8]}: " if report_id else '[UJI] '
            if os.environ.get('SIGAPI_RUN_MODE')=='pilot':prefix=prefix.replace('[UJI]','SIGAPI ·')
            db.execute('INSERT INTO outbox(id,event_seq,report_id,account_id,sender_ref,text) VALUES(%s,%s,%s,%s,%s,%s)',
                       (uuid4(), source['seq'], report_id, account, sender, prefix + reply))
            db.execute('UPDATE inbound_events SET processed=true,report_id=%s WHERE seq=%s', (report_id, source['seq']))
            if report_id and getattr(self,'task3',False):
                if command not in ('STATUS',) and not command.startswith('TRACK'):
                    self.on_intake(db,report_id,source['seq'])
            db.execute("UPDATE jobs SET state='done',lease_until=NULL WHERE id=%s", (job['id'],))
        return True

    def run_once(self, *, account=None, validate):
        job = self.claim_job(account)
        if not job:
            return False
        try:
            return self.process_job(job, validate)
        except Exception:
            with self.connect() as db:
                db.execute("""UPDATE jobs SET state=CASE WHEN attempts>=10 THEN 'failed' ELSE 'pending' END,
                    available_at=now()+interval '10 seconds',reason='PROCESSING_FAILED',lease_until=NULL
                    WHERE id=%s AND lease_token=%s AND state='running'""", (job['id'],job['lease_token']))
            raise

    def claim_outbox(self, accounts, senders):
        with self.connect() as db:
            db.execute("UPDATE outbox SET state='unknown',reason='SEND_LEASE_EXPIRED' WHERE state='sending' AND lease_until<now()")
            row = db.execute("""SELECT o.* FROM outbox o WHERE o.account_id=ANY(%s) AND o.sender_ref=ANY(%s)
                AND (o.state='pending' OR (o.state='leased' AND o.lease_until<now()))
                AND NOT EXISTS(SELECT 1 FROM outbox earlier WHERE earlier.account_id=o.account_id
                  AND earlier.sender_ref=o.sender_ref AND earlier.event_seq<o.event_seq
                  AND earlier.state IN ('pending','leased','sending'))
                ORDER BY o.event_seq FOR UPDATE OF o SKIP LOCKED LIMIT 1""", (accounts, senders)).fetchone()
            if not row:
                return None
            return db.execute("UPDATE outbox SET state='leased',lease_token=%s,lease_until=now()+interval '60 seconds' WHERE id=%s RETURNING *",
                              (uuid4(),row['id'])).fetchone()

    def start_send(self, id, token):
        with self.connect() as db:
            return db.execute("UPDATE outbox SET state='sending',lease_until=now()+interval '60 seconds' WHERE id=%s AND lease_token=%s AND state='leased' AND lease_until>now()", (id, token)).rowcount == 1

    def finish_send(self, id, token, message_id=None):
        with self.connect() as db:
            return db.execute("UPDATE outbox SET state=%s,provider_message_id=%s,reason=%s WHERE id=%s AND lease_token=%s AND state='sending'",
                              ('sent' if message_id else 'unknown', message_id, None if message_id else 'SEND_RESULT_UNKNOWN', id, token)).rowcount == 1
