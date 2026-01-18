"""
Script para adicionar módulo Dashboard se não existir e dar permissões
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'serrana.settings')
django.setup()

from usuarios.models import Modulo, Menu, PermissaoMenu
from django.contrib.auth.models import User

print("=" * 80)
print("VERIFICANDO E ADICIONANDO MÓDULO DASHBOARD")
print("=" * 80)

# Verificar se módulo Dashboard existe
dashboard_modulo = Modulo.objects.filter(nome__icontains='dashboard').first()

if not dashboard_modulo:
    print("\n⚠️  Módulo Dashboard não encontrado")
    print("   Criando...")
    
    dashboard_modulo = Modulo.objects.create(
        nome='Dashboard BI',
        descricao='Business Intelligence e Relatórios Gerenciais',
        icone='bi bi-graph-up',
        ordem=0,  # Primeiro módulo
        ativo=True
    )
    print(f"   ✅ Módulo '{dashboard_modulo.nome}' criado")
    
    # Criar menu principal
    menu_dashboard = Menu.objects.create(
        modulo=dashboard_modulo,
        nome='Dashboard Principal',
        descricao='Visão geral do negócio',
        url='/dashboard/',
        icone='bi bi-speedometer2',
        ordem=1,
        ativo=True
    )
    print(f"   ✅ Menu '{menu_dashboard.nome}' criado")
    
else:
    print(f"\n✓ Módulo Dashboard já existe: {dashboard_modulo.nome}")
    print(f"  Ativo: {dashboard_modulo.ativo}")
    
    menus = Menu.objects.filter(modulo=dashboard_modulo, ativo=True)
    print(f"  Menus ativos: {menus.count()}")

# Listar todos os módulos finais
print("\n" + "=" * 80)
print("MÓDULOS DO SISTEMA (em ordem)")
print("=" * 80)

modulos = Modulo.objects.filter(ativo=True).order_by('ordem', 'nome')
for modulo in modulos:
    menus_count = Menu.objects.filter(modulo=modulo, ativo=True).count()
    print(f"\n  {modulo.ordem}. 📦 {modulo.nome}")
    print(f"     Ícone: {modulo.icone}")
    print(f"     Menus: {menus_count}")

# Dar permissões aos usuários
print("\n" + "=" * 80)
print("ATUALIZANDO PERMISSÕES DOS USUÁRIOS")
print("=" * 80)

usuarios = ['admin', 'marcos', 'marcos@mbrtecnologia.com.br']
all_menus = Menu.objects.filter(ativo=True)

for username in usuarios:
    try:
        user = User.objects.get(username=username)
        
        for menu in all_menus:
            PermissaoMenu.objects.update_or_create(
                tipo='usuario',
                usuario=user,
                menu=menu,
                defaults={
                    'pode_visualizar': True,
                    'pode_criar': True,
                    'pode_editar': True,
                    'pode_excluir': True,
                }
            )
        
        print(f"  ✅ {username}: {all_menus.count()} permissões configuradas")
        
    except User.DoesNotExist:
        print(f"  ⚠️  Usuário '{username}' não encontrado")

print("\n" + "=" * 80)
print("✅ CONCLUÍDO!")
print("=" * 80)
