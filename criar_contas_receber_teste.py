"""Script para criar contas a receber de teste"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'serrana.settings')
django.setup()

from financeiro.models import TituloFinanceiro, ParcelaFinanceira, PlanoConta
from cadastros.models import Empresa, Pessoa
from datetime import date, timedelta
from decimal import Decimal

# Pega empresa
empresa = Empresa.objects.first()
print(f"Empresa: {empresa.nome_fantasia}")

# Pega ou cria um plano de contas de receita
plano_receita = PlanoConta.objects.filter(
    empresa=empresa,
    tipo='RECEITA',
    aceita_lancamento=True
).first()

if not plano_receita:
    print("ERRO: Não encontrou plano de contas de receita!")
    exit()

print(f"Plano de Contas: {plano_receita.nome}")

# Pega algumas pessoas (clientes)
clientes = Pessoa.objects.filter(empresa=empresa, tipo='CLIENTE')[:3]

if not clientes:
    print("ERRO: Não encontrou clientes cadastrados!")
    exit()

print(f"\nEncontrou {len(clientes)} clientes")

# Cria títulos a receber
for i, cliente in enumerate(clientes, 1):
    # Cria título
    titulo = TituloFinanceiro.objects.create(
        empresa=empresa,
        tipo='RECEBER',  # IMPORTANTE: Tipo RECEBER
        numero_documento=f'NF-{2000+i}',
        descricao=f'Venda para {cliente.nome}',
        pessoa=cliente,
        plano_conta=plano_receita,
        data_emissao=date.today(),
        data_primeiro_vencimento=date(2026, 1, 5 + (i*5)),  # Dias 5, 10, 15
        valor_total=Decimal('1500.00') * i,
        num_parcelas=1,
        status='ABERTO'
    )
    
    # Cria parcela
    parcela = ParcelaFinanceira.objects.create(
        titulo=titulo,
        numero_parcela=1,
        data_vencimento=date(2026, 1, 5 + (i*5)),
        valor_original=Decimal('1500.00') * i,
        saldo_aberto=Decimal('1500.00') * i,
        status='ABERTO'
    )
    
    print(f"\n✅ Criado: {titulo.numero_documento}")
    print(f"   Tipo: {titulo.tipo}")
    print(f"   Cliente: {cliente.nome}")
    print(f"   Vencimento: {parcela.data_vencimento}")
    print(f"   Valor: R$ {parcela.valor_original}")

print("\n\n=== VERIFICAÇÃO ===")
titulos_receber = TituloFinanceiro.objects.filter(
    empresa=empresa,
    tipo='RECEBER',
    data_primeiro_vencimento__gte=date(2026, 1, 1),
    data_primeiro_vencimento__lte=date(2026, 1, 31)
)
print(f"Total de títulos a RECEBER em janeiro/2026: {titulos_receber.count()}")

parcelas_receber = ParcelaFinanceira.objects.filter(
    titulo__empresa=empresa,
    titulo__tipo='RECEBER',
    data_vencimento__gte=date(2026, 1, 1),
    data_vencimento__lte=date(2026, 1, 31)
)
print(f"Total de parcelas a RECEBER em janeiro/2026: {parcelas_receber.count()}")
