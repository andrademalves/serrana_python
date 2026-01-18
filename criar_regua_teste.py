import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'serrana.settings')
django.setup()

from financeiro.models import ReguaCobranca, ReguaEtapa
from usuarios.models import Empresa

print("=" * 60)
print("CRIANDO RÉGUA DE COBRANÇA DE TESTE")
print("=" * 60)

# Pegar primeira empresa
empresa = Empresa.objects.first()
print(f"\nEmpresa: {empresa.razao_social} (ID: {empresa.id})")

# Criar régua
regua, created = ReguaCobranca.objects.get_or_create(
    nome="Régua Padrão - 3 Etapas",
    empresa=empresa,
    defaults={
        'descricao': 'Régua de cobrança padrão com 3 etapas: lembrete, cobrança e última chamada',
        'ativa': True
    }
)

if created:
    print(f"✓ Régua criada: {regua.nome}")
    
    # Criar etapas
    etapas_config = [
        {
            'ordem': 1,
            'nome': 'Lembrete Pré-Vencimento',
            'offset_dias': -3,
            'assunto_email': 'Lembrete: Sua parcela vence em 3 dias',
            'template_email': '''Olá {cliente_nome},

Este é um lembrete amigável sobre sua parcela que vencerá em breve.

Parcela: {parcela_numero}/{parcela_total}
Valor: R$ {parcela_valor}
Vencimento: {data_vencimento}

Agradecemos sua atenção!

Atenciosamente,
{empresa_nome}''',
            'enviar_email': True,
            'ativo': True
        },
        {
            'ordem': 2,
            'nome': 'Cobrança Vencimento',
            'offset_dias': 0,
            'assunto_email': 'Parcela vence hoje - {documento_numero}',
            'template_email': '''Olá {cliente_nome},

Sua parcela vence hoje. Por favor, providencie o pagamento.

Parcela: {parcela_numero}/{parcela_total}
Valor: R$ {parcela_valor}
Vencimento: HOJE ({data_vencimento})

Atenciosamente,
{empresa_nome}''',
            'enviar_email': True,
            'ativo': True
        },
        {
            'ordem': 3,
            'nome': 'Cobrança Pós-Vencimento (+7 dias)',
            'offset_dias': 7,
            'assunto_email': 'URGENTE: Parcela vencida há 7 dias',
            'template_email': '''Olá {cliente_nome},

Sua parcela está vencida há 7 dias. Solicitamos regularização urgente.

Parcela: {parcela_numero}/{parcela_total}
Valor: R$ {parcela_valor}
Vencimento: {data_vencimento}
Dias em atraso: 7

Por favor, entre em contato para regularizar.

Atenciosamente,
{empresa_nome}''',
            'enviar_email': True,
            'ativo': True
        }
    ]
    
    for etapa_config in etapas_config:
        etapa = ReguaEtapa.objects.create(
            regua=regua,
            **etapa_config
        )
        print(f"  ✓ Etapa {etapa.ordem}: {etapa.nome} ({etapa.offset_dias:+d} dias)")
    
    print(f"\n✅ Régua criada com sucesso com {len(etapas_config)} etapas!")
else:
    print(f"ℹ️  Régua já existe: {regua.nome}")
    print(f"   Etapas: {regua.etapas.count()}")

print("\n" + "=" * 60)
print("Agora você pode:")
print("1. Acessar http://127.0.0.1:8000/financeiro/cobranca/reguas/")
print("2. Ver a régua criada e editá-la se necessário")
print("3. Criar um título a receber e selecionar esta régua")
print("=" * 60)
