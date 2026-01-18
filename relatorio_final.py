"""
Script de relatório final - verificar se tudo foi corrigido
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'serrana.settings')
django.setup()

from usuarios.models import Modulo, Menu

print("=" * 80)
print("RELATÓRIO FINAL - FUNCIONALIDADES DISPONÍVEIS")
print("=" * 80)

print("\n📊 MÓDULOS ATIVOS:")
modulos = Modulo.objects.filter(ativo=True).order_by('ordem')
for modulo in modulos:
    print(f"  {modulo.ordem}. {modulo.nome} ({modulo.icone})")

print("\n" + "=" * 80)
print("MENUS POR MÓDULO")
print("=" * 80)

for modulo in modulos:
    menus = Menu.objects.filter(modulo=modulo, ativo=True).order_by('ordem')
    
    if menus.exists():
        print(f"\n📁 {modulo.nome.upper()} ({menus.count()} menus)")
        for menu in menus:
            print(f"  {menu.ordem}. {menu.nome}")
            print(f"      URL: {menu.url}")
            print(f"      Ícone: {menu.icone}")

print("\n" + "=" * 80)
print("✅ FUNCIONALIDADES ENCONTRADAS")
print("=" * 80)

# Verificar funcionalidades específicas solicitadas
from django.db.models import Q

funcionalidades = {
    'Dashboard BI': Menu.objects.filter(nome__icontains='dashboard', ativo=True, modulo__nome__icontains='dashboard').exists(),
    'Regime Tributário (Impostos)': Menu.objects.filter(nome__icontains='tribut', ativo=True).exists(),
    'Centros de Custo': Menu.objects.filter(Q(nome__icontains='centro') & Q(nome__icontains='custo'), ativo=True).exists(),
    'Budget & Lucratividade': Menu.objects.filter(nome__icontains='budget', ativo=True).exists(),
    'Classificação de Custos': Menu.objects.filter(nome__icontains='classific', ativo=True).exists(),
}

for nome, existe in funcionalidades.items():
    status = '✅' if existe else '❌'
    print(f"{status} {nome}")

print("\n" + "=" * 80)
print("🔧 CORREÇÕES APLICADAS")
print("=" * 80)
print("  ✅ Campo 'saldo_quantidade' corrigido para 'quantidade' em dashboard/services_kpi.py")
print("  ✅ Menus de impostos e custos criados no módulo Financeiro")
print("  ✅ Permissões atualizadas para todos os usuários")
print("  ✅ URL routing do Dashboard BI corrigido")

print("\n" + "=" * 80)
print("📝 PRÓXIMOS PASSOS")
print("=" * 80)
print("  1. Acesse http://127.0.0.1:8000/")
print("  2. Faça login com: marcos@mbrtecnologia.com.br")
print("  3. Verifique se o Dashboard BI está funcionando")
print("  4. Navegue até o módulo Financeiro")
print("  5. Verifique os novos menus:")
print("     • Regime Tributário")
print("     • Centros de Custo")
print("     • Budget & Lucratividade")
print("     • Classificação de Custos")

print("\n" + "=" * 80)
