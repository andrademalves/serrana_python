import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'serrana.settings')
django.setup()

from projetos.models import OrcamentoItem

items = OrcamentoItem.objects.filter(orcamento_id=1).select_related('item')
print(f'Total items no orçamento 1: {items.count()}')
print()

for i in items:
    print(f'ID: {i.id}')
    print(f'Tipo: {i.tipo}')
    print(f'Item FK (objeto): {i.item}')
    print(f'Item FK (ID): {i.item.id if i.item else "NULL"}')
    print(f'Descrição: {i.descricao}')
    print('-' * 50)
