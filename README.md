[README.md](https://github.com/user-attachments/files/27801198/README.md)
# Camila 2 CLT — Crédito Já / Venditore

Agente para qualificação de leads de empréstimo consignado CLT via WhatsApp/Venditore.

## Incluído nesta versão

- Memória persistente por sessão: não pede novamente vínculo ou dados pessoais já recebidos.
- Skill interna de vendedor de consignado CLT em `sales_skill.py`.
- Regras de banco por tempo de vínculo em `bank_rules.py`.
- Fluxo: vínculo → dados pessoais → operador/digitação.
- Após dados pessoais completos, gera nota/card interno e tenta aplicar automaticamente as etiquetas `digitar proposta` e o nome do operador.
- Rodízio persistente de operadores: Ryan → Vitória → Otávio → Tatiane → Bianca, repetindo nessa ordem sem reiniciar a cada atendimento.
- Não pede documentos antes da digitação.
- Follow-up de dados por 48h, de 1h em 1h, somente segunda a sexta, das 08h às 18h.
- Quando operador envia proposta, inicia follow-up de proposta por 48h: “o valor ainda está disponível, vamos seguir?”
- Respostas comerciais contra objeções: SPC/Serasa, taxa, segurança, pagamento antecipado, carteira digital/app do banco.
- Nunca recomenda fazer pela carteira digital ou direto em banco único.

## Arquivos principais

- `main.py`: webhook FastAPI da Venditore + follow-ups + aplicação das etiquetas no handoff.
- `agent.py`: fluxo conversacional e escolha do operador do rodízio.
- `sales_skill.py`: skill de vendedor CLT.
- `bank_rules.py`: regras extraídas do PDF.
- `storage.py`: memória em JSON por sessão e índice persistido do rodízio.
- `venditore.py`: API wts.chat, notas, mensagens e etiquetas.

## Memória no Railway

Para a memória e o rodízio de operadores não sumirem em deploy/restart, crie um Volume no Railway e configure:

`SESSION_DB_PATH=/data/sessions.json`

Sem Volume, funciona, mas a memória pode ser perdida em redeploy.

## Etiquetas Venditore

Por padrão o sistema tenta aplicar as etiquetas pelo nome:

- `digitar proposta`
- `Ryan`
- `Vitória`
- `Otávio`
- `Tatiane`
- `Bianca`

Se a conta Venditore exigir ID interno da etiqueta em vez de nome, configure no Railway:

- `VENDITORE_LABEL_DIGITAR_PROPOSTA_ID`
- `VENDITORE_LABEL_RYAN_ID`
- `VENDITORE_LABEL_VITORIA_ID`
- `VENDITORE_LABEL_OTAVIO_ID`
- `VENDITORE_LABEL_TATIANE_ID`
- `VENDITORE_LABEL_BIANCA_ID`

Mesmo se alguma etiqueta falhar, o sistema cria uma nota interna avisando as etiquetas necessárias.

## Webhook Venditore

Configurar na Venditore:

`https://SEU-PROJETO.up.railway.app/webhook/venditore`

## Segurança

Não subir `.env` nem token real para GitHub.
Tokens devem ficar apenas nas variáveis do Railway.
