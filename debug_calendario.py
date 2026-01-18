"""Script para debugar calendário"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'serrana.settings')
django.setup()

from financeiro.models import ParcelaFinanceira, TituloFinanceiro
from datetime import date
from cadastros.models import Empresa
from decimal import Decimal

emp = Empresa.objects.first()
print(f"Empresa: {emp.nome_fantasia}")

primeiro_dia = date(2026, 1, 1)
ultimo_dia = date(2026, 1, 31)

parcelas = ParcelaFinanceira.objects.filter(
    titulo__empresa=emp,
    data_vencimento__gte=primeiro_dia,
    data_vencimento__lte=ultimo_dia,
    status__in=['ABERTO', 'PARCIAL', 'QUITADO']
).select_related('titulo', 'titulo__pessoa')

print(f"\nTotal de parcelas em janeiro/2026: {parcelas.count()}")

# Organiza por tipo
eventos_por_dia = {}
for dia in range(1, 32):
    eventos_por_dia[dia] = {
        'a_pagar': [],
        'a_receber': [],
        'total_pagar': Decimal('0.00'),
        'total_receber': Decimal('0.00'),
    }

for parcela in parcelas:
    dia = parcela.data_vencimento.day
    print(f"\nParcela {parcela.id}:")
    print(f"  Data: {parcela.data_vencimento}")
    print(f"  Tipo do título: '{parcela.titulo.tipo}'")
    print(f"  Pessoa: {parcela.titulo.pessoa.nome if parcela.titulo.pessoa else 'Sem pessoa'}")
    print(f"  Valor: R$ {parcela.valor_original}")
    print(f"  Status: {parcela.status}")
    
    if parcela.titulo.tipo == 'PAGAR':
        eventos_por_dia[dia]['a_pagar'].append(parcela)
        print(f"  -> Adicionado em A PAGAR")
    else:
        eventos_por_dia[dia]['a_receber'].append(parcela)
        print(f"  -> Adicionado em A RECEBER")

# Resumo
total_pagar = sum(len(eventos_por_dia[d]['a_pagar']) for d in range(1, 32))
total_receber = sum(len(eventos_por_dia[d]['a_receber']) for d in range(1, 32))

print(f"\n\n=== RESUMO ===")
print(f"Total a pagar: {total_pagar}")
print(f"Total a receber: {total_receber}")

print(f"\n\n=== DIAS COM EVENTOS ===")
for dia in range(1, 32):
    if eventos_por_dia[dia]['a_pagar'] or eventos_por_dia[dia]['a_receber']:
        print(f"\nDia {dia}:")
        print(f"  A pagar: {len(eventos_por_dia[dia]['a_pagar'])}")
        print(f"  A receber: {len(eventos_por_dia[dia]['a_receber'])}")
