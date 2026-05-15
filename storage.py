import json, os, threading
from datetime import datetime, timezone

DB_PATH = os.getenv('SESSION_DB_PATH', 'sessions.json')
_LOCK = threading.Lock()
SYSTEM_KEY = '__system__'

def _load():
    if not os.path.exists(DB_PATH): return {}
    try:
        with open(DB_PATH,'r',encoding='utf-8') as f: return json.load(f)
    except Exception: return {}

def _save(data):
    directory=os.path.dirname(DB_PATH)
    if directory:
        os.makedirs(directory, exist_ok=True)
    tmp=DB_PATH+'.tmp'
    with open(tmp,'w',encoding='utf-8') as f: json.dump(data,f,ensure_ascii=False,indent=2)
    os.replace(tmp, DB_PATH)

def now_iso(): return datetime.now(timezone.utc).isoformat()

def get_session(session_id):
    with _LOCK:
        return _load().get(session_id, {})

def update_session(session_id, patch):
    with _LOCK:
        data=_load(); s=data.get(session_id,{})
        s.update(patch); s['updated_at']=now_iso()
        data[session_id]=s; _save(data); return s

def all_sessions():
    with _LOCK:
        data=_load()
        return {k:v for k,v in data.items() if k != SYSTEM_KEY}

def get_system_state():
    with _LOCK:
        return _load().get(SYSTEM_KEY, {})

def update_system_state(patch):
    with _LOCK:
        data=_load(); s=data.get(SYSTEM_KEY,{})
        s.update(patch); s['updated_at']=now_iso()
        data[SYSTEM_KEY]=s; _save(data); return s

def next_round_robin_operator():
    """Return the next operator in Alex's fixed order and persist the pointer."""
    operators=['Ryan','Vitória','Otávio','Tatiane','Bianca']
    with _LOCK:
        data=_load(); system=data.get(SYSTEM_KEY,{})
        idx=int(system.get('operator_round_robin_index') or 0) % len(operators)
        operator=operators[idx]
        system['operator_round_robin_index']=(idx + 1) % len(operators)
        system['last_operator_assigned']=operator
        system['last_operator_assigned_at']=now_iso()
        system['updated_at']=now_iso()
        data[SYSTEM_KEY]=system
        _save(data)
        return operator
