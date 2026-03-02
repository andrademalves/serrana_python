"""
Script para criar migration e adicionar campo vendedor ao PerfilUsuario
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'serrana.settings')
django.setup()

print("=" * 80)
print("CRIANDO MIGRATION: PERFIL VENDEDOR")
print("=" * 80)

import subprocess
import sys

# Criar migration
print("\n1️⃣ Criando migration para campo 'vendedor' em PerfilUsuario...")
result = subprocess.run(
    [sys.executable, 'manage.py', 'makemigrations', 'usuarios'],
    capture_output=True,
    text=True
)

print(result.stdout)
if result.stderr:
    print(result.stderr)

if result.returncode != 0:
    print("❌ Erro ao criar migration")
    sys.exit(1)

# Aplicar migration
print("\n2️⃣ Aplicando migration...")
result = subprocess.run(
    [sys.executable, 'manage.py', 'migrate', 'usuarios'],
    capture_output=True,
    text=True
)

print(result.stdout)
if result.stderr:
    print(result.stderr)

if result.returncode != 0:
    print("❌ Erro ao aplicar migration")
    sys.exit(1)

print("\n" + "=" * 80)
print("✅ MIGRATION APLICADA COM SUCESSO!")
print("=" * 80)
print("\n📝 Agora você pode:")
print("   • Editar um usuário no Admin Django")
print("   • Marcar a opção 'É Vendedor' no perfil")
print("   • O sistema criará/vinculará automaticamente o registro de Pessoa")
print("=" * 80)
