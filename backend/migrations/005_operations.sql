CREATE TABLE service_heartbeats(service text PRIMARY KEY,last_seen timestamptz NOT NULL DEFAULT now(),details jsonb NOT NULL DEFAULT '{}');
ALTER TABLE provider_operations ADD COLUMN created_at timestamptz NOT NULL DEFAULT now();
INSERT INTO schema_versions(version) VALUES(5);
