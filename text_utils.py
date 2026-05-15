import re
from datetime import datetime, time

CPF_RE = re.compile(r'\b\d{3}\.?\d{3}\.?\d{3}-?\d{2}\b|\b\d{11}\b')
EMAIL_RE = re.compile(r'[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}')
DATE_RE = re.compile(r'\b\d{1,2}[./-]\d{1,2}[./-]\d{2,4}\b')
DATE_8_RE = re.compile(r'\b\d{8}\b')

FIELD_LABELS = {
    'name': 'Nome completo',
    'cpf': 'CPF',
    'birth': 'Data de nascimento',
    'email': 'E-mail',
}
COMMON_NON_NAMES = {
    'cpf','cof','email','e-mail','data','nascimento','nasci','nasc','mande','mandei','enviei','ja','já','nome','completo',
    'precisa','preciso','mais','nao','não','ok','oi','bom','boa','tarde','dia','noite','obrigado','obrigada'
}

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

def normalize_cpf(value: str):
    digits=re.sub(r'\D+', '', value or '')
    return digits if len(digits)==11 else ''

def normalize_birth(value: str):
    raw=(value or '').strip()
    digits=re.sub(r'\D+', '', raw)
    if len(digits)==8:
        day=int(digits[:2]); month=int(digits[2:4]); year=int(digits[4:])
        if year < 100:
            year += 1900 if year > 30 else 2000
        if 1 <= day <= 31 and 1 <= month <= 12 and 1900 <= year <= datetime.now().year:
            return f'{day:02d}/{month:02d}/{year:04d}'
    return raw if DATE_RE.search(raw) else ''

def _extract_labeled_name(text: str):
    m=re.search(r'nome\s*(?:completo)?\s*[:\-]\s*([^\n\r]+)', text or '', re.I)
    if not m:
        return ''
    candidate=m.group(1).strip()
    candidate=re.sub(r'\b(cpf|data|nascimento|e-?mail)\b.*$', '', candidate, flags=re.I).strip()
    words=re.findall(r'\b[A-Za-zÀ-ÿ]{2,}\b', candidate)
    return candidate if len(words) >= 2 else ''

def _extract_free_name(text: str):
    t=text or ''
    low=t.lower()
    if any(k in low for k in ['cpf','cof','email','e-mail','data de nascimento','nascimento','já mandei','ja mandei','não precisa','nao precisa']):
        return ''
    cleaned=EMAIL_RE.sub(' ', t)
    cleaned=CPF_RE.sub(' ', cleaned)
    cleaned=DATE_RE.sub(' ', cleaned)
    cleaned=DATE_8_RE.sub(' ', cleaned)
    words=re.findall(r'\b[A-Za-zÀ-ÿ]{2,}\b', cleaned)
    meaningful=[w for w in words if w.lower() not in COMMON_NON_NAMES]
    if len(meaningful) >= 2 and len(' '.join(meaningful)) >= 6:
        return ' '.join(meaningful[:6])
    return ''

def extract_personal_data_fields(text: str):
    """Extract only fields actually present in this message.

    Used to accumulate personal data across multiple WhatsApp messages so the bot
    asks only for what is still missing instead of repeatedly asking everything.
    """
    text=text or ''
    fields={}
    cpf=CPF_RE.search(text)
    if cpf:
        fields['cpf']=normalize_cpf(cpf.group(0)) or cpf.group(0)
    email=EMAIL_RE.search(text)
    if email:
        fields['email']=email.group(0)
    birth=DATE_RE.search(text) or DATE_8_RE.search(text)
    if birth:
        normalized=normalize_birth(birth.group(0))
        if normalized:
            fields['birth']=normalized
    name=_extract_labeled_name(text) or _extract_free_name(text)
    if name:
        fields['name']=name
    return fields

def missing_personal_fields(personal_data: dict):
    personal_data=personal_data or {}
    missing=[]
    for key,label in FIELD_LABELS.items():
        if not personal_data.get(key):
            missing.append(label)
    return missing

def has_required_personal_data(text: str):
    fields=extract_personal_data_fields(text)
    missing=missing_personal_fields(fields)
    return not missing, missing

def is_status_question(text: str):
    t=(text or '').lower()
    keys=['deu certo','e aí','e ai','ta vendo','tá vendo','conseguiu','retorno','proposta','simulação','simulacao','demorando','novidade','alguma coisa']
    return any(k in t for k in keys)

def is_memory_question(text: str):
    t=(text or '').lower()
    keys=['já nos falamos','ja nos falamos','já falamos','ja falamos','já te mandei','ja te mandei','mande algum dado','mandei algum dado','meus dados','algum dado','já passei','ja passei']
    return any(k in t for k in keys)

def is_cancel_message(text: str):
    t=(text or '').lower()
    keys=['não precisa mais','nao precisa mais','não quero mais','nao quero mais','desisti','desistir','cancelar','cancela','deixa pra lá','deixa pra la']
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
    # Só ativa follow-up quando operador parece ter enviado valores/condições reais.
    # Frases genéricas como “vou dar andamento na sua proposta” não contam.
    strong=['valor liberado','valor disponível','valor disponivel','segue a simulação','simulacao','simulação','parcela','taxa','aprovado','aprovada']
    money=bool(re.search(r'\br\$\s*\d|\b\d+[\.,]\d{2}\b', t))
    return any(k in t for k in strong) or (money and any(k in t for k in ['proposta','valor','liberado','parcela']))

def within_business_hours(dt=None, start=8, end=18):
    dt = dt or datetime.now()
    if dt.weekday() >= 5:  # sábado/domingo
        return False
    return time(start,0) <= dt.time() <= time(end,0)
