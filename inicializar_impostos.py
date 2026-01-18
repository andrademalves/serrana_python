"""
Script para popular alíquotas de impostos padrão
Execute: python inicializar_impostos.py
"""

import os
import django

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'serrana.settings')
django.setup()

from financeiro.models import RegimeTributario, AliquotaImposto
from usuarios.models import Empresa
from django.contrib.auth.models import User

print("=" * 70)
print("INICIALIZAÇÃO DE REGIMES TRIBUTÁRIOS E ALÍQUOTAS DE IMPOSTOS")
print("=" * 70)

# ============================================================================
# 1. CRIAR REGIMES TRIBUTÁRIOS
# ============================================================================

print("\n[1] Criando Regimes Tributários...")

regimes_data = [
    {
        'nome': 'SIMPLES_NACIONAL',
        'descricao': 'Regime Simples Nacional - Unificação de impostos federais, estaduais e municipais'
    },
    {
        'nome': 'LUCRO_PRESUMIDO',
        'descricao': 'Lucro Presumido - Base de cálculo simplificada sobre faturamento'
    },
    {
        'nome': 'LUCRO_REAL',
        'descricao': 'Lucro Real - Base de cálculo sobre o lucro contábil efetivo'
    },
    {
        'nome': 'MEI',
        'descricao': 'Microempreendedor Individual - Regime simplificado com valor fixo mensal'
    },
]

regimes_criados = {}

for regime_data in regimes_data:
    regime, created = RegimeTributario.objects.get_or_create(
        nome=regime_data['nome'],
        defaults={'descricao': regime_data['descricao']}
    )
    regimes_criados[regime_data['nome']] = regime
    status = "✓ Criado" if created else "→ Já existe"
    print(f"{status}: {regime.get_nome_display()}")

print(f"\nTotal de regimes: {RegimeTributario.objects.count()}")


# ============================================================================
# 2. CRIAR ALÍQUOTAS PADRÃO PARA SIMPLES NACIONAL
# ============================================================================

print("\n[2] Criando Alíquotas para SIMPLES NACIONAL (Comércio/Indústria)...")

# Obter primeira empresa ou criar uma de exemplo
empresa = Empresa.objects.first()

if not empresa:
    print("\n⚠️  AVISO: Nenhuma empresa encontrada no sistema.")
    print("   Por favor, crie uma empresa primeiro ou modifique este script.")
    empresa_exemplo = {
        'razao_social': 'Empresa Exemplo LTDA',
        'nome_fantasia': 'Exemplo',
        'cnpj': '00.000.000/0001-00',
        'slug': 'exemplo'
    }
    print(f"   Criando empresa exemplo: {empresa_exemplo['razao_social']}")
    empresa = Empresa.objects.create(**empresa_exemplo)

print(f"Empresa selecionada: {empresa.nome_fantasia}")

# SIMPLES NACIONAL - Anexo I (Comércio)
# Faixa de receita: até R$ 180.000 → Alíquota 4%
regime_simples = regimes_criados['SIMPLES_NACIONAL']

aliquotas_simples = [
    {
        'tipo_imposto': 'ICMS',
        'aliquota_percentual': 1.25,
        'base_calculo': 'FATURAMENTO',
        'observacao': 'ICMS incluído no Simples Nacional - Anexo I'
    },
    {
        'tipo_imposto': 'ISS',
        'aliquota_percentual': 0.00,  # Não aplica para comércio
        'base_calculo': 'FATURAMENTO',
        'observacao': 'ISS não aplica para comércio no Simples'
    },
    {
        'tipo_imposto': 'PIS',
        'aliquota_percentual': 0.00,  # Unificado no Simples
        'base_calculo': 'FATURAMENTO',
        'observacao': 'PIS incluído na alíquota única do Simples'
    },
    {
        'tipo_imposto': 'COFINS',
        'aliquota_percentual': 0.00,  # Unificado no Simples
        'base_calculo': 'FATURAMENTO',
        'observacao': 'COFINS incluído na alíquota única do Simples'
    },
]

