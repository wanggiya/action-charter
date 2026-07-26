# inspect_vector

Status: implemented in Checkpoint 1.

## Contract

Input: an existing `.geojson`, `.gpkg`, or `.shp` file canonically located
beneath the configured read-only input root.

Output: validated JSON containing source, driver, layer names, CRS, geometry
type, feature count, fields, and extent.

The implementation uses GeoPandas and pyogrio APIs directly. It exposes no
command parameter, shell, SQL, network operation, write, overwrite, or delete.

