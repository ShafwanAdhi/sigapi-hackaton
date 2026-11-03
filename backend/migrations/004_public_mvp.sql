CREATE TABLE regions(
 code text PRIMARY KEY,name text NOT NULL,geometry jsonb,approved_sha256 text,
 snapshot jsonb,updated_at timestamptz NOT NULL DEFAULT now());
INSERT INTO regions(code,name) VALUES('35.73','Kota Malang');
CREATE TABLE app_settings(key text PRIMARY KEY,value jsonb NOT NULL);
INSERT INTO app_settings VALUES('service','{"distribution_enabled":false,"public_intake":false,"live_gate_passed":false}');
CREATE TABLE admin_users(
 id uuid PRIMARY KEY,username text UNIQUE NOT NULL,password_hash text NOT NULL,
 region_code text NOT NULL REFERENCES regions,role text NOT NULL DEFAULT 'city_admin'
 CHECK(role IN ('city_admin','system_admin')),active boolean NOT NULL DEFAULT true);
CREATE TABLE admin_sessions(
 token_hash text PRIMARY KEY,user_id uuid NOT NULL REFERENCES admin_users,
 csrf_token text NOT NULL,created_at timestamptz NOT NULL DEFAULT now(),
 last_seen timestamptz NOT NULL DEFAULT now(),expires_at timestamptz NOT NULL);
CREATE TABLE rate_limits(
 key text PRIMARY KEY,attempts integer NOT NULL,expires_at timestamptz NOT NULL);
CREATE TABLE destinations(
 id uuid PRIMARY KEY,region_code text NOT NULL REFERENCES regions,name text NOT NULL,
 number text NOT NULL,role text NOT NULL CHECK(role IN ('authority','community')),
 categories text[] NOT NULL DEFAULT ARRAY['forest_land','building'],
 account_id text NOT NULL DEFAULT 'default',active boolean NOT NULL DEFAULT false,
 authorized boolean NOT NULL DEFAULT false,version integer NOT NULL DEFAULT 1,
 address text NOT NULL DEFAULT '',invitation_url text NOT NULL DEFAULT '',
 updated_at timestamptz NOT NULL DEFAULT now());
ALTER TABLE reports ADD COLUMN region_code text REFERENCES regions DEFAULT '35.73';
ALTER TABLE reports ADD COLUMN lifecycle text NOT NULL DEFAULT 'open';
ALTER TABLE incidents ADD COLUMN region_code text REFERENCES regions DEFAULT '35.73';
ALTER TABLE incidents ADD COLUMN location_version integer NOT NULL DEFAULT 1;
ALTER TABLE outbox ADD COLUMN destination_version integer;
CREATE TABLE analysis_runs(
 id uuid PRIMARY KEY,report_id uuid NOT NULL REFERENCES reports,revision integer NOT NULL,
 input_seq bigint NOT NULL,result jsonb NOT NULL,created_at timestamptz NOT NULL DEFAULT now());
CREATE TABLE public_incidents(
 incident_id uuid PRIMARY KEY REFERENCES incidents,location_version integer NOT NULL,
 projection jsonb NOT NULL,photo_key text,published_at timestamptz NOT NULL DEFAULT now(),
 expires_at timestamptz NOT NULL DEFAULT now()+interval '7 days',withdrawn boolean NOT NULL DEFAULT false);
CREATE TABLE verification_events(
 id uuid PRIMARY KEY,request_id uuid NOT NULL,incident_id uuid NOT NULL REFERENCES incidents,
 location_version integer NOT NULL,choice text NOT NULL CHECK(choice IN ('valid','invalid')),
 latitude double precision NOT NULL,longitude double precision NOT NULL,
 accuracy_m double precision NOT NULL,gps_fix_at timestamptz NOT NULL,distance_m double precision NOT NULL,
 description text NOT NULL DEFAULT '',solved boolean NOT NULL DEFAULT false,
 photo_key text,payload_hash text NOT NULL,source text NOT NULL DEFAULT 'public_link',
 created_at timestamptz NOT NULL DEFAULT now(),UNIQUE(incident_id,request_id),
 CHECK(choice='valid' OR solved=false));
CREATE TABLE intake_admissions(
 account_id text NOT NULL,message_id text NOT NULL,sender_ref text NOT NULL,
 created_at timestamptz NOT NULL DEFAULT now(),PRIMARY KEY(account_id,message_id));
CREATE INDEX public_event_summary ON verification_events(incident_id,location_version,created_at);
INSERT INTO schema_versions(version) VALUES(4);
