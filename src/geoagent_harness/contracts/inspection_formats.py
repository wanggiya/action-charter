"""Qualified inspector input formats shared by discovery, policy and execution."""
from pathlib import PurePosixPath
from geoagent_harness.contracts.table_sources import TABLE_SUFFIXES

INSPECTOR_SUFFIXES = {
    'inspect_csv': TABLE_SUFFIXES,
    'inspect_vector': ('.geojson', '.gpkg', '.shp'),
    'inspect_raster': ('.tif', '.tiff'),
}

class InspectionFormatError(ValueError):
    """An inspector cannot consume the declared source format."""


def source_inspector(path):
    suffix = PurePosixPath(path).suffix.lower()
    return next((skill for skill, formats in INSPECTOR_SUFFIXES.items() if suffix in formats), None)


def validate_inspector_source(skill, arguments):
    if skill not in INSPECTOR_SUFFIXES or not isinstance(arguments.get('path'), str):
        return
    suffix = PurePosixPath(arguments['path']).suffix.lower()
    if suffix not in INSPECTOR_SUFFIXES[skill]:
        compatible = source_inspector(arguments['path'])
        remedy = f'Use {compatible} for this source.' if compatible else 'Choose a registered compatible source format.'
        raise InspectionFormatError(f'{skill} requires {" or ".join(INSPECTOR_SUFFIXES[skill])} input; '
                                    f'path has format {suffix or "(no extension)"}. {remedy} Nothing executed.')
