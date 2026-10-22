"""Bounded own-chat outcome ranking. No model calls, execution or authority."""
import json
from typing import Annotated, Literal
from pydantic import BaseModel, ConfigDict, Field, TypeAdapter
from geoagent_harness.recipe_catalog.successful import _connection, contracts

LIMIT = 200
POLICY_VERSION = "own-chat-checks-v1"


class Observation(BaseModel):
    model_config = ConfigDict(extra='forbid', strict=True)
    operation_id: str = Field(pattern=r'^[a-z][a-z0-9_]{0,99}$')
    contract_sha256: str = Field(pattern=r'^[a-f0-9]{64}$')
    result: Literal['verified_pass', 'deterministic_check_failed']


OBSERVATIONS = TypeAdapter(Annotated[list[Observation], Field(max_length=20)])


def record_outcome(root, record):
    """Accept dispatch-bound terminal evidence; omit arguments, paths and rows."""
    basis = record.get('retention_basis') or {}
    if not record.get('conversation_id') or not record.get('execution_performed') or not record.get('finished_at'):
        return 'ineligible'
    if record.get('status') not in {'completed', 'validation_failed'}:
        return 'excluded_environment_or_interruption'
    operations = basis.get('operations') or []
    steps = record.get('steps') or []
    if not operations or len(operations) != len(steps):
        return 'incomplete'
    observations = []
    for operation, step in zip(operations, steps):
        if (operation['step_id'], operation['skill_id']) != (step.get('step_id'), step.get('skill_id')):
            return 'mismatched'
        passed = (step.get('validation_outcome') or {}).get('passed')
        # Untested completion, failed dispatch and advisory Critic prose are not evidence.
        if passed is True and step.get('status') in {'completed', 'validated_success'}:
            result = 'verified_pass'
        elif passed is False and step.get('status') == 'validation_failed':
            result = 'deterministic_check_failed'
        else:
            continue
        observations.append({'operation_id': operation['skill_id'], 'contract_sha256': operation['contract_sha256'], 'result': result})
    if not observations:
        return 'no_verified_checks'
    payload = json.dumps(observations, sort_keys=True)
    db = _connection(root)
    try:
        with db:
            db.execute('BEGIN IMMEDIATE')
            db.execute('CREATE TABLE IF NOT EXISTS outcome_rank_v1 (run_id TEXT PRIMARY KEY, conversation_id TEXT NOT NULL, payload TEXT NOT NULL)')
            previous = db.execute('SELECT conversation_id,payload FROM outcome_rank_v1 WHERE run_id=?', (record['run_id'],)).fetchone()
            if previous:
                if previous != (record['conversation_id'], payload):
                    raise ValueError('Outcome evidence changed')
                return 'unchanged'
            if db.execute('SELECT COUNT(*) FROM outcome_rank_v1').fetchone()[0] >= LIMIT:
                return 'full'
            db.execute('INSERT INTO outcome_rank_v1 VALUES (?,?,?)', (record['run_id'], record['conversation_id'], payload))
    finally:
        db.close()
    return 'recorded'


def recommendations(root, conversation_id, eligible):
    """Current-contract evidence only. Empty evidence preserves baseline ordering."""
    path = root / 'workflow-state' / 'successful-workflows.sqlite3'
    if not path.exists():
        return []
    db = _connection(root)
    try:
        exists = db.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name='outcome_rank_v1'").fetchone()
        rows = db.execute('SELECT payload FROM outcome_rank_v1 WHERE conversation_id=? ORDER BY run_id LIMIT ?', (conversation_id, LIMIT)).fetchall() if exists else []
    finally:
        db.close()
    current = contracts(root)
    totals = {}
    for (payload,) in rows:
        if len(payload) > 32000:
            raise ValueError('Outcome evidence exceeds limit')
        try:
            observations = [item.model_dump() for item in OBSERVATIONS.validate_json(payload)]
        except ValueError:
            raise ValueError('Stored outcome evidence is invalid; use baseline ranking') from None
        for observation in observations:
            identity = observation['operation_id']
            if identity not in eligible or current.get(identity, {}).get('contract_sha256') != observation['contract_sha256']:
                continue
            count = totals.setdefault(identity, [0, 0])
            count[0 if observation['result'] == 'verified_pass' else 1] += 1
    result = [{'operation_id': key, 'verified_passes': value[0], 'check_failures': value[1],
               'score': round((value[0] - value[1]) / (value[0] + value[1] + 4), 4),
               'contract_sha256': current[key]['contract_sha256'],
               'basis': 'Same chat, current operation contract, recorded deterministic checks; not proof for new data'} for key, value in totals.items()]
    return sorted(result, key=lambda item: (-item['score'], item['operation_id']))[:5]


def reset(root, conversation_id):
    """Delete derived ranking metadata for this chat; preserve durable runs."""
    db = _connection(root)
    try:
        with db:
            exists = db.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name='outcome_rank_v1'").fetchone()
            if exists:
                db.execute('DELETE FROM outcome_rank_v1 WHERE conversation_id=?', (conversation_id,))
    finally:
        db.close()


def rank_recipes(recipes, words, items):
    """Evidence breaks relevance ties only, never overrides the request match."""
    import re
    scores = {item['operation_id']: item['score'] for item in items}
    def key(recipe):
        relevant = len(words & set(re.findall(r'[a-z]{3,}', recipe.name.casefold()+' '+recipe.description.casefold())))
        score = sum(scores.get(step.skill, 0) for step in recipe.steps) / max(len(recipe.steps), 1)
        return (-relevant, -score, recipe.id)
    return sorted(recipes, key=key)


def ranking_receipt(recipes, words, items):
    """Explain the exact supplied ordering, without claiming model adoption."""
    recipes = list(recipes)
    baseline = [r.id for r in rank_recipes(recipes, words, [])[:5]]
    ranked = [r.id for r in rank_recipes(recipes, words, items)[:5]]
    return {'policy_version': POLICY_VERSION, 'baseline_recipe_ids': baseline,
            'supplied_recipe_ids': ranked, 'recipe_order_changed': baseline != ranked,
            'model_adoption': 'not_measured', 'authority_granted': False}
