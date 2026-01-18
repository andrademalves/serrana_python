"""
Script para verificar e corrigir módulos cadastrados no sistema
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'serrana.settings')
django.setup()

from usuarios.models import Modulo, Menu

print("=" * 80)
print("ANÁLISE DE MÓDULOS E APPS DO PROJETO")
print("=" * 80)

# Apps Django reais do projeto
apps_reais = [
    'usuarios',
    'cadastros', 
    'estoque',
    'financeiro',
    'projetos',
    'vendas',
    'dashboard'
]

print("\n=== APPS REAIS DO PROJETO ===")
for app in apps_reais:
    print(f"  ✓ {app}")

# Módulos cadastrados no banco
print("\n" + "=" * 80)
print("MÓDULOS CADASTRADOS NO BANCO DE DADOS")
print("=" * 80)

modulos_db = Modulo.objects.all().order_by('ordem', 'nome')
print(f"\nTotal: {modulos_db.count()} módulos\n")

for modulo in modulos_db:
    menus = Menu.objects.filter(modulo=modulo, ativo=True)
    print(f"\n📦 {modulo.nome}")
    print(f"   Ativo: {modulo.ativo}")
    print(f"   Menus: {menus.count()}")
    
    if menus.count() > 0:
        for menu in menus[:3]:  # Mostrar só os 3 primeiros
            print(f"   - {menu.nome} ({menu.url})")
        if menus.count() > 3:
            print(f"   ... e mais {menus.count() - 3} menus")

# Identificar módulos que não correspondem aos apps
print("\n" + "=" * 80)
print("ANÁLISE DE CORRESPONDÊNCIA")
print("=" * 80)

modulos_invalidos = []
for modulo in modulos_db:
    nome_lower = modulo.nome.lower().replace(' ', '')
    
    # Mapear nomes de módulos para apps
    mapeamento = {
        'usuários': 'usuarios',
        'cadastros': 'cadastros',
        'estoque': 'estoque',
        'financeiro': 'financeiro',
        'contasareceber': 'financeiro',  # Faz parte do financeiro
        'orçamentoseprojetos': 'projetos',
        'importações': None,  # Não existe
        'sistema': 'usuarios',  # Parte de usuários
        'dashboard': 'dashboard',
    }
    
    app_correspondente = mapeamento.get(nome_lower)
    
    if app_correspondente is None:
        modulos_invalidos.append(modulo)
        print(f"\n❌ MÓDULO INVÁLIDO: {modulo.nome}")
        print(f"   Este módulo não corresponde a nenhum app do projeto!")
        print(f"   Deve ser desativado ou removido")

if len(modulos_invalidos) == 0:
    print("\n✅ Todos os módulos correspondem aos apps do projeto")

# Verificar menus com URLs inválidas
print("\n" + "=" * 80)
print("VERIFICANDO URLs DE MENUS")
print("=" * 80)

menus_com_problema = []
all_menus = Menu.objects.filter(ativo=True)

for menu in all_menus:
    url = menu.url
    
    # URLs que podem ser problemáticas
    if 'importacoes' in url.lower():
        menus_com_problema.append((menu, 'URL aponta para app inexistente (importações)'))
    elif url.startswith('/contas-receber/') and not url.startswith('financeiro:'):
        # contas a receber faz parte do financeiro
        menus_com_problema.append((menu, 'Contas a receber deveria fazer parte do financeiro'))

if menus_com_problema:
    print(f"\n⚠️  {len(menus_com_problema)} menus com possíveis problemas:\n")
    for menu, problema in menus_com_problema:
        print(f"  • {menu.modulo.nome} > {menu.nome}")
        print(f"    URL: {menu.url}")
        print(f"    Problema: {problema}\n")
else:
    print("\n✅ Nenhum problema identificado nas URLs")

print("\n" + "=" * 80)
print("AÇÕES RECOMENDADAS")
print("=" * 80)

if modulos_invalidos:
    print("\n1. DESATIVAR MÓDULOS INVÁLIDOS:")
    for modulo in modulos_invalidos:
        print(f"   - {modulo.nome}")

if menus_com_problema:
    print(f"\n2. CORRIGIR/DESATIVAR {len(menus_com_problema)} MENUS PROBLEMÁTICOS")

print("\n3. ESTRUTURA CORRETA DEVERIA SER:")
print("   • Usuários (usuarios)")
print("   • Cadastros (cadastros)")
print("   • Estoque (estoque)")
print("   • Financeiro (financeiro)")
print("   • Projetos (projetos)")
print("   • Vendas (vendas)")
print("   • Dashboard (dashboard)")

print("\n" + "=" * 80)
