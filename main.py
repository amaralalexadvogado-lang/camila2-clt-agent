import os, logging, asyncio
from datetime import datetime, timezone, timedelta
from fastapi import FastAPI, Request, BackgroundTasks
from dotenv import load_dotenv
from src.agent import process_message
from src.storage import update_session, all_sessions
from src.venditore import send_text, create_note
from src.text_utils import within_business_hours, looks_like_proposal_sent

load_dotenv()
logging.basicConfig(level=logging.INFO)
logger=logging.getLogger('camila2-clt')
app=FastAPI(title='Camila 2 CLT - Crédito Já')

BUSINESS_START=int(os.getenv('BUSINESS_START_HOUR','8'))
BUSINESS_END=int(os.getenv('BUSINESS_END_HOUR','18'))
FOLLOWUP_MAX_HOURS=int(os.getenv('FOLLOWUP_MAX_HOURS','48'))
FOLLOWUP_INTERVAL_MINUTES=int(os.getenv('FOLLOWUP_INTERVAL_MINUTES','60'))

@app.get('/')
def root(): return {'ok': True, 'service':'camila2-clt'}
@app.get('/health')
def health(): return {'ok': True}

def extract_message(body: dict):
    content=body.get('content') if isinstance(body.get('content'),dict) else {}
    session_id=content.get('sessionId') or body.get('sessionId') or body.get('session_id') or ''
    msg_type=(content.get('type') or body.get('messageType') or '').upper()
    text=content.get('text') or content.get('caption') or body.get('text') or ''
    if not text and msg_type in ['IMAGE','DOCUMENT','VIDEO','AUDIO','FILE']:
        text=f'[{msg_type.lower()}] documento recebido'
    event=(body.get('eventType') or body.get('event') or body.get('type') or '').upper()
    user_id=body.get('userId') or content.get('userId')
    if not text and isinstance(body.get('message'), dict):
        m=body['message']; session_id=session_id or m.get('sessionId',''); text=m.get('text','') or m.get('caption','')
    if not text and isinstance(body.get('data'), dict):
        d=body['data']; session_id=session_id or d.get('sessionId',''); text=d.get('text','') or d.get('caption','')
    if user_id:
        return session_id, text, 'human_out'
    if event and event not in ['MESSAGE_RECEIVED','MESSAGE.RECEIVED','NEW_MESSAGE','NEWMESSAGE']:
        if not text:
            return session_id, '', 'ignore'
    return session_id, text, 'in'

@app.post('/webhook/venditore')
async def webhook_venditore(request: Request, background_tasks: BackgroundTasks):
    body=await request.json()
    session_id,text,kind=extract_message(body)
    if not session_id:
        return {'ok': True, 'ignored': 'no_session'}
    if kind == 'human_out':
        background_tasks.add_task(handle_operator_message, session_id, text)
        return {'ok': True, 'operator': True}
    if kind!='in' or not text:
        return {'ok': True, 'ignored': kind}
    background_tasks.add_task(handle_incoming, session_id, text)
    return {'ok': True}

async def handle_operator_message(session_id: str, text: str):
    # Quando operador passa proposta, a Camila inicia follow-up comercial se cliente não responder.
    if text and looks_like_proposal_sent(text):
        update_session(session_id, {
            'stage':'proposal_sent',
            'proposal_sent_at': datetime.now(timezone.utc).isoformat(),
            'last_proposal_followup_at': None,
            'proposal_followup_count': 0
        })
        logger.info('Proposta detectada por operador na sessão %s', session_id)

async def handle_incoming(session_id: str, text: str):
    logger.info('Mensagem recebida %s: %s', session_id, text[:120])
    # Se cliente respondeu depois de proposta, parar follow-up automático.
    # A resposta vai para operador; a Camila só confirma intenção sem pedir dados novamente.
    replies, note = process_message(session_id, text)
    if note:
        create_note(session_id, note)
    for msg in [r for r in replies if r]:
        send_text(session_id, msg)
        await asyncio.sleep(0.8)

@app.on_event('startup')
async def startup_event():
    asyncio.create_task(followup_loop())

async def followup_loop():
    while True:
        try:
            await run_followups_once()
        except Exception as e:
            logger.exception('Erro no follow-up: %s', e)
        await asyncio.sleep(60)

async def run_followups_once():
    now=datetime.now(timezone.utc)
    local_now=datetime.now()
    if not within_business_hours(local_now, BUSINESS_START, BUSINESS_END):
        return
    data=all_sessions()
    for session_id,s in data.items():
        stage=s.get('stage')
        if stage == 'ask_data':
            started=datetime.fromisoformat(s.get('ask_data_at')) if s.get('ask_data_at') else now
            last_key='last_followup_at'; count_key='followup_count'
            msg=('Oi, passando para dar sequência ao seu atendimento do consignado CLT. '
                 'Para eu encaminhar sua análise, me envie por favor: nome completo, CPF, data de nascimento e e-mail.')
        elif stage == 'ask_documents':
            started=datetime.fromisoformat(s.get('ask_documents_at')) if s.get('ask_documents_at') else now
            last_key='last_doc_followup_at'; count_key='doc_followup_count'
            msg=('Oi, já recebi seus dados. Falta só o envio dos documentos/fotos para eu encaminhar ao time comercial. '
                 'Pode mandar por aqui para seguirmos?')
        elif stage == 'proposal_sent':
            started=datetime.fromisoformat(s.get('proposal_sent_at')) if s.get('proposal_sent_at') else now
            last_key='last_proposal_followup_at'; count_key='proposal_followup_count'
            msg=('Passando para confirmar: o valor da proposta ainda está disponível para você. '
                 'Vamos seguir com a contratação?')
        else:
            continue
        if now - started > timedelta(hours=FOLLOWUP_MAX_HOURS):
            update_session(session_id, {'followup_expired_at': now.isoformat()})
            continue
        last=s.get(last_key)
        if last and now - datetime.fromisoformat(last) < timedelta(minutes=FOLLOWUP_INTERVAL_MINUTES):
            continue
        count=int(s.get(count_key) or 0) + 1
        if send_text(session_id, msg):
            update_session(session_id, {last_key:now.isoformat(), count_key:count})

@app.post('/admin/followups/run-once')
async def admin_followups():
    await run_followups_once(); return {'ok': True}

@app.post('/admin/session/{session_id}/proposal-sent')
async def mark_proposal_sent(session_id: str):
    update_session(session_id, {'stage':'proposal_sent','proposal_sent_at':datetime.now(timezone.utc).isoformat(),'proposal_followup_count':0})
    return {'ok': True}
