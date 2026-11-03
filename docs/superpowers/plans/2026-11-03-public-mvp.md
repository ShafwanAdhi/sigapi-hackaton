# SIGAPI Public MVP Implementation Plan

Approved scope: implement the user's 3 November 2026 completion plan.

## Goal and architecture

Complete public WhatsApp reporting, multimodal evidence analysis, controlled
distribution, GPS confirmations, owner-only TRACK, and the five-menu Admin Kota
dashboard. Pilot: Kota Malang (35.73). Preserve existing React branding.

Deploy a fresh isolated stack at https://sigapi.shafwan.digital on the existing
Ubuntu 24.04 VPS. Existing host Nginx/Certbot proxies 127.0.0.1:8084. Docker
contains PostgreSQL, internal/web APIs, workers, OpenClaw and static frontends.
Keep gateway/internal/database private; do not upgrade host Node or disturb other
applications. Use a compatible pinned Node 24 container. Initial service memory
budget: 2 GiB. No local reports, media or WhatsApp sessions migrate to the VPS.

## Tasks

1. Preserve existing changes in a reviewed checkpoint, pull main into the feature
   branch, run Python/Node/frontend/browser baseline with a separate test database,
   and remove Windows-only runtime/test paths.
2. Add versioned database migrations for regions, admins, Argon2 passwords,
   persistent sessions, scoped access, CSRF, login throttling, destinations and
   configuration audit. CLI provisions admins; no public registration.
3. Complete public intake with trusted transport identity, dynamic reporter replies,
   independently authorized forwarding, unconditional takeover of handled DMs,
   quotas (20 messages/10 minutes/sender, five new reports/day), bounded spool
   (500 messages/256 MB), and explicit provider budgets. Separate active draft
   selection from report lifecycle. Add sourced cross-evidence consistency,
   conservative holds, fixed sourced safety advice, 60-minute FIRMS refresh,
   versioned reevaluation, per-frame isolation and orphan candidate filtering.
   Destinations use UUID/configuration version; fan out to all active category and
   region matches. Recheck policy, revision and consent at send admission. Unknown
   sends require audited reconciliation, never automatic retry.
4. Wire real public React to GET /api/laporan/{slug} and multipart POST
   /api/laporan/{slug}/verifications. Normal eligible distribution publishes a
   safe versioned projection; private escalation does not. Only approved sanitized
   photo derivatives are public. Validate radius <=2000 m, 0<accuracy<=100 m,
   age<=60 s, future tolerance<=5 s, 2000-character description, optional decoded
   photo<=10 MB, request idempotency, location version, and atomic
   10 attempts/10 minutes/IP+slug throttling. Invalid+solved normalizes false.
   Technical failures create no verification event. Aggregate none/supporting_valid/
   supporting_invalid/disputed separately from claimed_solved. TRACK uses stored
   owner-scoped historical reports, actual deliveries, public evidence and claims.
   Preserve original anchors and contribution history across grouping changes.
5. Add separate React admin application with Overview, Laporan, Peta Kebakaran,
   Pihak Berwenang and Saluran MPA. All values are real API data. Support filters,
   scoped private media, evidence/grouping review, recheck, photo approval,
   destination management, authorized send tests and delivery reconciliation/audit.
6. Deploy /opt/sigapi with private volumes/secrets, HTTPS, fresh WhatsApp pairing,
   health/readiness, resource limits, backup/restore, rollback and explicit dry-run
   retention purge (seven days, including sensitive gateway files/logs). Build
   frontend/images outside VPS where feasible. Test other hosted apps remain
   healthy. Document operator runbook and record actual acceptance evidence.

## Acceptance and constraints

Use TDD for features and regressions. Run real PostgreSQL/local HTTP/Node tests,
frontend typecheck/build and Playwright. Cover duplicate input, restart, stale
workers, source corrections, revoked consent, destination edits, partial fan-out,
ambiguous send results, cross-region access, CSRF, public/private data separation,
historical TRACK ownership, GPS boundary values and stale forms.

Two authorized distinct outbound test contacts are not yet available. Local
fixture gates allow later implementation to proceed; live dispatch acceptance
remains pending. Keep public WhatsApp admission disabled until load controls and
real rehearsal pass. Do not send to institutions without explicit authorization.
Use coordinator chat for MPA initially; automatic Channel creation is excluded.
No authenticity percentages, model training, recurring firefighting progress or
CSV/PDF exports. Reverse image search, satellite hotspots and public contributions
are supporting evidence, never proof of authenticity or official closure.

## Execution

Execute sequentially in the current feature checkout, preserving private local
runtime paths. Record decisions/test commands in this plan's ignored execution
ledger. Review the whole change with a fresh reviewer before final completion.
