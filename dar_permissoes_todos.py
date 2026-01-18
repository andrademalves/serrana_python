"""
Script para dar permissões completas aos usuários admin e marcos
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'serrana.settings')
django.setup()

from django.contrib.auth.models import User
from usuarios.models import Menu, PermissaoMenu

print("=" * 80)
print("DANDO PERMISSÕES PARA TODOS OS USUÁRIOS")
print("=" * 80)

# Usuários para dar permissão
usernames = ['admin', 'marcos']
menus = Menu.objects.filter(ativo=True)

for username in usernames:
    try:
        usuario = User.objects.get(username=username)
        print(f"\n{'=' * 80}")
        print(f"Usuário: {usuario.username}")
        print('=' * 80)
        
        for menu in menus:
            PermissaoMenu.objects.update_or_create(
                tipo='usuario',
                usuario=usuario,
                menu=menu,
                defaults={
                    'pode_visualizar': True,
                    'pode_criar': True,
                    'pode_editar': True,
                    'pode_excluir': True,
                }
            )
        
        print(f"✅ {menus.count()} permissões configuradas!")
        
    except User.DoesNotExist:
        print(f"\n⚠️  Usuário '{username}' não encontrado, pulando...")

print("\n" + "=" * 80)
print("✅ CONCLUÍDO!")
print("=" * 80)
