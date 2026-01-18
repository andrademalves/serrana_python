"""
Verificação final de permissões do usuário marcos@mbrtecnologia.com.br
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'serrana.settings')
django.setup()

from django.contrib.auth.models import User
from usuarios.models import Modulo, Menu, PermissaoMenu

username = 'marcos@mbrtecnologia.com.br'

print("=" * 80)
print(f"VERIFICAÇÃO FINAL - {username}")
print("=" * 80)

user = User.objects.get(username=username)

print(f"\n✅ STATUS DO USUÁRIO")
print(f"{'=' * 80}")
print(f"  Username: {user.username}")
print(f"  Nome: {user.first_name} {user.last_name}".strip())
print(f"  Email: {user.email}")
print(f"  Superuser: {'✅ SIM' if user.is_superuser else '❌ NÃO'}")
print(f"  Staff: {'✅ SIM' if user.is_staff else '❌ NÃO'}")
print(f"  Ativo: {'✅ SIM' if user.is_active else '❌ NÃO'}")

print(f"\n✅ PERMISSÕES DE ACESSO")
print(f"{'=' * 80}")

if user.is_superuser:
    print("  🔓 ACESSO TOTAL AO SISTEMA")
    print("     - Pode acessar TODOS os módulos")
    print("     - Pode gerenciar empresas")
    print("     - Pode criar/editar usuários")
    print("     - Pode acessar o painel admin Django")
    print("     - Não precisa de permissões específicas por menu")
else:
    permissoes = PermissaoMenu.objects.filter(
        usuario=user,
        menu__ativo=True
    ).select_related('menu', 'menu__modulo')
    
    modulos_dict = {}
    for perm in permissoes:
        modulo = perm.menu.modulo.nome
        if modulo not in modulos_dict:
            modulos_dict[modulo] = []
        modulos_dict[modulo].append({
            'menu': perm.menu.nome,
            'visualizar': perm.pode_visualizar,
            'criar': perm.pode_criar,
            'editar': perm.pode_editar,
            'excluir': perm.pode_excluir,
        })
    
    print(f"\n  Total de menus com permissão: {permissoes.count()}")
    print(f"  Módulos com acesso: {len(modulos_dict)}")

print(f"\n✅ MÓDULOS DISPONÍVEIS")
print(f"{'=' * 80}")

modulos = Modulo.objects.filter(ativo=True).order_by('ordem', 'nome')
for modulo in modulos:
    menus = Menu.objects.filter(modulo=modulo, ativo=True)
    print(f"\n  📦 {modulo.nome} ({menus.count()} menus)")
    
    # Mostrar status de acesso
    if user.is_superuser:
        print(f"     ✅ ACESSO TOTAL")
    else:
        tem_acesso = PermissaoMenu.objects.filter(
            usuario=user,
            menu__modulo=modulo,
            menu__ativo=True,
            pode_visualizar=True
        ).exists()
        print(f"     {'✅' if tem_acesso else '❌'} {'Tem acesso' if tem_acesso else 'Sem acesso'}")

print(f"\n✅ FUNCIONALIDADES ESPECIAIS")
print(f"{'=' * 80}")

funcionalidades = {
    'Gerenciar Empresas': user.is_superuser,
    'Acessar Painel Admin': user.is_staff,
    'Criar Usuários': user.is_superuser,
    'Ver Dashboard BI': True,  # Todos podem ver
    'Exportar Relatórios': user.is_superuser or user.is_staff,
}

for func, tem_acesso in funcionalidades.items():
    print(f"  {'✅' if tem_acesso else '❌'} {func}")

print(f"\n{'=' * 80}")
print("RESUMO")
print(f"{'=' * 80}")

if user.is_superuser and user.is_staff:
    print("\n  🎉 USUÁRIO COM PODERES ADMINISTRATIVOS COMPLETOS!")
    print("\n  Pode:")
    print("    ✅ Acessar todos os módulos do sistema")
    print("    ✅ Gerenciar empresas (criar, editar, excluir)")
    print("    ✅ Gerenciar usuários e permissões")
    print("    ✅ Acessar o painel admin Django")
    print("    ✅ Ver e gerar relatórios")
    print("    ✅ Executar qualquer operação no sistema")
elif user.is_staff:
    print("\n  👤 USUÁRIO STAFF (acesso parcial)")
elif user.is_superuser:
    print("\n  🔓 USUÁRIO SUPERUSER")
else:
    print("\n  👤 USUÁRIO COMUM")

print(f"\n  ⚠️  LEMBRE-SE:")
print(f"     Faça LOGOUT e LOGIN novamente para aplicar as mudanças!")
print(f"\n{'=' * 80}")
