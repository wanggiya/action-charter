# Showcase workloads and editions

Recorded 2026-11-06 from an owner discussion. **Plan, not implemented.**
Decision: [2026-11-06 showcase workloads and editions](../decisions/2026-11-06-showcase-workloads-and-editions.md).

The owner chose four real workloads that every phase is measured against, and two
product editions. Data-source facts below are from general knowledge, **not
re-verified**; check licences, terms and availability before use (task G0/PA0/H0).

## Two editions, one codebase

| | **Personal** | **Platform** |
|---|---|---|
| Who | One person, own machine | Team or organisation, server (self-managed first; cloud later) |
| How work starts | The user asks (chat, Guided/Studio); runs while the app is open | Same, plus **unattended background agents**: schedules, file/table/feed events, API |
| Autonomy | L0–L1, plus L2 writes the user approves each time | Registered automations up to L2/L3 per [server autonomy design](SERVER_AUTONOMY_DESIGN.md); L4 stays human |
| Users / login | One, no login | Many, login (OIDC/LDAP), roles |
| Storage / queue | SQLite + files, in-process | PostgreSQL, job queue, worker pool |
| Model | Local (Ollama) or any allowed provider | Shared model gateway |
| Workloads | Health (H), engineering (E), policy analysis (PA), grid **on demand** (G1–G2) | All, plus grid **monitoring** (G3–G5) |

Rules:
- Same code; the edition is a configuration profile plus packaging (as in
  [EDITIONS_AND_INTERFACES.md](EDITIONS_AND_INTERFACES.md): Personal = laptop profile;
  Platform = team server and enterprise profiles). No `if personal:` branches.
- Personal has **no background service**; it is not a weaker governance mode.
- A recipe proven in Personal can be exported to Platform and registered as an
  automation there. This is the upgrade path.

## The four workloads

### H — Health data science (real-data test)

Purpose: prove analysis on sensitive-style data with local models and the egress gate.

| Data (check terms) | Use |
|---|---|
| UCI "Diabetes 130-US hospitals" (`diabetic_data.csv`, already used by `scripts/real_data_tests/`) | Encounter-level analysis; existing baseline |
| CDC PLACES (county/tract diabetes and other prevalence) + Census TIGER/Line boundaries | Area-level maps; joins by FIPS |
| CDC BRFSS (diabetes indicators) | Survey analysis, weights |
| Synthea (synthetic patients) | Patient-level pipelines with no privacy risk |
| Optional: MIMIC-IV (PhysioNet credentialed access) | Only with egress class `none` (local model); PhysioNet's rules restrict sending credentialed data to online services. Never in the repo |

What it must show: Data Card first; correct statistics (e.g. clustering by `patient_nbr`
— the 2026-11-01 run did not); plain-language report; county map; **small-cell
suppression** in outputs; model egress limited by data class.

### E — Data engineering to PostgreSQL/PostGIS

Purpose: "file in → usable, governed tables out".

| Task | Input | Steps | "Usable" means |
|---|---|---|---|
| E1 | Shapefile / GeoPackage / GeoJSON | Existing `inspect_vector` + `load_vector_to_postgis` | SRID set, geometries valid (`ST_IsValid`), spatial index, Data Card, optional GeoServer layer |
| E2 | **CAD: DXF and DWG** (new) | DWG → DXF conversion → read layers → **georeference** → normalise → load | As E1, plus layer/block mapping recorded and CRS confirmed |
| E3 | Health CSV (H data) | Validate → codebook decode → clean → create-only load → join geography by FIPS | Typed columns, keys, Data Card, suppression rules attached |

E2 specifics (not implemented today; no DWG/DXF code exists in `src/`):
- GDAL here has a DXF driver (read/write) and a CAD driver (limited DWG versions). Full
  DWG needs a converter: **LibreDWG** (GPL — run as a separate external program, do not
  link) or **ODA File Converter** (free but proprietary — user installs it; not bundled).
- CAD files often have **no CRS** or local engineering coordinates, mixed units
  (mm/m/ft), blocks, arcs and annotation. The Data Card must show "CRS unknown"; loading
  is **blocked** until a human supplies the CRS or control points; a deterministic check
  confirms the result lies in the expected area.
- Explode blocks, linearise arcs with recorded tolerance, closed polylines → polygons,
  keep layer name and handle as columns, keep text as a separate point table.

### PA — Policy analysis demo (public showcase)

Goal: for the officials elected in the **2026 midterms** (held 2026-11-03) — governors,
senators, then House members if feasible — extract stated positions on **railroads,
power grid, AI, data centres** and other development topics from their official
material, then produce maps and reports.

