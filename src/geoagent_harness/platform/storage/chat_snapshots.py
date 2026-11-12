"""Immutable chat snapshot encoding within an existing metadata transaction."""
import hashlib, json
from datetime import datetime, timezone
from geoagent_harness.platform.storage.sqlite import adapt_legacy as as_transaction


def _tables(db):
    db = as_transaction(db)
    db.records('chat_history_blobs_v1').ensure()
    db.records('chat_history_v1').ensure()

def _digest(value):return hashlib.sha256(json.dumps(value,sort_keys=True,separators=(',',':'),allow_nan=False).encode()).hexdigest()

def archive(db,state,*,kind=None,view=None):
    """Called inside the same transaction as a state/view write; identical payloads deduplicate."""
    db = as_transaction(db)
    if not state:return
    plan=state.get('planner_result');analysis=state.get('analytical_session')
    if not plan and not analysis and not view:return
    _tables(db)
    refs={}
    for key,value in [('planner_result',plan),('analytical_session',analysis),('view',view)]:
        if value is None:refs[key]=None;continue
        digest=_digest(value);encoded=json.dumps(value,separators=(',',':'),allow_nan=False)
        if len(encoded.encode())>2_000_000:raise ValueError('History item exceeds its saved-record budget')
        db.records('chat_history_blobs_v1').put(digest,encoded,ignore_existing=True);refs[key]=digest
    identity=state['conversation_id'];entry_id=_digest({'conversation_id':identity,'revision':state['revision'],**refs})
    if db.records('chat_history_v1').get(entry_id) is not None:return
    if db.records('chat_history_v1').count(owner=identity)>=128:raise ValueError('Chat history reached 128 distinct items; export/archive before adding more')
    last=db.records('chat_history_v1').entries(owner=identity,limit=1)
    prior=json.loads(last[0].content) if last else {}
    event_kind=kind or ('analysis' if refs['analytical_session'] and refs['analytical_session']!=prior.get('analytical_session') else 'workflow')
    summary=(view or {}).get('columns')
    summary=(' / '.join(summary)+' · '+view['view']) if summary else (analysis or {}).get('message','') if event_kind=='analysis' else (plan or {}).get('plan',{}).get('summary','Saved analysis')
    record={'id':entry_id,'conversation_id':identity,'revision':state['revision'],'kind':event_kind,'summary':str(summary)[:180],
        'recorded_at':datetime.now(timezone.utc).isoformat(),'message_count':len(state.get('messages',[])),**refs}
    db.records('chat_history_v1').put(entry_id,json.dumps(record,separators=(',',':')),owner=identity)

