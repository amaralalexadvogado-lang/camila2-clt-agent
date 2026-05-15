import os, logging, requests
logger=logging.getLogger(__name__)
BASE=os.getenv('VENDITORE_BASE_URL','https://api.wts.chat').rstrip('/')
TOKEN=os.getenv('VENDITORE_TOKEN','')
# Novo conector Venditore/WhatsApp da Camila 2. Pode ficar vazio se a API aceitar só Bearer token.
CONNECTION_ID=os.getenv('VENDITORE_CONNECTION_ID','') or os.getenv('VENDITORE_ACCOUNT_ID','')
ACCOUNT=CONNECTION_ID

# Etiquetas exigidas pelo Alex no fim do fluxo CLT.
# Se a API do Venditore da conta exigir ID em vez de nome, configure estes envs no Railway:
# VENDITORE_LABEL_DIGITAR_PROPOSTA_ID, VENDITORE_LABEL_RYAN_ID, VENDITORE_LABEL_VITORIA_ID,
# VENDITORE_LABEL_OTAVIO_ID, VENDITORE_LABEL_TATIANE_ID, VENDITORE_LABEL_BIANCA_ID.

OPERATOR_LABEL_ENV={
    'Ryan':'VENDITORE_LABEL_RYAN_ID',
    'Vitória':'VENDITORE_LABEL_VITORIA_ID',
    'Otávio':'VENDITORE_LABEL_OTAVIO_ID',
    'Tatiane':'VENDITORE_LABEL_TATIANE_ID',
    'Bianca':'VENDITORE_LABEL_BIANCA_ID',
}

def headers():
    h={'Authorization': f'Bearer {TOKEN}', 'Content-Type':'application/json'}
    if ACCOUNT: h['account']=ACCOUNT
    return h

def _post(endpoint: str, payload: dict) -> bool:
    if os.getenv('DRY_RUN','false').lower()=='true' or not TOKEN:
        logger.info('[DRY_RUN POST] %s %s', endpoint, payload)
        return True
    try:
        r=requests.post(BASE+endpoint, headers=headers(), json=payload, timeout=20)
        if r.status_code in (200,201,202,204): return True
        logger.warning('Venditore post %s -> %s %s', endpoint, r.status_code, r.text[:300])
    except Exception as e:
        logger.exception('Erro Venditore post %s: %s', endpoint, e)
    return False

def _put(endpoint: str, payload: dict) -> bool:
    if os.getenv('DRY_RUN','false').lower()=='true' or not TOKEN:
        logger.info('[DRY_RUN PUT] %s %s', endpoint, payload)
        return True
    try:
        r=requests.put(BASE+endpoint, headers=headers(), json=payload, timeout=20)
        if r.status_code in (200,201,202,204): return True
        logger.warning('Venditore put %s -> %s %s', endpoint, r.status_code, r.text[:300])
    except Exception as e:
        logger.exception('Erro Venditore put %s: %s', endpoint, e)
    return False

def send_text(session_id: str, text: str) -> bool:
    endpoints=[f'/chat/v1/session/{session_id}/message', f'/chat/v3/session/{session_id}/message/text']
    for ep in endpoints:
        if _post(ep, {'text':text}): return True
    return False

def create_note(session_id: str, text: str) -> bool:
    for ep in [f'/chat/v1/session/{session_id}/note']:
        if _post(ep, {'text':text}): return True
    return False

def _label_payloads(label_name: str):
    label_id = None
    if label_name.lower() == 'digitar proposta':
        label_id = os.getenv('VENDITORE_LABEL_DIGITAR_PROPOSTA_ID')
    else:
        label_id = os.getenv(OPERATOR_LABEL_ENV.get(label_name,''), '')

    payloads=[]
    if label_id:
        payloads.extend([
            {'labelId': label_id}, {'tagId': label_id}, {'id': label_id},
            {'labelIds':[label_id]}, {'tagIds':[label_id]}, {'labels':[label_id]}, {'tags':[label_id]},
        ])
    payloads.extend([
        {'name': label_name}, {'label': label_name}, {'tag': label_name},
        {'labelName': label_name}, {'tagName': label_name},
        {'labels':[label_name]}, {'tags':[label_name]},
    ])
    return payloads

def add_label(session_id: str, label_name: str) -> bool:
    """Apply one Venditore label by name/ID, trying common WTS/Venditore shapes.

    The exact Venditore account may accept names directly or require configured label IDs.
    We try conservative endpoints and log any failure without blocking the customer reply.
    """
    endpoints=[
        f'/chat/v1/session/{session_id}/label',
        f'/chat/v1/session/{session_id}/labels',
        f'/chat/v1/session/{session_id}/tag',
        f'/chat/v1/session/{session_id}/tags',
        f'/chat/v3/session/{session_id}/label',
        f'/chat/v3/session/{session_id}/labels',
        f'/chat/v3/session/{session_id}/tag',
        f'/chat/v3/session/{session_id}/tags',
    ]
    for ep in endpoints:
        for payload in _label_payloads(label_name):
            if _post(ep, payload):
                logger.info('Etiqueta aplicada na sessão %s: %s', session_id, label_name)
                return True
    # Fallback: algumas contas aceitam atualização direta da sessão.
    for payload in _label_payloads(label_name):
        if _put(f'/chat/v1/session/{session_id}', payload):
            logger.info('Etiqueta aplicada via update na sessão %s: %s', session_id, label_name)
            return True
    logger.error('Não foi possível aplicar etiqueta %s na sessão %s', label_name, session_id)
    return False

def apply_handoff_labels(session_id: str, operator_name: str) -> dict:
    results={
        'digitar proposta': add_label(session_id, 'digitar proposta'),
        operator_name: add_label(session_id, operator_name),
    }
    if not all(results.values()):
        create_note(session_id, 'ATENÇÃO: lead pronto para digitação, mas a aplicação automática de alguma etiqueta falhou. Etiquetas necessárias: digitar proposta e ' + operator_name)
    return results
