import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'serrana.settings')
django.setup()

from cadastros.models import Produto
from estoque.models import Item

print('=== PRODUTOS (cadastros) ===')
print(f'Total Produtos: {Produto.objects.count()}')
print(f'Ativos tipo produto: {Produto.objects.filter(ativo=True, tipo="produto").count()}')
print(f'Ativos tipo servico: {Produto.objects.filter(ativo=True, tipo="servico").count()}')

print('\n=== ITENS (estoque) ===')
print(f'Total Itens: {Item.objects.count()}')
print(f'Ativos: {Item.objects.filter(ativo=True).count()}')

print('\nPrimeiros 5 produtos:')
for p in Produto.objects.filter(ativo=True)[:5]:
    print(f'  - {p.codigo} | {p.tipo} | {p.descricao}')

print('\nPrimeiros 5 itens de estoque:')
for i in Item.objects.filter(ativo=True)[:5]:
    print(f'  - {i.codigo} | {i.tipo_item} | {i.descricao}')
