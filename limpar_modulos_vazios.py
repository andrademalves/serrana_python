"""
Script para limpar módulos vazios e reorganizar
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'serrana.settings')
django.setup()

from usuarios.models import Modulo, Menu, PermissaoMenu

print("=" * 80)
print("LIMPEZA FINAL DE MÓDULOS")
print("=" * 80)

# Desativar módulos sem menus ativos
modulos = Modulo.objects.filter(ativo=True)

for modulo in modulos:
    menus_count = Menu.objects.filter(modulo=modulo, ativo=True).count()
    
    if menus_count == 0:
        print(f"\n⚠️  Módulo '{modulo.nome}' não tem menus ativos")
        print(f"   Desativando...")
        modulo.ativo = False
        modulo.save()
        print(f"   ✅ Desativado")

# Listar módulos finais
print("\n" + "=" * 80)
print("MÓDULOS ATIVOS FINAL")
print("=" * 80)

modulos_ativos = Modulo.objects.filter(ativo=True).order_by('ordem', 'nome')
for modulo in modulos_ativos:
    menus_count = Menu.objects.filter(modulo=modulo, ativo=True).count()
    print(f"\n📦 {modulo.nome} ({menus_count} menus)")

print("\n" + "=" * 80)
print("✅ Limpeza concluída!")
print("=" * 80)
