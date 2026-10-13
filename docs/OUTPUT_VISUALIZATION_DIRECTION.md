# Output visualization and public demo — planned

Current delivery includes bounded table previews and input → operation → result cards with
arrows. A planned result is labeled separately from a recorded outcome. Step dependencies
are displayed from reviewed data, not inferred execution order. Interactive maps and chart
selection are not implemented by this follow-up.

## Proposed checkpoint 27 slice, before release/demo preparation

| Output contract | Visualization | Acceptance |
| --- | --- | --- |
| Verified CSV table | Existing bounded table, numeric bar/line chart and histogram | Explicit columns/aggregation, bounded rows, null handling and clear sample/truncation label; no invented values |
| Verified vector data | 2D map and attribute table | Explicit CRS conversion, bounded features/bounds, safe geometry handling, original source/digest link; no external tile requests by default |
| Verified raster metadata | Bounds/CRS/statistics first; bounded raster thumbnail where supported | Nodata/scale legend and sampling labeled; incompatible raster reported clearly |
| Multi-step outcome | Expandable provenance sequence and intermediate preview selector | Distinguish planned versus produced outputs, actual dependencies and failed/skipped steps |

Visualizations are read-only views of verified artifacts, not a new execution channel.
Implement typed backend preview contracts and resource limits before selecting a rendering
library. No live database access or dependency installation is implied by these proposals.

## LinkedIn demo preparation

Use public/synthetic CSV and GeoJSON fixtures. Demonstrate inspect → transform → authorize
→ execute → independent validation → output view, then a restart showing durable recovery.
Add one extension-discovery/test/install scene that distinguishes candidates from executable
operations. Record only after manual acceptance. Exclude credentials, private filenames,
conversation content and model/service configuration. Prepare a short script, expected outputs,
capability/limitation notes and screenshots/video; publishing remains the operator's decision.
