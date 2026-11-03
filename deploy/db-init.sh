#!/bin/sh
set -eu
psql --username "$POSTGRES_USER" --dbname "$POSTGRES_DB" --set=app_password="$SIGAPI_DB_PASSWORD" <<'SQL'
SELECT format('CREATE ROLE sigapi_app LOGIN NOSUPERUSER NOCREATEDB NOCREATEROLE PASSWORD %L', :'app_password') \gexec
GRANT CONNECT ON DATABASE sigapi TO sigapi_app;
GRANT USAGE, CREATE ON SCHEMA public TO sigapi_app;
SQL
