import re
from datetime import datetime, time

CPF_RE = re.compile(r'\b\d{3}\.?\d{3}\.?\d{3}-?\d{2}\b')
EMAIL_RE = re.compile(r'[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}')
DATE_RE = re.compile(r'\b\d{1,2}[/-]\d{1,2}[/-]\d{2,4}\b')

def parse_tenure_months(text: str):
    t = (text or '').lower().replace(',', ' ')
    years = 0; months = 0
    for m in re.finditer(r'(\d+)\s*(ano|anos|a\b)', t):
        years += int(m.group(1))
    for m in re.finditer(r'(\d+)\s*(mes|mês|meses|m\b)', t):
        months += int(m.group(1))
    if years or months:
        return years * 12 + months
    nums = re.findall(r'\b\d{1,2}\b', t)
    if nums:
        n = int(nums[0])
        return n if n <= 24 else None
    return None

def has_required_personal_data(text: str):
    cpf = CPF_RE.search(text or '')
    email = EMAIL_RE.search(text or '')
    birth = DATE_RE.search(text or '')
    cleaned = EMAIL_RE.sub(' ', text or '')
    words = re.findall(r'\b[A-Za-zÀ-ÿ]{2,}\b', cleaned)
    has_name = len(words) >= 2
    missing=[]
    if not has_name: missing.append('Nome completo')
    if not cpf: missing.append('CPF')
    if not birth: missing.append('Data de nascimento')
    if not email: missing.append('E-mail')
    return not missing, missing

def is_status_question(text: str):
    t=(text or '').lower()
    keys=['deu certo','e aí','e ai','ta vendo','tá vendo','conseguiu','retorno','proposta','simulação','simulacao','demorando','novidade','alguma coisa']
    return any(k in t for k in keys)

def is_memory_question(text: str):
    t=(text or '').lower()
    keys=['já nos falamos','ja nos falamos','já falamos','ja falamos','já te mandei','ja te mandei','mande algum dado','mandei algum dado','meus dados','algum dado','já passei','ja passei']
    return any(k in t for k in keys)

def asks_about_bank_app(text: str):
    t=(text or '').lower()
    return any(k in t for k in ['carteira digital','ctps digital','banco do brasil','caixa tem','meu banco','direto no banco','aplicativo do banco','app do banco'])

def looks_like_document(text: str):
    t=(text or '').lower()
    keys=['[document]','[image]','[pdf]','[arquivo]','[foto]','documento','rg','cnh','holerite','contracheque','comprovante','carteira','ctps','print']
    return any(k in t for k in keys)

def looks_like_proposal_sent(text: str):
    t=(text or '').lower()
    keys=['proposta','valor liberado','valor disponível','valor disponivel','parcela','taxa','aprovado','aprovada','vamos seguir','segue a simulação','simulacao','simulação']
    return any(k in t for k in keys)

def within_business_hours(dt=None, start=8, end=18):
    dt = dt or datetime.now()
    if dt.weekday() >= 5:  # sábado/domingo
        return False
    return time(start,0) <= dt.time() <= time(end,0)
