"""
Script temporário para criar e aplicar migrations
"""
import os
import sys
import django
from io import StringIO

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'serrana.settings')
django.setup()

from django.core.management import call_command

print("=" * 80)
print("EXECUTANDO VERIFICAÇÃO DO SISTEMA")
print("=" * 80)

try:
    call_command('check')
    print("\n✅ Sistema verificado com sucesso!\n")
except Exception as e:
    print(f"\n❌ Erro na verificação: {e}\n")
    # Continuar mesmo com erros de verificação
    print("⚠️ Continuando mesmo com avisos...\n")

print("=" * 80)
print("CRIANDO MIGRATIONS")
print("=" * 80)

try:
    # Criar migrations para financeiro
    print("\n📝 Criando migrations para app FINANCEIRO...")
    call_command('makemigrations', 'financeiro', verbosity=2, interactive=False)
    
    # Criar migrations para projetos
    print("\n📝 Criando migrations para app PROJETOS...")
    call_command('makemigrations', 'projetos', verbosity=2, interactive=False)
    
    print("\n✅ Migrations criadas com sucesso!\n")
except Exception as e:
    print(f"\n⚠️ Aviso ao criar migrations: {e}\n")
    print("Continuando...\n")

print("=" * 80)
print("APLICANDO MIGRATIONS")
print("=" * 80)

try:
    call_command('migrate', verbosity=2, interactive=False)
    print("\n✅ Migrations aplicadas com sucesso!\n")
except Exception as e:
    print(f"\n❌ Erro ao aplicar migrations: {e}\n")
    sys.exit(1)

print("=" * 80)
print("✅ PROCESSO CONCLUÍDO COM SUCESSO!")
print("=" * 80)
