import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'serrana.settings')
django.setup()

from estoque.models import Item
from cadastros.models import Produto

print('=== ITENS NO ESTOQUE ===')
itens = Item.objects.filter(ativo=True)[:5]
for i in itens:
    print(f'ID: {i.id} - Código: {i.codigo} - Descrição: {i.descricao} - Tipo: {i.tipo_item}')

print('\n=== PRODUTOS NO CADASTRO ===')
produtos = Produto.objects.filter(ativo=True, tipo='produto')[:5]
for p in produtos:
    print(f'ID: {p.id} - Código: {p.codigo} - Descrição: {p.descricao}')
