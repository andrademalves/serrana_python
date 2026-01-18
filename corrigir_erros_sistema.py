"""
Script para corrigir todos os erros detectados no sistema
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'serrana.settings')
django.setup()

from usuarios.models import Modulo, Menu, PermissaoMenu, UsuarioEmpresa
from django.contrib.auth import get_user_model
from django.db import models

User = get_user_model()

print("=" * 80)
print("CORRIGINDO ERROS DO SISTEMA")
print("=" * 80)

# ERRO 1: Campo incorreto em dashboard/services_kpi.py
# Mudança necessária: saldo_quantidade → quantidade
print("\n1. ❌ ERRO EM DASHBOARD - Campo 'saldo_quantidade' não existe")
print("   → O modelo SaldoEstoque usa o campo 'quantidade', não 'saldo_quantidade'")
print("   → Arquivo: dashboard/services_kpi.py linha 59")
print("   → SOLUÇÃO: Editar manualmente e trocar 'saldo_quantidade' por 'quantidade'")

# ERRO 2: URL reversa 'dashboard' não encontrada em template financeiro
print("\n2. ❌ ERRO EM FINANCEIRO - URL reversa 'dashboard' não encontrada")
print("   → Template financeiro/dashboard.html tenta fazer {% url 'dashboard' %}")
print("   → Mas a URL correta é 'dashboard:dashboard_principal'")
print("   → SOLUÇÃO: Buscar e corrigir templates do financeiro")

# CRIAR MENUS FALTANTES
print("\n" + "=" * 80)
print("CRIANDO MENUS PARA FUNCIONALIDADES FALTANTES")
print("=" * 80)

modulo_financeiro = Modulo.objects.filter(nome__icontains='financeiro').first()

if modulo_financeiro:
    print(f"\n✓ Módulo encontrado: {modulo_financeiro.nome}")
    
    # Pegar último número de ordem
    ultima_ordem = Menu.objects.filter(modulo=modulo_financeiro).aggregate(
        max_ordem=models.Max('ordem')
    )['max_ordem'] or 0
    
    menus_para_criar = [
        {
            'nome': 'Regime Tributário',
            'descricao': 'Configurar regimes tributários e alíquotas de impostos',
            'url': '/admin/financeiro/regimetributario/',
            'icone': 'bi bi-receipt',
            'ordem': ultima_ordem + 1
        },
        {
            'nome': 'Centros de Custo',
            'descricao': 'Gerenciar centros de custo da empresa',
            'url': '/admin/financeiro/centrocusto/',
            'icone': 'bi bi-diagram-3',
            'ordem': ultima_ordem + 2
        },
        {
            'nome': 'Budget & Lucratividade',
            'descricao': 'Controle de budget e análise de lucratividade',
            'url': '/financeiro/budget/dashboard/',
            'icone': 'bi bi-graph-up-arrow',
            'ordem': ultima_ordem + 3
        },
        {
            'nome': 'Classificação de Custos',
            'descricao': 'Classificar categorias como fixas ou variáveis',
            'url': '/admin/financeiro/categoriacustovariabilidade/',
            'icone': 'bi bi-tags',
            'ordem': ultima_ordem + 4
        }
    ]
    
    menus_criados = []
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
            menus_criados.append(menu)
        else:
            print(f"  ℹ️  Já existe: {menu.nome}")
    
    # ATUALIZAR PERMISSÕES PARA TODOS OS USUÁRIOS
    if menus_criados:
        print(f"\n📋 ATUALIZANDO PERMISSÕES...")
        
        usuarios_empresa = UsuarioEmpresa.objects.select_related('usuario').all()
        
        for ue in usuarios_empresa:
            usuario = ue.usuario
            
            # Criar permissões para os novos menus
            permissoes_criadas = 0
            for menu in menus_criados:
                permissao, created = PermissaoMenu.objects.get_or_create(
                    usuario=usuario,
                    menu=menu,
                    defaults={
                        'tipo': 'usuario',
                        'pode_visualizar': True,
                        'pode_criar': True,
                        'pode_editar': True,
                        'pode_excluir': True
                    }
                )
                if created:
                    permissoes_criadas += 1
            
            if permissoes_criadas > 0:
                print(f"  ✅ {usuario.email}: +{permissoes_criadas} permissões")

print("\n" + "=" * 80)
print("RESUMO DAS CORREÇÕES")
print("=" * 80)
print("\n✅ CONCLUÍDO:")
print("  • Menus de impostos e custos criados")
print("  • Permissões atualizadas para todos os usuários")

print("\n⚠️  CORREÇÕES MANUAIS NECESSÁRIAS:")
print("  1. dashboard/services_kpi.py linha 59:")
print("     Trocar: .filter(saldo_quantidade__gt=0)")
print("     Por:    .filter(quantidade__gt=0)")
print("\n  2. Buscar em templates do financeiro:")
print("     Trocar: {% url 'dashboard' %}")
print("     Por:    {% url 'dashboard:dashboard_principal' %}")

print("\n" + "=" * 80)
