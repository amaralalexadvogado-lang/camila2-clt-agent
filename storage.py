import json, os, threading
from datetime import datetime, timezone

DB_PATH = os.getenv('SESSION_DB_PATH', 'sessions.json')
_LOCK = threading.Lock()

def _load():
    if not os.path.exists(DB_PATH): return {}
    try:
        with open(DB_PATH,'r',encoding='utf-8') as f: return json.load(f)
    except Exception: return {}

def _save(data):
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
    with _LOCK: return _load()
