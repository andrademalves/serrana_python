"""
Script simplificado para testar a correção do formulário de orçamento
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'serrana.settings')
django.setup()

from projetos.models import Orcamento, OrcamentoItem
from projetos.forms import OrcamentoItemForm, OrcamentoItemFormSet
from decimal import Decimal

print("=" * 70)
print("TESTE: Validar form com valor 'produto_1' (formato Select2)")
print("=" * 70)

# Simular dados do POST do formulário
form_data = {
    'tipo': 'PRODUTO',
    'item': 'produto_1',  # Formato enviado pelo Select2
    'descricao': 'Barra de alumínio teste',
    'quantidade': '2.000',
    'valor_unitario': '750.0000',
    'desconto': '0.00'
}

print("\n1️⃣ Criando form com dados do POST...")
print(f"   Dados: {form_data}")

form = OrcamentoItemForm(data=form_data)

print(f"\n2️⃣ Validando form...")
is_valid = form.is_valid()

if is_valid:
    print("   ✅ Form é VÁLIDO!")
    print(f"   - Tipo: {form.cleaned_data['tipo']}")
    print(f"   - Item (valor do form): {form.cleaned_data.get('item')}")
    print(f"   - Descrição: {form.cleaned_data['descricao']}")
    print(f"   - Quantidade: {form.cleaned_data['quantidade']}")
else:
    print("   ❌ Form é INVÁLIDO!")
    print(f"   Erros: {form.errors}")
    for field, errors in form.errors.items():
        print(f"     - {field}: {errors}")

print("\n" + "=" * 70)
print("TESTE 2: Carregar orçamento existente para edição")
print("=" * 70)

# Buscar orçamento 1
try:
    orcamento = Orcamento.objects.get(pk=1)
    print(f"\n✅ Orçamento encontrado: {orcamento.codigo}")
    print(f"   Itens: {orcamento.itens.count()}")
    
    # Criar formset para edição
    formset = OrcamentoItemFormSet(instance=orcamento, prefix='itens')
    
    print(f"\n📋 Formset criado com {len(formset)} forms")
    
    for i, form in enumerate(formset):
        if form.instance and form.instance.pk:
            print(f"\n   Form {i} (Item ID {form.instance.pk}):")
            print(f"     - Tipo: {form.instance.tipo}")
            print(f"     - Item FK: {form.instance.item}")
            print(f"     - Descrição: {form.instance.descricao}")
            
            # Verificar atributos data
            item_widget_attrs = form.fields['item'].widget.attrs
            print(f"     - data-item-value: {item_widget_attrs.get('data-item-value', 'NÃO SETADO')}")
            print(f"     - data-item-text: {item_widget_attrs.get('data-item-text', 'NÃO SETADO')}")
            
except Orcamento.DoesNotExist:
    print("\n❌ Orçamento ID 1 não encontrado")

print("\n" + "=" * 70)
if is_valid:
    print("✅ TESTE PASSOU: Form aceita 'produto_1' sem erro!")
    print("\n💡 Agora teste no navegador:")
    print("   1. Criar novo orçamento: http://127.0.0.1:8000/projetos/orcamentos/criar/")
    print("   2. Editar orçamento: http://127.0.0.1:8000/projetos/orcamentos/1/editar/")
else:
    print("❌ TESTE FALHOU: Form ainda rejeita 'produto_1'")
    print("   É necessário mais ajustes no código")
print("=" * 70)
