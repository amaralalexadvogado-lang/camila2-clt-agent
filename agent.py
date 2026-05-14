from datetime import datetime, timezone
from bank_rules import bank_card
from text_utils import parse_tenure_months, has_required_personal_data, is_status_question, asks_about_bank_app, looks_like_document
from storage import get_session, update_session
from sales_skill import OBJECTION_REPLIES

INTRO = ('Olá! 😊 Sou a Camila, assistente da Crédito Já, correspondente bancária especializada em empréstimo para o trabalhador, '
         'parceira de bancos como BMG, C6, FACTA, MERCANTIL e outros bancos.\n\n'
         '🔒 Nosso atendimento é 100% gratuito, sem pagamento antecipado e sem consulta ao SPC/Serasa. '
         'Os descontos só acontecem no seu holerite depois da aprovação.\n\n'
         'Antes de continuarmos, preciso te perguntar uma coisa importante: quanto tempo você tem de carteira assinada nessa empresa?')
ASK_TENURE = 'Para eu ver os bancos certos para seu caso, preciso primeiro saber: quanto tempo você tem de carteira assinada nessa empresa?'
ASK_DATA = ('Perfeito! Agora preciso dessas informações para seguirmos:\n\n'
            'Nome completo:\nCPF:\nData de nascimento:\nE-mail:\n\n'
            'O e-mail é para caso a gente precise enviar o link para autorizar a consulta.')
ASK_DOCS = ('Perfeito, recebi seus dados e eles estão protegidos pela LGPD. ✅\n\n'
            'Agora, para eu encaminhar corretamente ao time comercial, me envie por favor os documentos/fotos necessários para conferência:\n'
            '- documento com foto (RG ou CNH);\n'
            '- holerite/contracheque recente ou comprovante de vínculo;\n'
            '- se tiver, print da carteira digital/CTPS mostrando o vínculo.\n\n'
            'Assim que receber, confirmo aqui e encaminho para o operador.')
DOCS_OK = ('Documentos recebidos, obrigado! ✅\n\n'
           'Agora sim encaminhei seu atendimento para o nosso time comercial verificar as propostas disponíveis.\n\n'
           'Importante: enquanto aguardamos, não tente simular em outros lugares para não travar seu CPF por até 48h. Já vamos te retornar.')
STATUS_HOLD = ('Estamos acompanhando por aqui. O sistema dos bancos está com instabilidade e por isso está demorando um pouco mais do que o esperado, '
               'mas seu caso já está com a gente e vamos te dar retorno assim que liberar a análise.')
BANK_APP_REPLY = OBJECTION_REPLIES['carteira_digital']

QUESTION_REPLIES = [
    (['spc','serasa','consulta'], OBJECTION_REPLIES['spc']),
    (['paga','antecipado','taxa antes','pix'], 'Não tem pagamento antecipado. O atendimento é gratuito e qualquer desconto só acontece no holerite depois da aprovação.'),
    (['holerite','desconto'], 'Nesse produto, se aprovado, o desconto acontece direto no holerite, conforme a margem disponível e as condições do banco.'),
    (['juros','taxa'], OBJECTION_REPLIES['taxa']),
    (['golpe','seguro','segurança','seguranca','lgpd'], OBJECTION_REPLIES['seguranca']),
]

def answer_question_if_needed(text):
    t=(text or '').lower()
    if asks_about_bank_app(text): return BANK_APP_REPLY
    for keys, ans in QUESTION_REPLIES:
        if any(k in t for k in keys): return ans
    return None

def operator_release_note(session_id: str):
    s=get_session(session_id)
    return '\n'.join([
        'LEAD CLT PRONTO PARA OPERADOR',
        f"Vínculo: {s.get('tenure_months')} meses",
        'Dados pessoais: recebidos e confirmados',
        'Documentos: recebidos e confirmados',
        '',
        s.get('bank_card','')
    ])

def process_message(session_id: str, text: str):
    s=get_session(session_id)
    stage=s.get('stage','new')
    text=text or ''

    # Memória anti-alucinação: se já está aguardando/proposta, não pedir dados/docs de novo.
    if stage in ('ready_for_operator','completed') and is_status_question(text):
        return [STATUS_HOLD], None
    if stage == 'proposal_sent':
        return ['Perfeito. A proposta está disponível para seguirmos. Quer que eu peça para o time comercial dar continuidade agora?'], None

    if stage in ('new','ask_tenure'):
        tenure=parse_tenure_months(text)
        if tenure is None:
            extra=answer_question_if_needed(text)
            update_session(session_id, {'stage':'ask_tenure', 'first_seen_at':s.get('first_seen_at') or datetime.now(timezone.utc).isoformat()})
            if stage == 'new':
                return [INTRO], None
            if extra:
                return [extra, ASK_TENURE], None
            return [ASK_TENURE], None
        card=bank_card(tenure)
        update_session(session_id, {
            'stage':'ask_data','tenure_months':tenure,'bank_card':card,
            'ask_data_at':datetime.now(timezone.utc).isoformat(),'followup_count':0,
            'personal_data_received': False, 'documents_received': False
        })
        return [ASK_DATA], card

    if stage == 'ask_data':
        ok, missing=has_required_personal_data(text)
        if not ok:
            extra=answer_question_if_needed(text)
            msg='Ainda preciso destes dados para seguir: ' + ', '.join(missing) + '. Pode me mandar, por favor?'
            return ([extra, msg] if extra else [msg]), None
        update_session(session_id, {
            'stage':'ask_documents','personal_data_received': True,
            'personal_data_received_at':datetime.now(timezone.utc).isoformat(),
            'raw_personal_data':text,'ask_documents_at':datetime.now(timezone.utc).isoformat(),
            'followup_count':0
        })
        return [ASK_DOCS], None

    if stage == 'ask_documents':
        if looks_like_document(text):
            update_session(session_id, {
                'stage':'ready_for_operator','documents_received': True,
                'documents_received_at':datetime.now(timezone.utc).isoformat(),
                'ready_for_operator_at':datetime.now(timezone.utc).isoformat()
            })
            return [DOCS_OK], operator_release_note(session_id)
        extra=answer_question_if_needed(text)
        msg='Já recebi seus dados. Agora falta apenas enviar os documentos/fotos para eu poder encaminhar ao time comercial. Pode mandar por aqui, por favor?'
        return ([extra, msg] if extra else [msg]), None

    return [ASK_TENURE], None
