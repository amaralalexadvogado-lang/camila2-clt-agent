import os, logging, requests
logger=logging.getLogger(__name__)
BASE=os.getenv('VENDITORE_BASE_URL','https://api.wts.chat').rstrip('/')
TOKEN=os.getenv('VENDITORE_TOKEN','')
ACCOUNT=os.getenv('VENDITORE_ACCOUNT_ID','')

def headers():
    h={'Authorization': f'Bearer {TOKEN}', 'Content-Type':'application/json'}
    if ACCOUNT: h['account']=ACCOUNT
    return h

def send_text(session_id: str, text: str) -> bool:
    if os.getenv('DRY_RUN','false').lower()=='true' or not TOKEN:
        logger.info('[DRY_RUN] Para %s: %s', session_id, text)
        return True
    endpoints=[f'/chat/v1/session/{session_id}/message', f'/chat/v3/session/{session_id}/message/text']
    for ep in endpoints:
        try:
            r=requests.post(BASE+ep, headers=headers(), json={'text':text}, timeout=20)
            if r.status_code in (200,201,202,204): return True
            logger.warning('Venditore send %s -> %s %s', ep, r.status_code, r.text[:200])
        except Exception as e: logger.exception('Erro Venditore send: %s', e)
    return False

def create_note(session_id: str, text: str) -> bool:
    if os.getenv('DRY_RUN','false').lower()=='true' or not TOKEN:
        logger.info('[DRY_RUN NOTE] %s: %s', session_id, text); return True
    for ep in [f'/chat/v1/session/{session_id}/note']:
        try:
            r=requests.post(BASE+ep, headers=headers(), json={'text':text}, timeout=20)
            if r.status_code in (200,201,202,204): return True
            logger.warning('Venditore note %s -> %s %s', ep, r.status_code, r.text[:200])
        except Exception as e: logger.exception('Erro Venditore note: %s', e)
    return False
