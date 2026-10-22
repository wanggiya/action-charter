"""Shared explicit discovery service for non-conversational entry points."""
from pathlib import Path
from .source import relative_path


def discover_dataset(root,path,delimiter=None):
    from geoagent_harness.interface_api.inspection_policy import bounded_read,probe_action,source_skill
    path=relative_path(path,'input')
    if source_skill(path) is None:raise ValueError('Unsupported discovery format')
    delimiter=delimiter or ('\t' if path.lower().endswith('.tsv') else ',')
    if delimiter not in {',','\t'}:raise ValueError('Choose comma or tab')
    root=Path(root).resolve(strict=True);action=probe_action(path)
    if action=='snapshot':
        source=bounded_read(root,action=action,path=path)
        return bounded_read(root,action='inspect',path=path,source_sha256=source['source_sha256'])
    return bounded_read(root,action=action.replace('_probe','_discover'),path=path,delimiter=delimiter)
