"""
Script para debugar problema de vendedor não aparecendo
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'serrana.settings')
django.setup()

from cadastros.models import Pessoa
from usuarios.models import Empresa
from django.contrib.auth.models import User

print("=" * 80)
print("DEBUG: Vendedores cadastrados")
print("=" * 80)

# Listar todas as empresas
print("\n📊 EMPRESAS CADASTRADAS:")
for empresa in Empresa.objects.all():
    print(f"  - ID: {empresa.id} | {empresa.nome_fantasia} | Ativa: {empresa.ativa}")

# Listar todos os vendedores
print("\n👤 VENDEDORES CADASTRADOS:")
vendedores = Pessoa.objects.filter(vendedor=True)
if vendedores.exists():
    for v in vendedores:
        print(f"  - {v.nome}")
        print(f"    Empresa: {v.empresa.nome_fantasia} (ID: {v.empresa.id})")
        print(f"    Ativo: {v.ativo}")
        print(f"    CPF/CNPJ: {v.cpf_cnpj}")
        print()
else:
    print("  ❌ Nenhum vendedor encontrado!")

# Procurar especificamente Carlos Eduardo Mendes
print("\n🔍 BUSCANDO 'Carlos Eduardo Mendes':")
carlos = Pessoa.objects.filter(nome__icontains='Carlos Eduardo')
if carlos.exists():
    for pessoa in carlos:
        print(f"  - {pessoa.nome}")
        print(f"    Empresa: {pessoa.empresa.nome_fantasia} (ID: {pessoa.empresa.id})")
        print(f"    Vendedor: {pessoa.vendedor}")
        print(f"    Cliente: {pessoa.cliente}")
        print(f"    Ativo: {pessoa.ativo}")
        print()
else:
    print("  ❌ Não encontrado!")

# Verificar usuários
print("\n👥 USUÁRIOS DO SISTEMA:")
for user in User.objects.all():
    print(f"  - {user.username} (ID: {user.id})")
    
print("\n" + "=" * 80)