for aliquota_data in aliquotas_simples:
    aliquota, created = AliquotaImposto.objects.get_or_create(
        empresa=empresa,
        regime_tributario=regime_simples,
        tipo_imposto=aliquota_data['tipo_imposto'],
        defaults={
            'aliquota_percentual': aliquota_data['aliquota_percentual'],
            'base_calculo': aliquota_data['base_calculo'],
            'observacao': aliquota_data['observacao']
        }
    )
    status = "✓" if created else "→"
    print(f"{status} {aliquota.get_tipo_imposto_display()}: {aliquota.aliquota_percentual}%")


# ============================================================================
# 3. CRIAR ALÍQUOTAS PADRÃO PARA LUCRO PRESUMIDO
# ============================================================================

print("\n[3] Criando Alíquotas para LUCRO PRESUMIDO...")

regime_presumido = regimes_criados['LUCRO_PRESUMIDO']

aliquotas_presumido = [
    {
        'tipo_imposto': 'IRPJ',
        'aliquota_percentual': 1.20,  # 15% sobre 8% de presunção = 1.20%
        'base_calculo': 'FATURAMENTO',
        'observacao': 'IRPJ 15% sobre base de 8% do faturamento'
    },
    {
        'tipo_imposto': 'CSLL',
        'aliquota_percentual': 1.08,  # 9% sobre 12% de presunção = 1.08%
        'base_calculo': 'FATURAMENTO',
        'observacao': 'CSLL 9% sobre base de 12% do faturamento'
    },
    {
        'tipo_imposto': 'PIS',
        'aliquota_percentual': 0.65,
        'base_calculo': 'FATURAMENTO',
        'observacao': 'PIS regime cumulativo'
    },
    {
        'tipo_imposto': 'COFINS',
        'aliquota_percentual': 3.00,
        'base_calculo': 'FATURAMENTO',
        'observacao': 'COFINS regime cumulativo'
    },
    {
        'tipo_imposto': 'ICMS',
        'aliquota_percentual': 18.00,
        'base_calculo': 'FATURAMENTO',
        'observacao': 'ICMS alíquota estadual padrão (varia por estado)'
    },
    {
        'tipo_imposto': 'ISS',
        'aliquota_percentual': 5.00,
        'base_calculo': 'FATURAMENTO',
        'observacao': 'ISS para serviços (varia por município - média 2-5%)'
    },
]

for aliquota_data in aliquotas_presumido:
    aliquota, created = AliquotaImposto.objects.get_or_create(
        empresa=empresa,
        regime_tributario=regime_presumido,
        tipo_imposto=aliquota_data['tipo_imposto'],
        defaults={
            'aliquota_percentual': aliquota_data['aliquota_percentual'],
            'base_calculo': aliquota_data['base_calculo'],
            'observacao': aliquota_data['observacao']
        }
    )
    status = "✓" if created else "→"
    print(f"{status} {aliquota.get_tipo_imposto_display()}: {aliquota.aliquota_percentual}%")


# ============================================================================
# 4. CRIAR ALÍQUOTAS PADRÃO PARA LUCRO REAL
# ============================================================================

print("\n[4] Criando Alíquotas para LUCRO REAL...")

regime_real = regimes_criados['LUCRO_REAL']

aliquotas_real = [
    {
        'tipo_imposto': 'IRPJ',
        'aliquota_percentual': 15.00,  # + adicional de 10% sobre lucro > R$ 20.000/mês
        'base_calculo': 'LUCRO',
        'observacao': 'IRPJ 15% sobre lucro real (+ adicional 10% se > R$ 20k/mês)'
    },
    {
        'tipo_imposto': 'CSLL',
        'aliquota_percentual': 9.00,
        'base_calculo': 'LUCRO',
        'observacao': 'CSLL 9% sobre lucro real'
    },
    {
        'tipo_imposto': 'PIS',
        'aliquota_percentual': 1.65,
        'base_calculo': 'FATURAMENTO',
        'observacao': 'PIS regime não cumulativo (com direito a crédito)'
    },
    {
        'tipo_imposto': 'COFINS',
        'aliquota_percentual': 7.60,
        'base_calculo': 'FATURAMENTO',
        'observacao': 'COFINS regime não cumulativo (com direito a crédito)'
    },
    {
        'tipo_imposto': 'ICMS',
        'aliquota_percentual': 18.00,
        'base_calculo': 'FATURAMENTO',
        'observacao': 'ICMS alíquota estadual padrão (varia por estado)'
    },
    {
        'tipo_imposto': 'ISS',
        'aliquota_percentual': 5.00,
        'base_calculo': 'FATURAMENTO',
        'observacao': 'ISS para serviços (varia por município)'
    },
]

