CREATE TABLE IF NOT EXISTS schema_versions(version integer PRIMARY KEY, installed_at timestamptz NOT NULL DEFAULT now());
CREATE TABLE IF NOT EXISTS incidents(id uuid PRIMARY KEY, created_at timestamptz NOT NULL DEFAULT now());
CREATE TABLE IF NOT EXISTS reports(
 id uuid PRIMARY KEY, account_id text NOT NULL, sender_ref text NOT NULL, conversation_id text NOT NULL,
 revision integer NOT NULL DEFAULT 1, status text NOT NULL DEFAULT 'draft', active boolean NOT NULL DEFAULT true,
 state jsonb NOT NULL, analysis jsonb, analysis_revision integer,
 created_at timestamptz NOT NULL DEFAULT now(), updated_at timestamptz NOT NULL DEFAULT now());
CREATE UNIQUE INDEX IF NOT EXISTS one_active_draft ON reports(account_id,sender_ref) WHERE active;
CREATE TABLE IF NOT EXISTS media(
 id uuid PRIMARY KEY, account_id text NOT NULL, sender_ref text NOT NULL, provider_message_id text NOT NULL,
 slot integer NOT NULL CHECK(slot BETWEEN 0 AND 9), kind text NOT NULL CHECK(kind IN ('image','video')),
 sha256 text NOT NULL, storage_key text NOT NULL, content_type text NOT NULL,
 validation_status text NOT NULL DEFAULT 'pending', reason text,
 created_at timestamptz NOT NULL DEFAULT now(), UNIQUE(account_id,sender_ref,provider_message_id,slot));
CREATE TABLE IF NOT EXISTS inbound_events(
 seq bigserial PRIMARY KEY, id uuid UNIQUE NOT NULL, account_id text NOT NULL, provider_message_id text NOT NULL,
 sender_ref text NOT NULL, conversation_id text NOT NULL, payload jsonb NOT NULL, report_id uuid REFERENCES reports,
 processed boolean NOT NULL DEFAULT false, created_at timestamptz NOT NULL DEFAULT now(),
 UNIQUE(account_id,provider_message_id));
CREATE TABLE IF NOT EXISTS jobs(
 id uuid PRIMARY KEY, event_seq bigint UNIQUE NOT NULL REFERENCES inbound_events,
 account_id text NOT NULL, sender_ref text NOT NULL, state text NOT NULL DEFAULT 'pending',
 lease_token uuid, lease_until timestamptz, attempts integer NOT NULL DEFAULT 0,
 available_at timestamptz NOT NULL DEFAULT now(), reason text);
CREATE TABLE IF NOT EXISTS consent_events(
 event_seq bigint PRIMARY KEY REFERENCES inbound_events, report_id uuid NOT NULL REFERENCES reports,
 allowed boolean NOT NULL, created_at timestamptz NOT NULL DEFAULT now());
CREATE TABLE IF NOT EXISTS outbox(
 id uuid PRIMARY KEY, event_seq bigint UNIQUE NOT NULL REFERENCES inbound_events, report_id uuid REFERENCES reports,
 account_id text NOT NULL, sender_ref text NOT NULL, text text NOT NULL,
 state text NOT NULL DEFAULT 'pending', lease_token uuid, lease_until timestamptz,
 provider_message_id text, reason text, created_at timestamptz NOT NULL DEFAULT now());
INSERT INTO schema_versions(version) VALUES(1) ON CONFLICT DO NOTHING;
