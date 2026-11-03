# SIGAPI MVP operations

## Deployment profile

Host: `sigapi.shafwan.digital`, Ubuntu 24.04, one isolated Compose project in
`/opt/sigapi`. Host Nginx proxies loopback `8084`; only that port is published by
SIGAPI. PostgreSQL, gateway and internal API have no host ports. Existing apps
are not stopped or upgraded. Host Node is not used.

Public UI: `/laporan/{slug}`. Admin UI: `/admin/`. Public and admin web APIs run
separately from `/internal/*`, which the edge explicitly rejects.

The private `.env`, `.secrets/backup.key`, named database/media/gateway volumes,
QR codes and admin passwords never belong in Git. App SQL role is nonsuperuser.
The scheduler runs as root inside its restricted container to purge files owned
by the app and Node users; it has no host filesystem or Docker socket mounts.

Steady-state service limits total 1,824 MiB. These are resource limits, not an
availability or traffic guarantee. Provider concurrency and budgets remain
bounded; exhausted/failed providers produce unavailable/held results.

## Startup and shutdown

```bash
cd /opt/sigapi
docker compose up -d db
docker compose run --rm web python -m backend.manage migrate
docker compose run --rm gateway node /app/gateway-init.mjs
docker compose up -d internal web intake analysis scheduler gateway edge
docker compose ps
docker compose exec -T web python -m backend.manage status
```

Migrations are versioned and guarded by a PostgreSQL advisory lock. They do not
create sample reports, approve boundaries, enable dispatch, or mark live gates
passed. A successful health check proves only the component named by that check.
Gateway heartbeat proves plugin activity, not a paired WhatsApp account.

Stop only this project: `docker compose stop`. Do not use `down -v`: volumes
contain reports, media, configuration and WhatsApp credentials. Existing in-flight
sends become unknown when their lease expires and must be reconciled.

## Admin access

```bash
docker compose exec web python -m backend.manage admin-create --username admin
```

The command prompts privately for a password of at least 14 characters. Do not
put real passwords into command arguments, chat, screenshots or source files.
The initial account generated during deployment is recorded only in the user's
private local `.runtime/mvp-admin-credentials.txt`.

Sessions expire after eight hours or 30 minutes idle. Mutations require the
session's CSRF header and an allowed Origin. Logout invalidates the server session.
All report/media/destination queries enforce the admin's region on the server.

## Region and receivers

Import a sourced GeoJSON candidate without implicitly approving it:

```bash
docker compose exec web python -m backend.manage import-region --file /data/kota-malang.geojson --reason "Imported sourced candidate for operator review"
```

After an operator validates the actual boundary, repeat with `--approve` and a
specific reason. Approval binds the canonical geometry hash. OSM data is not an
official boundary certification. Distribution stays disabled without approval.

Manage authority and community recipients through the dashboard. Authorization
and activation are separate. Editing a recipient cancels its pending/leased
cards; admission also rechecks its UUID, version, account and number. Test sends
require an explicit authenticated operator action and never contain incident data.

Normal dispatch requires an eligible current decision. Public projections are
published in the same transaction. Private high-threat escalation does not
publish a projection by itself. Community and authority payloads stay separate;
only an authority payload may include the reporter's currently permitted contact.
Approved public photos are normalized derivatives; originals stay private.

## Fresh WhatsApp pairing and controlled rehearsal

Initial VPS state is fresh and public intake is disabled. No local session was
copied. Pair the dedicated number from a private operator terminal:

```bash
cd /opt/sigapi
docker compose stop gateway
docker compose run --rm gateway node /opt/openclaw/node_modules/openclaw/openclaw.mjs channels login --channel whatsapp
docker compose up -d gateway
```

Scan the QR using the dedicated phone's Linked Devices screen. Do not upload the
QR or auth directory. `SIGAPI_TEST_SENDERS` lists authorized rehearsal senders;
the backend enforces this even if an incoming message reaches the plugin.

Two distinct authorized recipient contacts remain necessary for real authority
and community dispatch acceptance. Configure them privately, review the boundary,
then enable distribution explicitly through the settings CLI. Rehearsal must
prove complete reporting, provider evidence, a conflict hold, a labelled threat
escalation, one eligible fan-out with actual provider receipts, HTTPS GPS submit,
and owner-only TRACK. Fixtures do not satisfy these live gates.

Only after recording the live evidence may an operator set `live_gate_passed`
and `public_intake` true. The gateway's DM policy must separately become `open`
with `allowFrom: ["*"]`; the outgoing authorization remains independent. Do not
edit the outgoing recipients into a wildcard. Default deployment keeps both
public admission and distribution disabled.

## Recovery and review

- Spool replay uses the same durable transport event ID. A 202 means event/job
  commit, not evidence verification or successful forwarding.
- Restarted workers reclaim leases. Stale revisions/tokens cannot commit results.
- Starting a new draft does not cancel a historical report's analysis.
- Ambiguous sends stay `unknown`. Inspect WhatsApp history before recording an
  actual receipt or confirming the message was not sent and requesting retry.
- Grouping and evidence reviews require an audit reason and current revision.
- Location corrections withdraw old public projections. Republished forms carry
  a new location version; stale submissions are rejected.
- FIRMS refreshes hourly. Failures retain the old snapshot and record unavailable;
  old coverage is never relabelled current. Newly covered held reports are requeued.

## Backup and restore

```bash
bash deploy/backup.sh
bash deploy/test-restore.sh backups/sigapi-YYYYMMDDTHHMMSSZ.dump.enc
```

Backup creates encrypted database, immutable-media and gateway-state archives plus
checksums. The key stays in `.secrets/backup.key`; keep a separate protected copy
off-host. The current single-host backup is not off-site disaster recovery.
The script briefly pauses only SIGAPI maintenance, then resumes it even on error.
Daily backups run through the dedicated `sigapi-backup.timer`.

Restore testing uses a newly created temporary database and drops only that
database. It never overwrites production. For actual recovery, stop SIGAPI,
restore database and corresponding media into fresh volumes, verify permissions,
and validate gateway auth or re-pair before starting intake. Do not start two
gateways against the same WhatsApp auth state.

## Retention

```bash
docker compose exec web python -m backend.manage purge
docker compose exec --user root web python -m backend.manage purge --apply
```

Without `--apply`, purge is a dry-run. Scheduled retention is explicitly enabled
in Compose; its due date survives restarts and purge never runs during startup.
An incident and related sensitive data expire seven days after their earliest
source. Media, public GPS, intake/spool, transcripts and stale sensitive logs are
included. Provider operation counters remain spent; purging does not renew quotas.
Configuration, credentials, users and approved receiver configuration remain.
Encrypted backup archives expire after seven days. Copies already received by
external WhatsApp recipients cannot be erased by this application.

## Verification

```bash
docker compose --profile test build tests
docker compose --profile test run --rm tests
docker compose --profile test stop test-db
```

The test database is a separate disposable service with no production data.
Frontend checks run in each app: `npm ci`, `npm run build`, then Playwright.
Browser fixtures prove client behavior; only a phone rehearsal proves real GPS
and WhatsApp account integration. Keep acceptance evidence private and redact
identities, credentials, media and provider responses before sharing.