for aliquota_data in aliquotas_real:
    aliquota, created = AliquotaImposto.objects.get_or_create(
        empresa=empresa,
        regime_tributario=regime_real,
        tipo_imposto=aliquota_data['tipo_imposto'],
        defaults={
            'aliquota_percentual': aliquota_data['aliquota_percentual'],
            'base_calculo': aliquota_data['base_calculo'],
            'observacao': aliquota_data['observacao']
        }
    )
    status = "✓" if created else "→"
    print(f"{status} {aliquota.get_tipo_imposto_display()}: {aliquota.aliquota_percentual}%")


# ============================================================================
# 5. ATRIBUIR REGIME À EMPRESA
# ============================================================================

print("\n[5] Configurando regime tributário da empresa...")

if not empresa.regime_tributario:
    # Definir Simples Nacional como padrão
    empresa.regime_tributario = regime_simples
    empresa.save()
    print(f"✓ Empresa '{empresa.nome_fantasia}' configurada com {regime_simples.get_nome_display()}")
else:
    print(f"→ Empresa já possui regime: {empresa.regime_tributario.get_nome_display()}")


# ============================================================================
# 6. RESUMO
# ============================================================================

print("\n" + "=" * 70)
print("RESUMO DA INICIALIZAÇÃO")
print("=" * 70)

print(f"\n📊 Regimes Tributários: {RegimeTributario.objects.count()}")

for regime in RegimeTributario.objects.all():
    total_aliquotas = AliquotaImposto.objects.filter(
        regime_tributario=regime,
        empresa=empresa
    ).count()
    print(f"   • {regime.get_nome_display()}: {total_aliquotas} alíquotas configuradas")

print(f"\n🏢 Empresa: {empresa.nome_fantasia}")
print(f"   Regime: {empresa.regime_tributario.get_nome_display() if empresa.regime_tributario else 'Não configurado'}")

if empresa.regime_tributario:
    print(f"\n💰 Alíquotas Ativas para {empresa.nome_fantasia}:")
    aliquotas_ativas = AliquotaImposto.objects.filter(
        empresa=empresa,
        regime_tributario=empresa.regime_tributario,
        ativo=True
    )
    
    total_percentual = sum(a.aliquota_percentual for a in aliquotas_ativas)
    
    for aliquota in aliquotas_ativas:
        print(f"   • {aliquota.get_tipo_imposto_display():20} {aliquota.aliquota_percentual:6.2f}% "
              f"(base: {aliquota.get_base_calculo_display()})")
    
    print(f"\n   📈 Carga tributária total aproximada: {total_percentual:.2f}%")

print("\n" + "=" * 70)
print("✅ INICIALIZAÇÃO CONCLUÍDA COM SUCESSO!")
print("=" * 70)

print("\n💡 PRÓXIMOS PASSOS:")
print("   1. Ajustar alíquotas conforme a realidade da sua empresa")
print("   2. Configurar alíquotas específicas para outras empresas do sistema")
print("   3. Testar cálculo de impostos com CalculadoraImpostos.calcular_impostos_venda()")

print("\n📝 EXEMPLO DE USO:")
print("""
from financeiro.services_budget import CalculadoraImpostos

resultado = CalculadoraImpostos.calcular_impostos_venda(
    empresa=empresa,
    valor_venda=10000
)

print(f"Valor venda: R$ {resultado['valor_liquido']:.2f}")
print(f"Total impostos: R$ {resultado['total_impostos']:.2f}")
for imp in resultado['impostos']:
    print(f"  - {imp['tipo']}: R$ {imp['valor']:.2f}")
""")

print("\n" + "=" * 70)
