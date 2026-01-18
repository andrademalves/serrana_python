import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'serrana.settings')
django.setup()

from projetos.models import OrcamentoItem
from projetos.templatetags.projetos_tags import get_item_original_name

print("=" * 70)
print("TESTE: Template tag get_item_original_name")
print("=" * 70)

# Criar item mock com item_ref = produto_1
item = OrcamentoItem(
    tipo='PRODUTO',
    item_ref='produto_1',
    item_codigo='123',
    descricao='material para porta x'
)

print(f"\nItem criado:")
print(f"  - tipo: {item.tipo}")
print(f"  - item_ref: {item.item_ref}")
print(f"  - item_codigo: {item.item_codigo}")
print(f"  - descricao: {item.descricao}")

# Testar o filtro
resultado = get_item_original_name(item)

print(f"\nResultado do filtro:")
print(f"  {resultado}")

print("\n" + "=" * 70)
if " - " in resultado:
    print("✅ SUCESSO! Mostrando código e descrição original")
    print(f"   Exemplo: {resultado}")
else:
    print(f"⚠️ Resultado: {resultado}")
print("=" * 70)