Why it fits: public data, so later (once cloud models are considered, after Phases 5 and
7) the egress gate could allow a stronger cloud model here while health data stays
local — one platform showing both policies. Until then PA uses local/on-site models. It also suits
multi-agent mode (collector, extractor, verifier, cartographer) and process/outcome
workspaces.

Pipeline:
Scope (2026-11-06): **governors and senators only**; House later.

1. **PA0 Source survey.** Official and campaign websites, press releases, platform
   documents, speeches; for senate incumbents `congress.gov` (bills, statements). Winner lists
   from state election offices / certified results (certification runs into December;
   flag pending races). Boundaries: Census TIGER/Line states. (House, later: use the
   **districts used in 2026**; several states redrew mid-decade.) Avoid sources whose
   terms forbid scraping; respect `robots.txt`.
2. **PA1 Capture now (time-sensitive).** Campaign websites often disappear after an
   election. Archive sources **now** as data collection, outside the product (standard
   tools such as `wget`/browser save, or the Internet Archive). Keep a manifest: URL,
   capture time, SHA-256, licence/terms note. Store under `data/input/` (not in git).
   This does not break the Phase 0 feature freeze.
3. **PA2 Gold set.** The owner hand-labels ~50–100 statements (topic, stance, quote).
   Used in the Phase 1 benchmark to measure extraction accuracy.
4. **PA3 Document corpus capability** (new): HTML/PDF → text with page/offset, source
   hash, stored in the run workspace.
5. **PA4 Stance extraction with verification** (new): the model returns topic, stance
   (`supports` / `opposes` / `conditional` / `mentions_only` / `no_statement_found`),
   **verbatim quote** and source. Deterministic software checks the quote exists in the
   hashed source; unverifiable claims are dropped.
6. **PA5 Outputs:** state maps per topic, per-official evidence
   tables, method report with gold-set accuracy, model and date.

Neutrality and accuracy rules (required before anything is published):
- Only **stated** positions with quote and link; never infer from party or votes unless
  that is a separate, labelled analysis.
- `no_statement_found` is not opposition; say so on every map.
- Same procedure and sources for every official; record coverage gaps.
- Human review of every published stance (or all flagged ones plus a measured sample).
- No persuasion content, no ranking of people; state limitations and the date.

### G — Power grid monitoring (automation showcase, Platform edition)

Goal: keep grid data current automatically and report areas showing trouble.

Candidate public sources (check terms, keys and delay):
- **EIA hourly electric grid monitor (EIA-930)** via the EIA API (free key): demand,
  generation by fuel, interchange per balancing authority; updated hourly with delay.
- ISO/RTO feeds (CAISO, ERCOT, PJM, MISO, NYISO, ISO-NE, SPP); some need registration.
- Outages: **no free national real-time outage feed** is known. DOE EAGLE-I county
  outage data and DOE OE-417 disturbance reports are published with a delay; utility
  outage maps vary and their terms often forbid scraping. Commercial aggregators exist.
- Context: NWS weather alerts API (public).

Honest scope: the platform can **detect anomalies** (sudden demand drops, missing data,
interchange swings) and correlate them with weather alerts and later outage reports. It
**cannot confirm** an outage from these feeds alone, and is not an operational tool.
Alerts say "anomaly; possible causes …" with sources.

| Task | Edition | What |
|---|---|---|
| G0 | — | Source survey and terms; choose one region first (one ISO or a few balancing authorities) |
| G1 | Personal | On-demand ingest of one day → staging → Data Card → map |
| G2 | Personal | Deterministic anomaly rules (thresholds, gaps, seasonal baseline) with a test set from past events |
| G3 | Platform (Phase 7) | Scheduled hourly ingest; **the "runs unattended for a week" exit job** |
| G4 | Platform (Phase 8) | Registered automation at L1/L2: ingest, verify, detect, alert; idempotent per hour; circuit breaker on feed failure |
| G5 | Platform (Phase 8) | Weather/outage-report correlation; daily summary report |

Why it is a good first automation: clear goal, checkable result (schema, completeness,
rule output), contained (writes only its own staging tables), bounded, and it builds a
track record — all five conditions in the server autonomy design.

## Capabilities these require (gap list)

