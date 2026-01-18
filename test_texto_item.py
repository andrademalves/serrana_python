import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'serrana.settings')
django.setup()

from projetos.models import OrcamentoItem
from projetos.forms import OrcamentoItemForm

print("=" * 70)
print("TESTE: Verificar texto exibido no campo item")
print("=" * 70)

# Simular item com item_ref = produto_1
item_mock = OrcamentoItem(
    id=1,
    tipo='PRODUTO',
    item_ref='produto_1',
    item_codigo='123',
    descricao='material para porta x',  # Descrição customizada pelo usuário
    quantidade=1.000,
    valor_unitario=1500.00
)

print(f"\nItem mock criado:")
print(f"  - item_ref: {item_mock.item_ref}")
print(f"  - item_codigo: {item_mock.item_codigo}")
print(f"  - descricao (customizada): {item_mock.descricao}")

# Criar form de edição
form = OrcamentoItemForm(instance=item_mock)

# Verificar atributos data
attrs = form.fields['item'].widget.attrs
data_value = attrs.get('data-item-value', 'NÃO SETADO')
data_text = attrs.get('data-item-text', 'NÃO SETADO')

print(f"\nAtributos do widget:")
print(f"  - data-item-value: {data_value}")
print(f"  - data-item-text: {data_text}")

print("\n" + "=" * 70)

# Verificar se buscou do produto original
from cadastros.models import Produto
try:
    produto = Produto.objects.get(pk=1)
    texto_esperado = f"{produto.codigo} - {produto.descricao}"
    print(f"✅ Produto ID 1 encontrado:")
    print(f"   Código: {produto.codigo}")
    print(f"   Descrição: {produto.descricao}")
    print(f"   Texto esperado: {texto_esperado}")
    
    if data_text == texto_esperado:
        print(f"\n✅ CORRETO! Mostrando dados do PRODUTO, não da descrição customizada")
    else:
        print(f"\n⚠️ Texto exibido: {data_text}")
        print(f"   Esperado: {texto_esperado}")
except Produto.DoesNotExist:
    print("❌ Produto ID 1 não encontrado")

print("=" * 70)
