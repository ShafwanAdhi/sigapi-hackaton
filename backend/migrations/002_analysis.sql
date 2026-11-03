ALTER TABLE reports ADD COLUMN IF NOT EXISTS task3_enabled boolean NOT NULL DEFAULT false;
ALTER TABLE reports ADD COLUMN IF NOT EXISTS latest_seq bigint NOT NULL DEFAULT 0;
ALTER TABLE reports ADD COLUMN IF NOT EXISTS facts jsonb NOT NULL DEFAULT '{}';
ALTER TABLE reports ADD COLUMN IF NOT EXISTS clarification_count integer NOT NULL DEFAULT 0;
ALTER TABLE incidents ADD COLUMN IF NOT EXISTS slug text UNIQUE;
ALTER TABLE incidents ADD COLUMN IF NOT EXISTS location jsonb;
ALTER TABLE incidents ADD COLUMN IF NOT EXISTS observed_at timestamptz;
ALTER TABLE incidents ADD COLUMN IF NOT EXISTS category text NOT NULL DEFAULT 'unknown';
ALTER TABLE incidents ADD COLUMN IF NOT EXISTS revision integer NOT NULL DEFAULT 1;
ALTER TABLE incidents ADD COLUMN IF NOT EXISTS pending_review boolean NOT NULL DEFAULT false;
ALTER TABLE incidents ADD COLUMN IF NOT EXISTS account_id text;
ALTER TABLE incidents ADD COLUMN IF NOT EXISTS basis jsonb NOT NULL DEFAULT '{}';
ALTER TABLE reports ADD COLUMN IF NOT EXISTS incident_id uuid REFERENCES incidents;
ALTER TABLE reports ADD COLUMN IF NOT EXISTS incident_basis jsonb;
CREATE TABLE IF NOT EXISTS analysis_jobs(
 id uuid PRIMARY KEY,report_id uuid NOT NULL REFERENCES reports,revision integer NOT NULL,input_seq bigint NOT NULL,
 kind text NOT NULL,state text NOT NULL DEFAULT 'pending',available_at timestamptz NOT NULL DEFAULT now(),
 lease_until timestamptz,lease_token uuid,attempts integer NOT NULL DEFAULT 0,reason text,
 created_at timestamptz NOT NULL DEFAULT now(),UNIQUE(report_id,revision,input_seq,kind));
CREATE TABLE IF NOT EXISTS evidence_results(
 id uuid PRIMARY KEY,report_id uuid NOT NULL REFERENCES reports,revision integer NOT NULL,input_seq bigint NOT NULL,
 kind text NOT NULL,evidence_key text NOT NULL,result jsonb NOT NULL,created_at timestamptz NOT NULL DEFAULT now(),
 UNIQUE(report_id,revision,input_seq,kind,evidence_key));
CREATE TABLE IF NOT EXISTS policy_decisions(
 id uuid PRIMARY KEY,report_id uuid NOT NULL REFERENCES reports,revision integer NOT NULL,input_seq bigint NOT NULL,
 result jsonb NOT NULL,created_at timestamptz NOT NULL DEFAULT now());
CREATE TABLE IF NOT EXISTS report_incident_matches(
 report_id uuid REFERENCES reports,incident_id uuid REFERENCES incidents,distance_m double precision,
 time_delta_s double precision,explanation jsonb,reviewed boolean NOT NULL DEFAULT false,
 PRIMARY KEY(report_id,incident_id));
CREATE TABLE IF NOT EXISTS audit_events(
 id uuid PRIMARY KEY,subject_id uuid,actor text NOT NULL,action text NOT NULL,details jsonb NOT NULL,
 created_at timestamptz NOT NULL DEFAULT now());
CREATE TABLE IF NOT EXISTS manual_reviews(
 id uuid PRIMARY KEY,report_id uuid REFERENCES reports,revision integer NOT NULL,evidence_key text NOT NULL,
 reason text NOT NULL,references_json jsonb NOT NULL,created_at timestamptz NOT NULL DEFAULT now());
CREATE TABLE IF NOT EXISTS provider_operations(
 operation_key text PRIMARY KEY,attempts integer NOT NULL DEFAULT 0,result jsonb);
CREATE TABLE IF NOT EXISTS report_fingerprints(
 report_id uuid REFERENCES reports,frame_key text NOT NULL,sha256 text NOT NULL,dhash text,
 PRIMARY KEY(report_id,frame_key));
CREATE TABLE IF NOT EXISTS provider_gates(
 provider text PRIMARY KEY,next_start timestamptz NOT NULL DEFAULT now(),flight_until timestamptz,owner uuid);
ALTER TABLE outbox ALTER COLUMN event_seq DROP NOT NULL;
ALTER TABLE outbox ADD COLUMN IF NOT EXISTS source_key text UNIQUE;
ALTER TABLE outbox ADD COLUMN IF NOT EXISTS audience text NOT NULL DEFAULT 'reporter';
ALTER TABLE outbox ADD COLUMN IF NOT EXISTS destination_id text;
ALTER TABLE outbox ADD COLUMN IF NOT EXISTS report_revision integer;
ALTER TABLE outbox ADD COLUMN IF NOT EXISTS input_seq bigint;
ALTER TABLE outbox ADD COLUMN IF NOT EXISTS incident_id uuid REFERENCES incidents;
ALTER TABLE outbox ADD COLUMN IF NOT EXISTS incident_revision integer;
ALTER TABLE outbox ADD COLUMN IF NOT EXISTS available_at timestamptz NOT NULL DEFAULT now();
CREATE TABLE IF NOT EXISTS delivery_events(
 id uuid PRIMARY KEY,outbox_id uuid UNIQUE NOT NULL REFERENCES outbox,incident_id uuid REFERENCES incidents,
 incident_revision integer NOT NULL,destination_id text NOT NULL,payload_kind text NOT NULL,
 report_id uuid NOT NULL REFERENCES reports,created_at timestamptz NOT NULL DEFAULT now(),
 UNIQUE(incident_id,incident_revision,destination_id,payload_kind));
CREATE INDEX IF NOT EXISTS analysis_pending ON analysis_jobs(state,available_at);
CREATE INDEX IF NOT EXISTS outbox_sender_order ON outbox(account_id,sender_ref,created_at);
INSERT INTO schema_versions(version) VALUES(2) ON CONFLICT DO NOTHING;