| Capability | Needed by | Exists? |
|---|---|---|
| CSV profile/clean/statistics/PostgreSQL load | H, E3 | Yes (diabetes pipeline) |
| Vector inspect + load to PostGIS, GeoServer publish | E1 | Yes |
| Data Card | all | Phase 2 |
| Small-cell suppression | H | No |
| CAD (DXF/DWG) import + georeferencing step | E2 | No |
| Governed web fetch (allowlisted domains, snapshot + hash) | PA, G | No |
| Document corpus (HTML/PDF text with offsets) | PA | No |
| Quote verification against source | PA | No |
| Map output (choropleth by state/county/district) | H, PA, G | Check; GeoServer publishing exists |
| Time-series ingest + anomaly rules | G | No |
| Scheduler, notifications, registered automations | G3–G5 | Phase 7–8 |

## Placement in the phases

| Phase | Workload work |
|---|---|
| 0 (now) | No new features. **PA1 capture sources** (data only). H0/G0/PA0 source and terms survey (docs only). |
| 1 | Benchmark tasks drawn from H, E1/E3, PA2 gold set, G1 one-day ingest; record E2/PA as baseline "unsupported" |
| 2 | **Hero journey = H** (diabetes + PLACES county map, plain language, clustering fixed); Data Card for all; E2 CAD import; suppression |
| 3 | PA3 document corpus, governed web fetch, in run workspaces |
| 4 | PA4–PA5 (governors + senators) as the **multi-agent showcase**; public demo |
| 5 | Personal package runs H, E, PA and G1–G2 end to end |
| 6 | External agents run one E or PA task through our governed tools |
| 7 | Platform edition; G3 is the unattended-week exit job. After this: consider cloud models (both editions exist) |
| 8 | G4–G5 registered automations; autonomy earned on track record |

## Owner decisions (2026-11-06)

| Topic | Decision |
|---|---|
| PA scope | **Governors and senators first** (state-level maps). House members later, only after the state-level demo works |
| PA timing | **Wait for Phases 3–4.** No feature-freeze exception. PA1 source capture (data only) still happens now |
| DWG converter | **Decide later.** Options listed below |
| Grid region and data | **Decide later.** Options listed below |
| Cloud models | **Deferred** until both editions exist (Personal package, Phase 5, and Platform with background agents, Phase 7). Until then PA uses local/on-site models; the gold set (PA2) measures whether that is good enough |

### Options: DWG conversion (decide before E2 starts, Phase 2)

| Option | Licence / cost | Pros | Cons |
|---|---|---|---|
| GDAL CAD driver only (already installed) | Open source (MIT/X) | No extra tool | Supports only some older DWG versions; partial entities |
| LibreDWG (`dwg2dxf`) | GPL-3; run as a separate program, never linked or bundled into the Apache-2.0 code | Open source; scriptable; offline | Coverage of newer DWG versions and complex entities varies |
| ODA File Converter | Free download, proprietary licence; user installs it | Broad DWG version support | Not redistributable; licence terms must be checked for commercial/server use |
| Ask users for DXF export | None | Simplest; GDAL DXF driver reads it well | Pushes work to the user; not "full DWG" |
| Commercial SDK (ODA Teigha membership, others) | Paid | Best fidelity | Cost; only if a paying customer needs it |

Whichever is chosen sits behind one "CAD converter" interface so it can be swapped, and
the converter name/version is recorded in evidence.

### Options: grid data (decide before G0/G1)

| Option | Coverage | Access | Notes |
|---|---|---|---|
| EIA hourly grid monitor (EIA-930) via EIA API v2 | All US balancing authorities | Free API key | Demand, forecast, generation by fuel, interchange; delayed by about an hour or more; good national start |
| CAISO OASIS | California ISO | Public | Prices, load, renewables; detailed |
| ERCOT public data / API | Texas | Free registration for API | Load, generation, prices; frequent updates |
| PJM Data Miner 2 | Mid-Atlantic / Midwest | Free account, API key | Load, generation, prices |
| MISO, NYISO, ISO-NE, SPP public data | Their regions | Mostly public files/APIs | Formats differ per ISO |
| DOE EAGLE-I outage data | County customers-out | Historical releases, delayed | Best for outage history/correlation, not live alerts |
| DOE OE-417 disturbance reports | National major events | Public, delayed | Event labels for validating anomaly rules |
| Utility outage maps | Single utility | Varies | Terms often forbid scraping; use only with permission |
| Commercial outage aggregators | National | Paid | Only if a customer pays for it |
| NWS weather alerts API | National | Public | Context for anomalies (storms, heat) |

Region choices: (a) national EIA-930 at balancing-authority level (simplest, one source),
(b) one ISO in depth (richer data, one format), (c) both: EIA-930 nationally + one ISO.
All candidates must be checked for terms, key requirements and delay before use.
