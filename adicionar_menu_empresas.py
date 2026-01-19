#!/usr/bin/env python
"""
Script para adicionar o menu "Empresas" ao painel do sistema.
Este script é idempotente - pode ser executado múltiplas vezes sem problemas.
"""
import os
import sys
import django

# Configurar Django
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'serrana.settings')
django.setup()

from usuarios.models import Modulo, Menu, PermissaoMenu
from django.contrib.auth.models import Group

def main():
    print("=" * 80)
    print("ADICIONANDO MENU 'EMPRESAS' AO PAINEL")
    print("=" * 80)
    
    # 1. Buscar módulo Usuários
    try:
        modulo_usuarios = Modulo.objects.get(nome='Usuários')
        print(f"\n✓ Módulo encontrado: {modulo_usuarios.nome}")
    except Modulo.DoesNotExist:
        print("\n❌ ERRO: Módulo 'Usuários' não encontrado!")
        return False
    
    # 2. Verificar se menu já existe
    menu, created = Menu.objects.get_or_create(
        modulo=modulo_usuarios,
        nome='Empresas',
        defaults={
            'descricao': 'Gestão de Empresas (Multiempresa)',
            'url': '/empresas/',
            'icone': 'fas fa-building',
            'ordem': 2,
            'ativo': True,
            'menu_pai': None
        }
    )
    
    if created:
        print(f"✓ Menu 'Empresas' criado com sucesso!")
    else:
        print(f"↻ Menu 'Empresas' já existia (ID: {menu.id})")
    
    print(f"   URL: {menu.url}")
    print(f"   Ícone: {menu.icone}")
    print(f"   Ordem: {menu.ordem}")
    print(f"   Ativo: {menu.ativo}")
    
    # 3. Atribuir permissão ao grupo Administrador
    grupo_admin = Group.objects.filter(name='Administrador').first()
    if grupo_admin:
        perm, perm_created = PermissaoMenu.objects.get_or_create(
            tipo='grupo',
            grupo=grupo_admin,
            menu=menu,
            defaults={
                'pode_visualizar': True,
                'pode_criar': True,
                'pode_editar': True,
                'pode_excluir': True,
            }
        )
        
        if perm_created:
            print(f"\n✓ Permissão criada para grupo 'Administrador'")
        else:
            print(f"\n↻ Permissão já existe para grupo 'Administrador'")
    else:
        print(f"\n⚠️  Grupo 'Administrador' não encontrado - permissões não atribuídas")
    
    # 4. Listar todos os menus do módulo Usuários
    print(f"\n📋 MENUS DO MÓDULO 'USUÁRIOS':")
    menus = Menu.objects.filter(modulo=modulo_usuarios, ativo=True).order_by('ordem')
    for m in menus:
        print(f"   {m.ordem}. {m.nome:20s} -> {m.url}")
    
    print("\n" + "=" * 80)
    print("✅ CONFIGURAÇÃO CONCLUÍDA COM SUCESSO!")
    print("=" * 80)
    print("\nO módulo 'Empresas' agora aparece no painel para:")
    print("  • Usuários superuser")
    print("  • Usuários do grupo 'Administrador'")
    print("  • Usuários com permissão específica no menu 'Empresas'")
    print("\n" + "=" * 80)
    
    return True

if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)
