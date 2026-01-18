"""
Script para desativar o módulo Dashboard BI
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'serrana.settings')
django.setup()

from usuarios.models import Modulo, Menu

print("=" * 80)
print("REMOVENDO DASHBOARD BI")
print("=" * 80)

# Desativar módulo Dashboard BI
modulo_dashboard = Modulo.objects.filter(nome__icontains='Dashboard BI').first()

if modulo_dashboard:
    print(f"\n✓ Módulo encontrado: {modulo_dashboard.nome}")
    
    # Desativar menus
    menus = Menu.objects.filter(modulo=modulo_dashboard)
    count = menus.update(ativo=False)
    print(f"  ✓ {count} menu(s) desativado(s)")
    
    # Desativar módulo
    modulo_dashboard.ativo = False
    modulo_dashboard.save()
    print(f"  ✓ Módulo '{modulo_dashboard.nome}' desativado")
else:
    print("\n⚠️  Módulo Dashboard BI não encontrado")

print("\n" + "=" * 80)
print("✅ DASHBOARD BI REMOVIDO COM SUCESSO")
print("=" * 80)
print("\nO sistema agora redireciona para a tela de módulos inicial.")
print("=" * 80)
