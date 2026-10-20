# Inspect charts and geometry

Small invented fixtures for interface acceptance, not real-world observations.
Copy them into the project's `data/input` under fresh names before asking Planner
to inspect them. Existing run snapshots are not upgraded by copying new fixtures.

- `regions.csv`: six rows; region sums North 30, South 20, East 25, West 30;
  complete amount total 105. Count by region: North 2, South 2, East 1, West 1.
- `boundaries.geojson`: four WGS84 features; two polygon boundaries (North has a
  hole), one line and one point. Attributes are region and amount.

Describe inspection in Planner, review the actual proposed operations, and Execute.
Read-only inspection needs no write authorization. Results → Chart offers the ten
views and aggregation selection. Analyze verified CSV checks the recorded file
hash and computes complete bounded aggregates without workflow execution. Results
→ Map shows boundaries, line and point; selecting a feature shows attributes and
links to Table. Old point-only run snapshots do not acquire these new geometries.

For combined processing, ask to extract boundary attributes to a fresh CSV and sum
amount by region into another fresh CSV. These are writes: enable Allow writes,
review, Authorize and Execute. Each output must be fresh. Expected totals are
North 30, South 20, Road 0 and Station 5. CSV export intentionally drops geometry.

[Contracts, limitations and acceptance](../../docs/CHECKPOINT27_ANALYSIS_AND_LAYOUT.md).
