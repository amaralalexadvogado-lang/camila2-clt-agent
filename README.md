# Camila 2 CLT — Crédito Já / Venditore

Agente para qualificação de leads de empréstimo consignado CLT via WhatsApp/Venditore.

## Incluído nesta versão

- Memória persistente por sessão: não pede novamente vínculo, dados ou documentos já recebidos.
- Skill interna de vendedor de consignado CLT em `src/sales_skill.py`.
- Regras de banco por tempo de vínculo em `src/bank_rules.py`.
- Fluxo: vínculo → dados → documentos → operador.
- Só gera nota de liberação ao operador quando dados + documentos estão confirmados.
- Follow-up de dados por 48h, de 1h em 1h, somente segunda a sexta, das 08h às 18h.
- Follow-up de documentos por 48h, de 1h em 1h, segunda a sexta, das 08h às 18h.
- Quando operador envia proposta, inicia follow-up de proposta por 48h: “o valor ainda está disponível, vamos seguir?”
- Respostas comerciais contra objeções: SPC/Serasa, taxa, segurança, pagamento antecipado, carteira digital/app do banco.
- Nunca recomenda fazer pela carteira digital ou direto em banco único.

## Arquivos principais

- `main.py`: webhook FastAPI da Venditore + follow-ups.
- `src/agent.py`: fluxo conversacional.
- `src/sales_skill.py`: skill de vendedor CLT.
- `src/bank_rules.py`: regras extraídas do PDF.
- `src/storage.py`: memória em JSON por sessão.
- `src/venditore.py`: API wts.chat.

## Memória no Railway

Para a memória não sumir em deploy/restart, crie um Volume no Railway e configure:

`SESSION_DB_PATH=/data/sessions.json`

Sem Volume, funciona, mas a memória pode ser perdida em redeploy.

## Webhook Venditore

Configurar na Venditore:

`https://SEU-PROJETO.up.railway.app/webhook/venditore`

## Segurança

Não subir `.env` nem token real para GitHub.
Tokens devem ficar apenas nas variáveis do Railway.
