"""Existing finite interface limits; no execution authority."""
import re

MAX_INTERFACE_REQUEST_BYTES = 65_536

MAX_INTERFACE_RECIPES = 200

MAX_INTERFACE_PLANS = 200

MAX_INTERFACE_PLAN_APPROVALS = 500

MAX_INTERFACE_EXECUTION_ATTEMPTS = 200

SAFE_RECIPE_FILENAME = re.compile(
    r"^[a-z0-9][a-z0-9_-]*\.[a-f0-9]{64}\.json$"
)

LOOPBACK_HOST = "127.0.0.1"

MAX_INTERFACE_OUTCOME_BYTES = 16_384

MAX_INTERFACE_DATA_RESOURCES = 500

MAX_INTERFACE_CRITIC_EVIDENCE = 200

INTERFACE_DATA_EXTENSIONS = {
    ".csv", ".geojson", ".gpkg", ".json", ".kml", ".parquet",
    ".shp", ".tif", ".tiff", ".tsv", ".xlsx", ".jsonl", ".ndjson",
}
