import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'serrana.settings')
django.setup()

from financeiro.models import ReguaCobranca
from usuarios.models import Empresa

print("=" * 60)
print("VERIFICANDO RÉGUAS NO BANCO DE DADOS")
print("=" * 60)

# Listar empresas
empresas = Empresa.objects.all()
print(f"\nTotal de Empresas: {empresas.count()}")
for e in empresas:
    print(f"  - ID: {e.id}, Razão Social: {e.razao_social}")

# Listar réguas
reguas = ReguaCobranca.objects.all()
print(f"\nTotal de Réguas: {reguas.count()}")
for r in reguas:
    print(f"  - ID: {r.id}")
    print(f"    Nome: {r.nome}")
    print(f"    Empresa: {r.empresa.razao_social} (ID: {r.empresa.id})")
    print(f"    Ativa: {r.ativa}")
    print(f"    Etapas: {r.etapas.count()}")
    print()

if reguas.count() == 0:
    print("⚠️  NENHUMA RÉGUA ENCONTRADA NO BANCO!")
    print("   Verifique se o formulário está salvando corretamente.")
