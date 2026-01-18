"""
Script para investigar e corrigir problema do Dashboard BI
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'serrana.settings')
django.setup()

from usuarios.models import Modulo, Menu

print("=" * 80)
print("INVESTIGANDO PROBLEMA DO DASHBOARD BI")
print("=" * 80)

# Verificar todos os menus com URL /dashboard/
menus_dashboard = Menu.objects.filter(url='/dashboard/', ativo=True)

print(f"\n📊 Menus com URL '/dashboard/':")
print(f"   Total encontrado: {menus_dashboard.count()}\n")

for menu in menus_dashboard:
    print(f"   • {menu.nome}")
    print(f"     Módulo: {menu.modulo.nome}")
    print(f"     URL: {menu.url}")
    print(f"     ID: {menu.id}")
    print(f"     Ordem: {menu.ordem}")
    print()

# Verificar módulos Dashboard e Usuários
print("=" * 80)
print("MÓDULOS ENVOLVIDOS")
print("=" * 80)

modulo_dashboard = Modulo.objects.filter(nome__icontains='dashboard').first()
modulo_usuarios = Modulo.objects.filter(nome__icontains='usuário').first()

if modulo_dashboard:
    print(f"\n📦 Módulo: {modulo_dashboard.nome}")
    print(f"   ID: {modulo_dashboard.id}")
    print(f"   Ordem: {modulo_dashboard.ordem}")
    print(f"   Ativo: {modulo_dashboard.ativo}")
    menus = Menu.objects.filter(modulo=modulo_dashboard, ativo=True)
    print(f"   Menus ativos: {menus.count()}")
    for m in menus:
        print(f"     - {m.nome} ({m.url})")

if modulo_usuarios:
    print(f"\n👥 Módulo: {modulo_usuarios.nome}")
    print(f"   ID: {modulo_usuarios.id}")
    print(f"   Ordem: {modulo_usuarios.ordem}")
    print(f"   Ativo: {modulo_usuarios.ativo}")
    menus = Menu.objects.filter(modulo=modulo_usuarios, ativo=True)
    print(f"   Menus ativos: {menus.count()}")
    for m in menus:
        print(f"     - {m.nome} ({m.url})")

print("\n" + "=" * 80)
print("SOLUÇÃO")
print("=" * 80)

# Identificar o menu duplicado no módulo Usuários
menu_duplicado = Menu.objects.filter(
    modulo=modulo_usuarios,
    url='/dashboard/',
    ativo=True
).first()

if menu_duplicado:
    print(f"\n⚠️  PROBLEMA IDENTIFICADO!")
    print(f"   Menu duplicado encontrado:")
    print(f"   - Nome: {menu_duplicado.nome}")
    print(f"   - Módulo: {menu_duplicado.modulo.nome}")
    print(f"   - URL: {menu_duplicado.url}")
    print(f"\n   Este menu deveria estar no módulo 'Dashboard BI', não em 'Usuários'")
    
    print(f"\n✅ APLICANDO CORREÇÃO...")
    
    # Desativar o menu duplicado em Usuários
    menu_duplicado.ativo = False
    menu_duplicado.save()
    
    print(f"   ✅ Menu '{menu_duplicado.nome}' desativado no módulo Usuários")
    
    # Garantir que existe menu no Dashboard BI
    menu_dashboard_bi = Menu.objects.filter(
        modulo=modulo_dashboard,
        ativo=True
    ).first()
    
    if not menu_dashboard_bi:
        print(f"   ⚠️  Nenhum menu ativo no Dashboard BI!")
        print(f"   Criando menu principal...")
        
        Menu.objects.create(
            modulo=modulo_dashboard,
            nome='Dashboard Principal',
            descricao='Business Intelligence - Visão Geral do Negócio',
            url='/dashboard/',
            icone='bi bi-speedometer2',
            ordem=1,
            ativo=True
        )
        print(f"   ✅ Menu criado no Dashboard BI")
    else:
        print(f"   ✅ Menu já existe no Dashboard BI: {menu_dashboard_bi.nome}")

print("\n" + "=" * 80)
print("ESTRUTURA FINAL")
print("=" * 80)

modulos = Modulo.objects.filter(ativo=True).order_by('ordem', 'nome')
for modulo in modulos:
    menus = Menu.objects.filter(modulo=modulo, ativo=True)
    if menus.count() > 0:
        print(f"\n📦 {modulo.nome}")
        for m in menus:
            print(f"   • {m.nome} → {m.url}")

print("\n" + "=" * 80)
print("✅ CORREÇÃO CONCLUÍDA!")
print("=" * 80)
print("\n⚠️  Execute 'python adicionar_dashboard_modulo.py' novamente")
print("   para atualizar as permissões dos usuários")
print("=" * 80)
