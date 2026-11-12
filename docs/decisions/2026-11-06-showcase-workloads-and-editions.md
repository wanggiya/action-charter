# Showcase workloads and Personal/Platform editions

Date: 2026-11-06. Direction set by the project owner; plan only.

Context: the owner named the real workloads the product should prove itself on and asked
how to split the software between personal use and a platform with background agents.

Decision:
- Four showcase workloads measure progress in every phase: **H** health data science
  (diabetes and other public health data), **E** data engineering (SHP/DWG/health data →
  usable PostgreSQL/PostGIS), **PA** policy analysis of governors and senators elected in
  the 2026 midterms (positions on rail, power grid, AI, data centres; maps and reports), **G**
  power-grid monitoring with anomaly reports.
- Two editions from one codebase: **Personal** (no background service; user-started work)
  and **Platform** (adds unattended background agents through registered automations).
  Edition = configuration profile + packaging.
- The health journey is the Phase 2 hero journey; PA is the Phase 4 multi-agent public
  demo with mandatory quote verification and neutrality rules; G is the first Platform
  automation (Phase 7–8), scoped to anomaly detection, not confirmed outages.
- PA sources are captured now as data collection, because campaign sites disappear after
  elections; this does not break the Phase 0 feature freeze.

Follow-up decisions (same day): PA covers **governors and senators first**, House later;
PA waits for Phases 3–4 (no freeze exception); DWG converter and grid region/data
**decided later** from listed options; **cloud models deferred** until both the Personal
package and the Platform edition exist — until then local/on-site models only.

Consequences: phase exit criteria in [WORKING_METHOD.md](../product-direction/WORKING_METHOD.md)
reference the workloads. Details, data sources, gap list and open decisions:
[SHOWCASE_WORKLOADS.md](../product-direction/SHOWCASE_WORKLOADS.md).
