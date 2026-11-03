#!/bin/bash
set -euo pipefail
cd "$(dirname "${BASH_SOURCE[0]}")/.."
test "$(pwd -P)" = /opt/sigapi || exit 1
file=$(realpath -- "${1:?Supply encrypted database backup}")
[[ "$file" == /opt/sigapi/backups/sigapi-*.dump.enc ]] || { echo 'Backup path outside project'; exit 1; }
test -f "$file"
restore="sigapi_restore_$(date -u +%Y%m%d%H%M%S)_$RANDOM"
[[ "$restore" =~ ^sigapi_restore_[0-9_]+$ ]] || exit 1
docker compose exec -T db createdb -U sigapi_owner "$restore"
trap 'docker compose exec -T db dropdb -U sigapi_owner "$restore"' EXIT
openssl enc -d -aes-256-cbc -pbkdf2 -pass file:.secrets/backup.key -in "$file" |
  docker compose exec -T db pg_restore -U sigapi_owner --dbname "$restore" --no-owner --exit-on-error
docker compose exec -T db psql -U sigapi_owner -d "$restore" -Atc 'SELECT max(version) FROM schema_versions; SELECT count(*) FROM admin_users;'
printf 'Restore verified in isolated temporary database. Production was not overwritten.\n'
