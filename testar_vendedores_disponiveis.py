"""
Script para testar se vendedores estão sendo buscados corretamente
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'serrana.settings')
django.setup()

from cadastros.models import Pessoa
from usuarios.models import Empresa

print("=" * 80)
print("TESTE: Busca de Vendedores para Orçamento")
print("=" * 80)

# Simular o que a view criar_orcamento_de_oportunidade faz
empresa = Empresa.objects.get(id=1)  # Empresa Serrana

print(f"\n📊 Empresa: {empresa.nome_fantasia} (ID: {empresa.id})")
print(f"   Ativa: {empresa.ativa}")

# Buscar vendedores exatamente como a view faz
vendedores = Pessoa.objects.filter(
    empresa=empresa,
    vendedor=True,
    ativo=True
)

print(f"\n👤 VENDEDORES DISPONÍVEIS: {vendedores.count()}")
print("-" * 80)

for v in vendedores:
    print(f"✓ {v.nome}")
    print(f"  CPF/CNPJ: {v.cpf_cnpj}")
    print(f"  Empresa: {v.empresa.nome_fantasia} (ID: {v.empresa.id})")
    print()

if vendedores.filter(nome__icontains='Carlos Eduardo').exists():
    print("✅ Carlos Eduardo Mendes ESTÁ DISPONÍVEL para orçamentos!")
else:
    print("❌ Carlos Eduardo Mendes NÃO ESTÁ DISPONÍVEL!")

print("=" * 80)
