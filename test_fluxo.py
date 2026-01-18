import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'serrana.settings')
django.setup()

from financeiro.services.calculadora import CalculadoraSaldos

print("Verificando CalculadoraSaldos...")
print(f"Classe: {CalculadoraSaldos}")
print(f"Tem fluxo_mensal: {'fluxo_mensal' in dir(CalculadoraSaldos)}")

if hasattr(CalculadoraSaldos, 'fluxo_mensal'):
    print(f"Tipo de fluxo_mensal: {type(CalculadoraSaldos.fluxo_mensal)}")
    print("✓ Método fluxo_mensal existe!")
else:
    print("✗ Método fluxo_mensal NÃO existe!")
    print("\nMétodos disponíveis:")
    for attr in dir(CalculadoraSaldos):
        if not attr.startswith('_'):
            print(f"  - {attr}")
