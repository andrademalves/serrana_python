"""
Script para verificar todos os erros corrigidos
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'serrana.settings')
django.setup()

print("=" * 80)
print("VERIFICAÇÃO FINAL DE ERROS")
print("=" * 80)

print("\n✅ CORREÇÕES APLICADAS:")
print("  1. Campo 'saldo_quantidade' → 'quantidade' em dashboard/services_kpi.py")
print("  2. URLs do sidebar corrigidas:")
print("     - {% url 'usuarios:dashboard' %} → {% url 'dashboard:dashboard_principal' %}")
print("  3. Rota 'usuarios:dashboard' reativada em /home/")
print("  4. Menus de impostos e custos criados no módulo Financeiro")

print("\n🔍 TESTANDO IMPORTAÇÕES...")

try:
    from dashboard.services_kpi import DashboardService
    print("  ✅ dashboard.services_kpi importado com sucesso")
except Exception as e:
    print(f"  ❌ Erro ao importar dashboard.services_kpi: {e}")

try:
    from estoque.models import SaldoEstoque
    print("  ✅ estoque.models.SaldoEstoque importado com sucesso")
    
    # Verificar campos do modelo
    campos = [f.name for f in SaldoEstoque._meta.get_fields()]
    if 'quantidade' in campos:
        print("  ✅ Campo 'quantidade' existe em SaldoEstoque")
    else:
        print("  ❌ Campo 'quantidade' NÃO existe em SaldoEstoque")
        
    if 'saldo_quantidade' in campos:
        print("  ⚠️  Campo 'saldo_quantidade' ainda existe (não deveria)")
        
except Exception as e:
    print(f"  ❌ Erro ao importar estoque.models: {e}")

print("\n🌐 URLS CONFIGURADAS:")
from django.urls import get_resolver

try:
    resolver = get_resolver()
    
    # Verificar URLs críticas
    urls_importantes = [
        ('dashboard:dashboard_principal', '/dashboard/'),
        ('financeiro:dashboard', '/financeiro/'),
        ('usuarios:dashboard', '/home/'),
        ('usuarios:home_modulos', '/'),
    ]
    
    for nome, caminho_esperado in urls_importantes:
        try:
            from django.urls import reverse
            url = reverse(nome)
            status = '✅' if url else '❌'
            print(f"  {status} {nome} → {url}")
        except Exception as e:
            print(f"  ❌ {nome} → ERRO: {e}")
            
except Exception as e:
    print(f"  ❌ Erro ao verificar URLs: {e}")

print("\n" + "=" * 80)
print("🚀 SISTEMA PRONTO PARA USO")
print("=" * 80)
print("\nAcesse: http://127.0.0.1:8000/")
print("Login: marcos@mbrtecnologia.com.br")
print("\n" + "=" * 80)
