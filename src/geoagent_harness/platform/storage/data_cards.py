"""Bounded context cache in the existing workspace repository; no source reads."""
import hashlib
import json
import re

from geoagent_harness.contracts.data_cards import DataCard
from geoagent_harness.platform.storage.metadata import transaction

MAX_CARDS = 256


def cache_key(owner, path, selection, contract):
    if owner != 'explicit_discovery' and not re.fullmatch('[a-f0-9]{32}', owner):
        raise ValueError('Data Card owner must be an explicit-tool scope or this conversation')
    value = [owner, path, selection, contract]
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(',', ':')).encode()).hexdigest()


def read(root, *, owner, path, selection, contract):
    key = cache_key(owner, path, selection, contract)
    with transaction(root) as unit:
        raw = unit.records('data_cards_v1').get(key) if unit is not None else None
    if raw is None:
        return None
    try:
        if len(raw.encode()) > 16000:
            return None
        value = json.loads(raw)
        if (value.get('owner') != owner or value.get('path') != path
                or value.get('selection') != selection or value.get('contract') != contract):
            return None
        card = DataCard.model_validate(value['card'])
        return card.model_dump(mode='json') if card.source == path and card.source_sha256 else None
    except (ValueError, TypeError, KeyError, AttributeError):
        return None  # An invalid cache is never evidence or authority.


def store(root, *, owner, path, selection, contract, card):
    key = cache_key(owner, path, selection, contract)
    card = DataCard.model_validate(card)
    if card.source != path or not card.source_sha256:
        raise ValueError('Only source-bound cards can be retained')
    value = json.dumps(dict(owner=owner, path=path, selection=selection, contract=contract,
                            card=card.model_dump(mode='json')), separators=(',', ':'))
    if len(value.encode()) > 16000:
        raise ValueError('Data Card cache entry exceeds its budget')
    with transaction(root, write=True) as unit:
        records = unit.records('data_cards_v1')
        records.ensure()
        if records.get(key) is None and records.count() >= MAX_CARDS:
            # Cache entries are reconstructible. Never prune chat/history/approvals.
            oldest = records.entries(limit=MAX_CARDS)[-1]
            records.delete(oldest.key)
        records.put(key, value, owner=owner)
