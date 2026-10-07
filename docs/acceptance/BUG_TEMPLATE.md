# Interface bug log

Use AC-UI-001, AC-UI-002, etc. Copy the entry below for each bug.

## AC-UI-001 — short observable problem

- Status: open / investigating / fixed / verified / deferred
- Case ID:
- Severity: S0 / S1 / S2 / S3
- Session ID and snapshot:
- Browser/version, viewport, model, write mode:
- Plan/run identifiers (filenames/digests, no secrets):
- Reproduction steps:
  1.
  2.
  3.
- Expected:
- Observed:
- Exact safe error text:
- Evidence path (screenshot, console message, API route/status, artifact):
- Reproduction rate: attempts / failures
- Layer suspected: UI / state / model / API / governance / adapter / configuration / unknown
- Fix reference:
- Regression check added (only where meaningful):
- Original-case retest:
- Related-case retest:
- Verified by / date:

Severity: S0 = authority escape or live-data mutation; stop the pass.
S1 = wrong input/output, misleading success, lost current plan, or blocked core journey.
S2 = recoverable interaction/layout/state problem with a workaround.
S3 = cosmetic, wording or minor convenience issue.

A fix remains "fixed" until the original reproduction is retested; then use "verified".
