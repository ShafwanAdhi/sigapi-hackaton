#!/bin/bash
set -euo pipefail
cd "$(dirname "${BASH_SOURCE[0]}")/.."
test "$(pwd -P)" = /opt/sigapi || { echo 'Unexpected project directory'; exit 1; }
umask 077
test -s .secrets/backup.key
mkdir -p backups
stamp=$(date -u +%Y%m%dT%H%M%SZ)
prefix="backups/sigapi-$stamp"
# Pause only SIGAPI maintenance while taking its immutable-media backup.
docker compose stop scheduler >/dev/null
cleanup() {
  rm -f -- "$prefix.dump.enc.part" "$prefix.media.tar.gz.enc.part" "$prefix.gateway.tar.gz.enc.part"
  docker compose up -d scheduler >/dev/null
}
trap cleanup EXIT
docker compose exec -T db pg_dump -U sigapi_owner --format=custom sigapi |
  openssl enc -aes-256-cbc -pbkdf2 -salt -pass file:.secrets/backup.key -out "$prefix.dump.enc.part"
docker compose run --rm --no-deps --user root --entrypoint tar web -C /data -czf - media |
  openssl enc -aes-256-cbc -pbkdf2 -salt -pass file:.secrets/backup.key -out "$prefix.media.tar.gz.enc.part"
docker compose run --rm --no-deps --entrypoint tar gateway -C /gateway -czf - state |
  openssl enc -aes-256-cbc -pbkdf2 -salt -pass file:.secrets/backup.key -out "$prefix.gateway.tar.gz.enc.part"
for kind in dump media.tar.gz gateway.tar.gz; do
  mv "$prefix.$kind.enc.part" "$prefix.$kind.enc"
  sha256sum "$prefix.$kind.enc" > "$prefix.$kind.enc.sha256"
done
python3 - <<'PY'
from pathlib import Path
import re,time
root=Path('/opt/sigapi/backups').resolve()
for p in root.iterdir():
    if p.is_file() and p.resolve().parent==root and re.fullmatch(r'sigapi-\d{8}T\d{6}Z\.(dump|media\.tar\.gz|gateway\.tar\.gz)\.enc(\.sha256|\.part)?',p.name):
        if p.stat().st_mtime<time.time()-7*86400:p.unlink()
PY
printf 'Encrypted database, media and gateway backup completed: %s\n' "$stamp"
