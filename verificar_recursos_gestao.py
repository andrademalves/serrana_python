"""
Script para verificar onde estão os recursos de custos, impostos e budget
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'serrana.settings')
django.setup()

from usuarios.models import Modulo, Menu

print("=" * 80)
print("LOCALIZAÇÃO DOS RECURSOS DE GESTÃO")
print("=" * 80)

# Módulo Financeiro
modulo_financeiro = Modulo.objects.filter(nome__icontains='financeiro').first()

if modulo_financeiro:
    print(f"\n📁 MÓDULO: {modulo_financeiro.nome}")
    print(f"   Status: {'✅ Ativo' if modulo_financeiro.ativo else '❌ Inativo'}")
    
    menus_gestao = Menu.objects.filter(
        modulo=modulo_financeiro,
        ativo=True
    ).filter(
        nome__icontains__in=['tribut', 'custo', 'budget', 'imposto']
    ) | Menu.objects.filter(
        modulo=modulo_financeiro,
        ativo=True,
        nome__in=['Regime Tributário', 'Centros de Custo', 'Budget & Lucratividade', 'Classificação de Custos']
    )
    
    menus_gestao = Menu.objects.filter(modulo=modulo_financeiro, ativo=True).order_by('ordem')
    
    print(f"\n📋 MENUS DISPONÍVEIS ({menus_gestao.count()} itens):")
    
    # Destacar os menus de gestão
    menus_importantes = ['Regime Tributário', 'Centros de Custo', 'Budget & Lucratividade', 'Classificação de Custos']
    
    for menu in menus_gestao:
        destaque = '⭐' if any(imp.lower() in menu.nome.lower() for imp in menus_importantes) else '  '
        print(f"\n{destaque} {menu.nome}")
        print(f"     URL: {menu.url}")
        print(f"     Descrição: {menu.descricao or 'N/A'}")

print("\n" + "=" * 80)
print("COMO ACESSAR:")
print("=" * 80)
print("\n1. Faça login no sistema")
print("2. Clique no botão 'Módulos' no topo (ao lado de 'Trocar Empresa')")
print("3. Selecione o módulo 'Financeiro'")
print("4. No menu lateral, você verá:")
print("   ⭐ Regime Tributário - Gestão de impostos")
print("   ⭐ Centros de Custo - Gestão de centros de custo")
print("   ⭐ Budget & Lucratividade - Controle de budget")
print("   ⭐ Classificação de Custos - Custos fixos/variáveis")

print("\n" + "=" * 80)
print("MODELOS NO BANCO DE DADOS:")
print("=" * 80)

from financeiro.models import RegimeTributario, AliquotaImposto, CentroCusto, CategoriaCustoVariabilidade

print(f"\n✓ RegimeTributario: {RegimeTributario.objects.count()} registros")
print(f"✓ AliquotaImposto: {AliquotaImposto.objects.count()} registros")
print(f"✓ CentroCusto: {CentroCusto.objects.count()} registros")
print(f"✓ CategoriaCustoVariabilidade: {CategoriaCustoVariabilidade.objects.count()} registros")

print("\n" + "=" * 80)
print("ROTAS DE BUDGET:")
print("=" * 80)

from django.urls import get_resolver

resolver = get_resolver()
print("\nBudget está configurado em: /financeiro/budget/")
print("\nExemplos de URLs:")
print("  • /financeiro/budget/dashboard/ - Dashboard de budget")
print("  • /admin/financeiro/regimetributario/ - Admin de impostos")
print("  • /admin/financeiro/centrocusto/ - Admin de centros de custo")

print("\n" + "=" * 80)
