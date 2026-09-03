# Dirty-vector spatial contract benchmark

This benchmark demonstrates deterministic detection of common vector-data
quality failures. `contract.yaml` is the versioned contract,
`BENCHMARK.json` records the exact expected failed checks, and `data/`
contains generated fixtures.

Regenerate the fixtures from the repository root with:

```bash
.venv/bin/python scripts/generate_spatial_contract_benchmark.py
```

The missing-CRS fixture uses an ESRI Shapefile without a `.prj` file because
GeoJSON readers commonly infer EPSG:4326 even when no explicit CRS member is
present.

The benchmark is read-only during assessment. A failed contract is an
expected deterministic result, not a workflow execution failure.
