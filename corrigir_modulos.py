"""
Script para corrigir módulos e menus do sistema
Remove/desativa módulos inexistentes (Importações)
Corrige URLs inválidas
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'serrana.settings')
django.setup()

from usuarios.models import Modulo, Menu, PermissaoMenu

print("=" * 80)
print("CORREÇÃO DE MÓDULOS E MENUS")
print("=" * 80)

# 1. Desativar módulo "Importações" que não existe
print("\n1. Desativando módulo 'Importações'...")
modulo_importacoes = Modulo.objects.filter(nome__icontains='importaç').first()
if modulo_importacoes:
    modulo_importacoes.ativo = False
    modulo_importacoes.save()
    print(f"   ✅ Módulo '{modulo_importacoes.nome}' desativado")
    
    # Desativar menus relacionados
    menus = Menu.objects.filter(modulo=modulo_importacoes)
    menus.update(ativo=False)
    print(f"   ✅ {menus.count()} menus desativados")
    
    # Remover permissões relacionadas
    permissoes = PermissaoMenu.objects.filter(menu__modulo=modulo_importacoes)
    count = permissoes.count()
    permissoes.delete()
    print(f"   ✅ {count} permissões removidas")
else:
    print("   ℹ️  Módulo 'Importações' não encontrado")

# 2. Verificar e corrigir módulo "Contas a Receber"
print("\n2. Verificando módulo 'Contas a Receber'...")
modulo_contas = Modulo.objects.filter(nome__icontains='contas a receber').first()
if modulo_contas:
    print(f"   ⚠️  Módulo '{modulo_contas.nome}' existe")
    print("   ℹ️  'Contas a Receber' deveria fazer parte do módulo 'Financeiro'")
    print("   ℹ️  Mantendo ativo por enquanto, mas considere reorganizar")
else:
    print("   ✅ Módulo separado 'Contas a Receber' não encontrado")

# 3. Listar módulos ativos
print("\n" + "=" * 80)
print("MÓDULOS ATIVOS NO SISTEMA")
print("=" * 80)

modulos_ativos = Modulo.objects.filter(ativo=True).order_by('ordem', 'nome')
for modulo in modulos_ativos:
    menus_count = Menu.objects.filter(modulo=modulo, ativo=True).count()
    print(f"\n📦 {modulo.nome}")
    print(f"   Ordem: {modulo.ordem}")
    print(f"   Menus ativos: {menus_count}")
    print(f"   Ícone: {modulo.icone}")

# 4. Verificar menus com URLs problemáticas
print("\n" + "=" * 80)
print("VERIFICANDO URLs DE MENUS")
print("=" * 80)

menus_problematicos = []
all_menus = Menu.objects.filter(ativo=True)

for menu in all_menus:
    # Verificar URLs que apontam para /importacoes/
    if '/importacoes/' in menu.url:
        menus_problematicos.append((menu, 'URL aponta para módulo inexistente'))
    # Verificar URLs que começam com /contas-receber/ (correto seria /financeiro/contas-receber/)
    elif menu.url.startswith('/contas-receber/'):
        menus_problematicos.append((menu, 'URL deveria começar com /financeiro/'))

print(f"\nTotal de menus ativos: {all_menus.count()}")
print(f"Menus com possíveis problemas: {len(menus_problematicos)}")

if menus_problematicos:
    print("\nDesativar menus problemáticos? (s/n)")
    # Desativar automaticamente
    for menu, problema in menus_problematicos:
        menu.ativo = False
        menu.save()
        print(f"   ⚠️  Desativado: {menu.modulo.nome} > {menu.nome}")
        print(f"      URL: {menu.url}")
        print(f"      Motivo: {problema}")

# 5. Resumo final
print("\n" + "=" * 80)
print("RESUMO FINAL")
print("=" * 80)

modulos_ativos = Modulo.objects.filter(ativo=True).count()
menus_ativos = Menu.objects.filter(ativo=True).count()
permissoes_ativas = PermissaoMenu.objects.filter(menu__ativo=True).count()

print(f"\n  Módulos ativos: {modulos_ativos}")
print(f"  Menus ativos: {menus_ativos}")
print(f"  Permissões ativas: {permissoes_ativas}")

print("\n✅ Correção concluída!")
print("   Execute 'python dar_permissoes_usuario.py' novamente para atualizar permissões")
print("=" * 80)
