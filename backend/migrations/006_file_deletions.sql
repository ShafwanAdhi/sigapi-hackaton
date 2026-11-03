CREATE TABLE file_deletions(storage_key text PRIMARY KEY,created_at timestamptz NOT NULL DEFAULT now());
INSERT INTO schema_versions(version) VALUES(6);
