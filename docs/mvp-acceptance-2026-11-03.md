# SIGAPI deployment and acceptance record — 3 November 2026

## Deployed state

The isolated SIGAPI stack is deployed at https://sigapi.shafwan.digital, with
the city administrator application at `/admin/`. PostgreSQL, internal API,
gateway and workers have no published host ports. Only the edge proxy publishes
`127.0.0.1:8084`. Host Nginx configuration validation passed before reload, and
Certbot provisioned HTTPS with renewal enabled. The first certificate expires
1 February 2027.

The database is new. Local reports, media and WhatsApp sessions were not copied.
An initial city administrator was provisioned through stdin. Credentials remain
in the private local `.runtime/mvp-admin-credentials.txt` file. The sourced
Malang boundary was imported as an unapproved candidate. Public WhatsApp intake,
distribution and the live acceptance gate remain disabled. No third-party test
message was sent. A healthy gateway heartbeat does not prove WhatsApp pairing.

## Verified automated results

- Python: 144 tests, OK, one infrastructure test skipped because Docker CLI is
  absent inside the test container. Tests used a separate disposable PostgreSQL
  database, never the production DSN. Deployment topology had also been checked
  separately in the local environment.
  That local deployment-contract test was rerun successfully after deployment.
  One additional administrator regression passed separately: historical receipts
  and cancelled current destinations must not appear as completed fan-out.
- WhatsApp plugin: 15 Node tests passed, including restart/replay, handled-message
  takeover, trusted sender identity, public admission and ambiguous delivery.
- Public form state: three Node tests passed.
- Playwright: six public tests and one administrator navigation/login test passed.
  Live-form browser tests use HTTP fixtures; they do not prove provider delivery.
- Public and admin TypeScript checks and production builds passed. The final
  admin rebuild ran in a resource-limited Node 24 container after Windows ran out
  of memory. This is a documented exception to the preferred local/CI build;
  host Node was not changed.
- A 12-megapixel PNG was sanitized in a network-isolated container with both
  memory and memory+swap capped at 192 MiB. Peak process RSS was 138,912 KiB.
  This measures that isolated processing case, not arbitrary concurrent traffic.

Independent review identified seven important reliability defects. Fixes defer
delivery while input classification is pending, refresh unsent destination
versions, withdraw stale publication before extraction/recheck and on held
decisions, retain the incident GPS anchor, bound photo processing, persist file
deletion retries, and require current-revision delivery receipts. Backup partial
archives also receive cleanup. Follow-up review identified the pre-extraction
publication gap; that path now has an additional regression test.

## Verified deployment checks

HTTPS health and administrator pages returned 200. Real login and authenticated
overview/map/runtime requests returned 200. The session cookie is Secure.
Mutation without CSRF returned 403; authenticated logout returned 200. Public
`/internal/health`, `/.env`, and an unknown public incident returned 404.
Edge DNS resolution now refreshes Docker service addresses after API recreation.

All SIGAPI services with configured health checks became healthy. A steady-state
sample totalled approximately 1,045 MiB across the eight containers; configured
limits total 1,824 MiB. Gateway memory was approximately 650 MiB of its 768 MiB
limit. This is an idle/unpaired sample, not a load benchmark.

Encrypted database, media and gateway backups completed. An isolated temporary
database restore verified schema version 6 and the provisioned administrator,
then removed that temporary database. Production was not overwritten. A dedicated
daily systemd backup timer is enabled. The backup key has a private local copy;
backups currently remain on the same VPS, so off-host recovery is not verified.

The existing Bonjermgu, personal website, RAG Campus, Siparih and WaspadAI sites
all returned HTTP 200 after deployment. No commands intentionally stopped or
reconfigured those applications. This check establishes current availability,
not an assertion that unrelated processes never restarted.

## Remaining acceptance gates

1. Review and approve the sourced Malang boundary through the system CLI.
2. Pair the new WhatsApp gateway using the bot phone; do not reuse local sessions.
3. Obtain two explicitly authorized recipients and record their roles/consent.
4. Rehearse actual intake, provider evidence, fan-out, HTTPS phone GPS form,
   administrator actions and owner-only historical TRACK. Record actual provider
   receipts separately from fixture results.
5. Only after those checks pass, record the live gate and enable public admission
   plus the gateway's open DM policy. Keep outbound authorization independent.

The implementation is deployed for controlled acceptance. The public MVP is not
declared complete until the real rehearsal passes. Satellite hotspots, reverse
image search and public contributions remain evidence signals, not proof of an
incident or official confirmation of response.
