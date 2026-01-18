"""
Script para dar todas as permissões a um usuário
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'serrana.settings')
django.setup()

from django.contrib.auth.models import User
from usuarios.models import Modulo, Menu, PermissaoMenu

print("=" * 80)
print("CONFIGURAÇÃO DE PERMISSÕES DE USUÁRIO")
print("=" * 80)

# Buscar o usuário
username = 'marcos@mbrtecnologia.com.br'
try:
    usuario = User.objects.get(username=username)
    print(f"\n✓ Usuário encontrado: {usuario.username}")
except User.DoesNotExist:
    print(f"\n❌ Usuário '{username}' não encontrado!")
    exit(1)

# Verificar módulos e menus
modulos = Modulo.objects.filter(ativo=True)
menus = Menu.objects.filter(ativo=True)

print(f"\n✓ Módulos ativos: {modulos.count()}")
print(f"✓ Menus ativos: {menus.count()}")

if modulos.count() == 0:
    print("\n⚠️  AVISO: Nenhum módulo cadastrado no sistema!")
    print("   Execute o script de inicialização de módulos primeiro.")
    exit(0)

if menus.count() == 0:
    print("\n⚠️  AVISO: Nenhum menu cadastrado no sistema!")
    print("   Execute o script de inicialização de menus primeiro.")
    exit(0)

# Listar módulos
print("\n=== MÓDULOS DISPONÍVEIS ===")
for modulo in modulos:
    menus_modulo = menus.filter(modulo=modulo)
    print(f"\n  📦 {modulo.nome} ({menus_modulo.count()} menus)")
    for menu in menus_modulo:
        print(f"     - {menu.nome} ({menu.url})")

# Criar permissões para todos os menus
print("\n" + "=" * 80)
print(f"CRIANDO PERMISSÕES COMPLETAS PARA: {usuario.username}")
print("=" * 80)

permissoes_criadas = 0
permissoes_atualizadas = 0

for menu in menus:
    # Verificar se já existe permissão
    permissao, created = PermissaoMenu.objects.update_or_create(
        tipo='usuario',
        usuario=usuario,
        menu=menu,
        defaults={
            'pode_visualizar': True,
            'pode_criar': True,
            'pode_editar': True,
            'pode_excluir': True,
        }
    )
    
    if created:
        permissoes_criadas += 1
        print(f"  ✅ Criada: {menu.modulo.nome} > {menu.nome}")
    else:
        permissoes_atualizadas += 1
        print(f"  🔄 Atualizada: {menu.modulo.nome} > {menu.nome}")

print("\n" + "=" * 80)
print("RESUMO")
print("=" * 80)
print(f"  Permissões criadas: {permissoes_criadas}")
print(f"  Permissões atualizadas: {permissoes_atualizadas}")
print(f"  Total de menus com permissão: {permissoes_criadas + permissoes_atualizadas}")
print("=" * 80)
print(f"\n✅ Usuário '{usuario.username}' agora tem ACESSO TOTAL a todos os módulos!")
