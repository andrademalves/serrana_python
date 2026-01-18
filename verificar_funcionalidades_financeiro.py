"""
Script para verificar funcionalidades faltantes e criar menus
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'serrana.settings')
django.setup()

from usuarios.models import Modulo, Menu

print("=" * 80)
print("VERIFICAÇÃO DE FUNCIONALIDADES - FINANCEIRO")
print("=" * 80)

# Verificar módulo Financeiro
modulo_financeiro = Modulo.objects.filter(nome__icontains='financeiro').first()

if modulo_financeiro:
    print(f"\n✓ Módulo Financeiro encontrado: {modulo_financeiro.nome}")
    
    menus = Menu.objects.filter(modulo=modulo_financeiro, ativo=True)
    print(f"\n=== MENUS ATUAIS ({menus.count()}) ===")
    for menu in menus:
        print(f"  • {menu.nome} → {menu.url}")
    
    # Verificar se existem menus de impostos e custos
    tem_impostos = menus.filter(nome__icontains='impost').exists()
    tem_tributos = menus.filter(nome__icontains='tribut').exists()
    tem_custos = menus.filter(nome__icontains='custo').exists()
    tem_budget = menus.filter(nome__icontains='budget').exists()
    tem_centro_custo = menus.filter(nome__icontains='centro').exists()
    
    print(f"\n=== VERIFICAÇÃO DE FUNCIONALIDADES ===")
    print(f"  {'✅' if tem_impostos else '❌'} Impostos")
    print(f"  {'✅' if tem_tributos else '❌'} Regime Tributário")
    print(f"  {'✅' if tem_custos else '❌'} Custos")
    print(f"  {'✅' if tem_budget else '❌'} Budget/Controle de Lucratividade")
    print(f"  {'✅' if tem_centro_custo else '❌'} Centro de Custo")
    
    if not (tem_impostos or tem_tributos or tem_custos or tem_budget or tem_centro_custo):
        print(f"\n⚠️  PROBLEMA: Funcionalidades financeiras avançadas NÃO estão no menu!")
        print(f"\n📋 CRIANDO MENUS FALTANTES...")
        
        menus_para_criar = [
            {
                'nome': 'Regime Tributário',
                'descricao': 'Configurar regimes tributários e alíquotas de impostos',
                'url': '/admin/financeiro/regimetributario/',
                'icone': 'bi bi-receipt',
                'ordem': 10
            },
            {
                'nome': 'Centros de Custo',
                'descricao': 'Gerenciar centros de custo da empresa',
                'url': '/admin/financeiro/centrocusto/',
                'icone': 'bi bi-diagram-3',
                'ordem': 11
            },
            {
                'nome': 'Budget & Lucratividade',
                'descricao': 'Controle de budget e análise de lucratividade',
                'url': '/financeiro/budget/dashboard/',
                'icone': 'bi bi-graph-up-arrow',
                'ordem': 12
            },
            {
                'nome': 'Classificação de Custos',
                'descricao': 'Classificar categorias como fixas ou variáveis',
                'url': '/admin/financeiro/categoriacustovariabilidade/',
                'icone': 'bi bi-tags',
                'ordem': 13
            }
        ]
        
        for menu_data in menus_para_criar:
            menu, created = Menu.objects.get_or_create(
                modulo=modulo_financeiro,
                nome=menu_data['nome'],
                defaults={
                    'descricao': menu_data['descricao'],
                    'url': menu_data['url'],
                    'icone': menu_data['icone'],
                    'ordem': menu_data['ordem'],
                    'ativo': True
                }
            )
            
            if created:
                print(f"  ✅ Criado: {menu.nome}")
            else:
                print(f"  ℹ️  Já existe: {menu.nome}")
    
    print(f"\n=== MENUS FINAIS ({Menu.objects.filter(modulo=modulo_financeiro, ativo=True).count()}) ===")
    for menu in Menu.objects.filter(modulo=modulo_financeiro, ativo=True).order_by('ordem'):
        print(f"  {menu.ordem}. {menu.nome} → {menu.url}")

print("\n" + "=" * 80)
print("✅ VERIFICAÇÃO CONCLUÍDA")
print("=" * 80)
print("\n⚠️  Atualize as permissões dos usuários executando:")
print("   python adicionar_dashboard_modulo.py")
print("=" * 80)
