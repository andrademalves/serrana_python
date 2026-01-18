"""
Script para verificar usuários, empresas e vínculos no sistema
"""
import os
import django

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'serrana.settings')
django.setup()

from django.contrib.auth.models import User
from usuarios.models import Empresa, UsuarioEmpresa

print("=" * 80)
print("VERIFICAÇÃO DE USUÁRIOS E EMPRESAS")
print("=" * 80)

# 1. Usuários
print("\n=== USUÁRIOS ===")
users = User.objects.all()
if users.exists():
    for u in users:
        print(f"  ID: {u.id} | Username: {u.username} | Superuser: {u.is_superuser} | Ativo: {u.is_active}")
else:
    print("  Nenhum usuário encontrado")

# 2. Empresas
print("\n=== EMPRESAS ===")
empresas = Empresa.objects.all()
if empresas.exists():
    for e in empresas:
        print(f"  ID: {e.id} | {e.nome_fantasia} | CNPJ: {e.cnpj} | Ativa: {e.ativa}")
else:
    print("  Nenhuma empresa encontrada")

# 3. Vínculos
print("\n=== VÍNCULOS (UsuarioEmpresa) ===")
vinculos = UsuarioEmpresa.objects.all()
if vinculos.exists():
    for v in vinculos:
        print(f"  User: {v.usuario.username} -> Empresa: {v.empresa.nome_fantasia} | Ativo: {v.ativo}")
else:
    print("  Nenhum vínculo encontrado")

print("\n" + "=" * 80)
print("DIAGNÓSTICO")
print("=" * 80)

if not users.exists():
    print("⚠️  PROBLEMA: Nenhum usuário cadastrado")
    print("   SOLUÇÃO: Crie um superusuário com: python manage.py createsuperuser")
elif not empresas.exists():
    print("⚠️  PROBLEMA: Nenhuma empresa cadastrada")
    print("   SOLUÇÃO: Cadastre uma empresa via Admin ou crie via script")
elif not vinculos.exists():
    print("⚠️  PROBLEMA: Usuários sem vínculo com empresas")
    print("   SOLUÇÃO: Criar vínculo UsuarioEmpresa")
    
    # Criar vínculo automaticamente se houver 1 usuário e 1 empresa
    if users.count() == 1 and empresas.count() == 1:
        user = users.first()
        empresa = empresas.first()
        print(f"\n   Criando vínculo automático: {user.username} -> {empresa.nome_fantasia}")
        
        vinculo = UsuarioEmpresa.objects.create(
            usuario=user,
            empresa=empresa,
            ativo=True,
            papel='Administrador'
        )
        print(f"   ✅ Vínculo criado com sucesso!")
else:
    print("✅ Sistema OK - Usuários e empresas vinculados corretamente")

print("=" * 80)
