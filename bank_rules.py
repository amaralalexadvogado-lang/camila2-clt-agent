from dataclasses import dataclass

@dataclass(frozen=True)
class BankRule:
    banco: str
    idade: str
    prazo: str
    margem: str
    vinculo_min_meses: int
    tempo_cnpj: str
    valor: str
    parcela_min: str
    funcionarios_min: str
    contratos: str

BANK_RULES = [
    BankRule('VCTEX','21 a 65 anos','10, 12, 15, 18, 24 e 36','70% a 100% da margem',6,'3 anos','R$ 800 a R$ 12.500','—','Sem mínimo','3 por CPF'),
    BankRule('FACTA','Mulher: 21 a 57 / Homem: até 62','24 a 60','70%',9,'1 ano','R$ 500 a R$ 26.000','verificar particularidades no RO','—','1 por CPF'),
    BankRule('MERCANTIL','20 a 58 anos','1 a 36','Limitada ao valor máximo',12,'3 anos','R$ 200 a R$ 50.000','R$ 10,00','Sem mínimo','1 por CPF'),
    BankRule('C6 CONSIG','21 a 60 anos','6 a 48','até 35%',6,'2 anos','R$ 700 a R$ 120.000','—','30','9 por CPF'),
    BankRule('ZIPDIN','21 a 65 anos','6 a 48','80% da margem disponível',12,'2 anos','Mín. R$ 500 / Máx. mediante análise','R$ 50,00','300','8 por CPF'),
    BankRule('PRATA DIGITAL','21 a 65 anos','6 a 36','90% Celcoin / 70% QI',3,'2 anos','R$ 8.500','—','10','—'),
    BankRule('HAPPY','Mulher: 21 a 60 / Homem: até 65','6, 12, 18, 24, 36','35%',6,'2 anos','Máx. R$ 12.000','R$ 75,00','30','9 por CPF'),
    BankRule('HUB','18 a 60 anos','6, 12, 18, 24, 36 e 48','35%',6,'2 anos','R$ 500 a R$ 25.000','R$ 75,00','20','9 por CPF'),
    BankRule('EASYCRÉDITO','Mulher: 21 a 57 / Homem: até 62','6, 9, 12, 15, 18, 24','70%',24,'2 anos','R$ 500 a R$ 50.000','R$ 75,00','20','1 por CPF'),
    BankRule('BANCO PAN','Mulher: 18 a 57 / Homem: até 62','6 a 48','35%',6,'1 ano','R$ 1.000 a R$ 40.000','—','20','Até 9 por vínculo'),
    BankRule('FUTURO','Mulher: 20 a 59 / Homem: até 61','12, 18, 24 e 36','70%',6,'2 anos','R$ 200 a R$ 12.000','R$ 75,00','20','9 por vínculo trabalhista'),
    BankRule('FOX','Mulher: 21 a 57 / Homem: até 62','6, 9, 12, 15, 18, 24','70%',12,'2 anos','R$ 500 a R$ 50.000','R$ 75,00','20','1 por CPF'),
    BankRule('NEON','18 a 60 anos','até 84','35%',12,'6 meses','Mín. R$ 300 / Máx. mediante análise','—','30','Até 3 por CPF'),
    BankRule('BMG','18 a 60 anos','12 a 48','72,5% da margem disponível',5,'5 anos','R$ 500 a R$ 20.000','—','Sem mínimo','9 por CPF'),
    BankRule('CREFAZ','Mulher: 18 a 63a4m / Homem: até 65a4m','12 a 48','30% da bruta',6,'3 anos','R$ 1.000 a R$ 25.000','—','Sem mínimo','1 por CPF'),
]

def eligible_banks_by_tenure(months: int):
    return [r for r in BANK_RULES if months >= r.vinculo_min_meses]

def bank_card(months: int) -> str:
    eligible = eligible_banks_by_tenure(months)
    if not eligible:
        return ('CARD INTERNO — CLT\n'
                f'Vínculo informado: {months} mês(es).\n'
                'Banco possível: nenhum banco da tabela aprova com esse vínculo.\n'
                'Conduta: tratar com cuidado, explicar que precisamos de vínculo maior e manter relacionamento.')
    linhas = [
        'CARD INTERNO — CLT',
        f'Vínculo informado: {months} mês(es).',
        'Bancos possíveis pelo tempo de vínculo:',
    ]
    for r in eligible:
        linhas.append(f'- {r.banco}: mínimo {r.vinculo_min_meses} meses | valor {r.valor} | prazo {r.prazo} | margem {r.margem}')
    return '\n'.join(linhas)
