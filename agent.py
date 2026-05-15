from datetime import datetime, timezone
from bank_rules import bank_card
from text_utils import parse_tenure_months, has_required_personal_data, is_status_question, is_memory_question, asks_about_bank_app
from storage import get_session, update_session, next_round_robin_operator
from sales_skill import OBJECTION_REPLIES

INTRO = ('Olá! 😊 Sou a Camila, assistente da Crédito Já, correspondente bancária especializada em empréstimo para o trabalhador.\n\n'
         '🔒 Nosso atendimento é 100% gratuito, sem pagamento antecipado e sem consulta ao SPC/Serasa. '
         'Os descontos só acontecem no seu holerite depois da aprovação.\n\n'
         'Antes de continuarmos, preciso te perguntar uma coisa importante: quanto tempo você tem de carteira assinada nessa empresa?')
ASK_TENURE = 'Para eu ver os bancos certos para seu caso, preciso primeiro saber: quanto tempo você tem de carteira assinada nessa empresa?'
ASK_DATA = ('Perfeito! Agora preciso dessas informações para seguirmos:\n\n'
            'Nome completo:\nCPF:\nData de nascimento:\nE-mail:\n\n'
            'O e-mail é para caso a gente precise enviar o link para autorizar a consulta.')
DATA_OK_OPERATOR = 'Obrigado pelo envio das informações. Seus dados estão protegidos pela LGPD. ✅'
INELIGIBLE_TENURE = ('Infelizmente, pelo seu tempo de casa, não vai ser possível dar sequência agora. '
                     'Mas vamos deixar seu cadastro salvo em nosso sistema para contato futuro. '
                     'Tenha um ótimo dia e fique com Deus. 🙏')
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

def operator_release_note(session_id: str, operator_name: str):
    s=get_session(session_id)
    return '\n'.join([
        'LEAD CLT PRONTO PARA DIGITAÇÃO',
        'Etiquetas obrigatórias: digitar proposta; ' + operator_name,
        'Operador responsável pelo rodízio: ' + operator_name,
        f"Vínculo: {s.get('tenure_months')} meses",
        'Dados pessoais: recebidos e confirmados',
        'Documentos: NÃO SOLICITAR NESTA ETAPA',
        '',
        s.get('bank_card','')
    ])

def process_message(session_id: str, text: str):
    s=get_session(session_id)
    stage=s.get('stage','new')
    text=text or ''

    # Retorno padrão: (mensagens_para_cliente, nota_interna, operador_para_etiquetas)
    # Depois que foi liberado para operador/digitação, a Camila fica em silêncio.
    # Só volta a falar se um operador enviar proposta e o cliente ficar sem responder (follow-up em main.py).
    if stage in ('ready_for_operator','completed','operator_active','ineligible'):
        return [], None, None
    if stage == 'proposal_sent':
        update_session(session_id, {'stage':'operator_active','customer_replied_after_proposal_at':datetime.now(timezone.utc).isoformat()})
        return [], None, None

    if stage in ('new','ask_tenure'):
        tenure=parse_tenure_months(text)
        if tenure is None:
            extra=answer_question_if_needed(text)
            update_session(session_id, {'stage':'ask_tenure', 'first_seen_at':s.get('first_seen_at') or datetime.now(timezone.utc).isoformat()})
            if stage == 'new':
                if is_memory_question(text):
                    return ['Eu conferi por aqui e ainda não localizei seus dados completos neste atendimento. Para eu não te passar informação errada, me confirma primeiro: quanto tempo você tem de carteira assinada nessa empresa?'], None, None
                return [INTRO], None, None
            if extra:
                return [extra, ASK_TENURE], None, None
            if is_memory_question(text):
                return ['Eu conferi por aqui e ainda não localizei seus dados completos neste atendimento. Para eu não te passar informação errada, me confirma primeiro: quanto tempo você tem de carteira assinada nessa empresa?'], None, None
            return [ASK_TENURE], None, None
        card=bank_card(tenure)
        if tenure < 3:
            update_session(session_id, {
                'stage':'ineligible',
                'tenure_months':tenure,
                'ineligible_reason':'tenure_less_than_3_months',
                'ineligible_at':datetime.now(timezone.utc).isoformat()
            })
            return [INELIGIBLE_TENURE], 'LEAD CLT SEM SEQUÊNCIA AGORA\nMotivo: tempo de casa inferior a 3 meses\nSalvar para contato futuro.', None
        update_session(session_id, {
            'stage':'ask_data','tenure_months':tenure,'bank_card':card,
            'ask_data_at':datetime.now(timezone.utc).isoformat(),'followup_count':0,
            'personal_data_received': False
        })
        return [ASK_DATA], card, None

    if stage == 'ask_data':
        ok, missing=has_required_personal_data(text)
        if not ok:
            extra=answer_question_if_needed(text)
            msg='Ainda preciso destes dados para seguir: ' + ', '.join(missing) + '. Pode me mandar, por favor?'
            return ([extra, msg] if extra else [msg]), None, None
        operator_name=next_round_robin_operator()
        update_session(session_id, {
            'stage':'ready_for_operator',
            'personal_data_received': True,
            'personal_data_received_at':datetime.now(timezone.utc).isoformat(),
            'raw_personal_data':text,
            'ready_for_operator_at':datetime.now(timezone.utc).isoformat(),
            'assigned_operator': operator_name
        })
        return [DATA_OK_OPERATOR], operator_release_note(session_id, operator_name), operator_name

    if stage == 'ready_for_operator':
        return [STATUS_HOLD], None, None

    return [ASK_TENURE], None, None
