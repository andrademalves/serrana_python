import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'serrana.settings')
django.setup()

from usuarios.models import Modulo, Menu, PermissaoMenu
from django.contrib.auth.models import User

print("=" * 80)
print("CORREÇÃO DO DASHBOARD BI - RELATÓRIO FINAL")
print("=" * 80)

print("\n🔍 PROBLEMA IDENTIFICADO:")
print("   Menu duplicado: 'Dashboard' estava em 2 módulos")
print("   • Módulo Usuários (ID: 1) → /dashboard/")
print("   • Módulo Dashboard BI (ID: 39) → /dashboard/")

print("\n✅ SOLUÇÃO APLICADA:")
print("   1. ❌ Menu do módulo 'Usuários' DESATIVADO")
print("   2. ✅ Menu do módulo 'Dashboard BI' MANTIDO ATIVO")
print("   3. 🔄 Permissões dos usuários ATUALIZADAS")

print("\n📊 ESTRUTURA FINAL:")
modulos = Modulo.objects.filter(ativo=True).order_by('ordem', 'nome')
for m in modulos:
    menus_count = Menu.objects.filter(modulo=m, ativo=True).count()
    print(f"   {m.ordem}. 📦 {m.nome} ({menus_count} menus)")

print("\n👤 USUÁRIO: marcos@mbrtecnologia.com.br")
u = User.objects.get(username='marcos@mbrtecnologia.com.br')
perms = PermissaoMenu.objects.filter(usuario=u, menu__ativo=True).count()
print(f"   • Permissões ativas: {perms} menus")
print(f"   • Superuser: {'✅ SIM' if u.is_superuser else '❌ NÃO'}")

print("\n" + "=" * 80)
print("✅ CORREÇÃO CONCLUÍDA!")
print("=" * 80)
print("\n⚠️  PRÓXIMO PASSO:")
print("   Faça LOGOUT e LOGIN novamente no navegador")
print("   O módulo 'Dashboard BI' agora aparecerá corretamente")
print("\n" + "=" * 80)
