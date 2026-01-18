"""
Script para verificar permissões de um usuário
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'serrana.settings')
django.setup()

from django.contrib.auth.models import User
from usuarios.models import Modulo, Menu, PermissaoMenu

username = 'marcos@mbrtecnologia.com.br'

print("=" * 80)
print(f"DEBUG DE PERMISSÕES - {username}")
print("=" * 80)

try:
    user = User.objects.get(username=username)
    print(f"\n✓ Usuário: {user.username}")
    print(f"  Superuser: {user.is_superuser}")
    print(f"  Staff: {user.is_staff}")
    print(f"  Ativo: {user.is_active}")
    
    # Verificar permissões do usuário
    permissoes = PermissaoMenu.objects.filter(
        usuario=user,
        pode_visualizar=True,
        menu__ativo=True
    ).select_related('menu', 'menu__modulo')
    
    print(f"\n  Total de permissões: {permissoes.count()}")
    
    # Agrupar por módulo
    modulos_dict = {}
    for perm in permissoes:
        modulo_nome = perm.menu.modulo.nome
        if modulo_nome not in modulos_dict:
            modulos_dict[modulo_nome] = []
        modulos_dict[modulo_nome].append(perm.menu.nome)
    
    print("\n=== MÓDULOS E MENUS COM PERMISSÃO ===\n")
    for modulo_nome, menus in sorted(modulos_dict.items()):
        print(f"  📦 {modulo_nome} ({len(menus)} menus)")
        for menu_nome in menus:
            print(f"     - {menu_nome}")
    
    # Verificar menus de nível superior (sem pai)
    menus_nivel_superior = Menu.objects.filter(
        id__in=[p.menu.id for p in permissoes],
        menu_pai__isnull=True,
        ativo=True
    ).select_related('modulo')
    
    print(f"\n=== MENUS DE NÍVEL SUPERIOR (exibidos na home) ===\n")
    print(f"  Total: {menus_nivel_superior.count()}")
    
    modulos_com_menu_superior = {}
    for menu in menus_nivel_superior:
        modulo = menu.modulo
        if modulo.nome not in modulos_com_menu_superior:
            modulos_com_menu_superior[modulo.nome] = []
        modulos_com_menu_superior[modulo.nome].append(menu.nome)
    
    for modulo_nome, menus in sorted(modulos_com_menu_superior.items()):
        print(f"\n  📦 {modulo_nome}")
        for menu_nome in menus:
            print(f"     - {menu_nome}")
    
    print("\n" + "=" * 80)
    
    if menus_nivel_superior.count() == 0:
        print("❌ PROBLEMA: Usuário tem permissões mas nenhum menu de nível superior!")
        print("   Possíveis causas:")
        print("   1. Todos os menus têm menu_pai (são submenus)")
        print("   2. Os menus principais estão inativos")
    else:
        print(f"✅ OK: {menus_nivel_superior.count()} módulos serão exibidos na home")
    
    print("=" * 80)
    
except User.DoesNotExist:
    print(f"❌ Usuário '{username}' não encontrado!")
