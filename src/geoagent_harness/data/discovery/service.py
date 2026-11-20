"""Shared explicit discovery service for non-conversational entry points."""
from pathlib import Path
from geoagent_harness.contracts.paths import relative_path


def discover_dataset(root,path,delimiter=None,*,card_context=False,options=None):
    if card_context:
        from geoagent_harness.data.discovery.context import prepare
        if options is not None and (not isinstance(options, dict) or set(options) - {'source_options','filters','missing_values'}):
            raise ValueError('Context options support source_options, filters and missing_values only')
        return prepare(Path(root).resolve(strict=True), path, allow_read=True,
                       delimiter=delimiter, **(options or {}))
    if options:
        raise ValueError('Context options require card_context')
    from geoagent_harness.workspaces.sandbox.inspection import bounded_read, probe_action, source_skill
    path=relative_path(path,'input')
    if source_skill(path) is None:raise ValueError('Unsupported discovery format')
    delimiter=delimiter or ('\t' if path.lower().endswith('.tsv') else ',')
    if delimiter not in {',','\t'}:raise ValueError('Choose comma or tab')
    root=Path(root).resolve(strict=True);action=probe_action(path)
    if action=='snapshot':
        source=bounded_read(root,action=action,path=path)
        return bounded_read(root,action='inspect',path=path,source_sha256=source['source_sha256'])
    return bounded_read(root,action=action.replace('_probe','_discover'),path=path,delimiter=delimiter)
