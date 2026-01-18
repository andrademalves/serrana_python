import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'serrana.settings')
django.setup()

from projetos.models import Orcamento, OrcamentoItem

# Buscar orçamento 3
orc = Orcamento.objects.get(pk=3)
print(f'Orçamento ID: {orc.id}')
print(f'Código: {orc.codigo}')
print(f'Cliente: {orc.cliente}')
print()

items = OrcamentoItem.objects.filter(orcamento_id=3).select_related('item')
print(f'Itens do orçamento: {items.count()}')

for i in items:
    print(f'\n--- Item {i.id} ---')
    print(f'Tipo: {i.tipo}')
    print(f'Item FK (objeto): {i.item}')
    print(f'Item FK ID: {i.item.id if i.item else "NULL"}')
    print(f'Descrição: {i.descricao}')
    print(f'Quantidade: {i.quantidade}')
    print(f'Valor Unit: {i.valor_unitario}')
    
    # Verificar como deveria aparecer no form
    if i.item:
        prefixo = 'produto' if i.tipo == 'PRODUTO' else 'item' if i.tipo == 'MATERIAL' else 'servico'
        valor_esperado = f'{prefixo}_{i.item.id}'
        texto_esperado = f'{i.item.codigo} - {i.item.descricao}'
        print(f'\n✅ DEVERIA APARECER NO SELECT:')
        print(f'   Valor: {valor_esperado}')
        print(f'   Texto: {texto_esperado}')
    else:
        print(f'\n⚠️ Item FK é NULL - Select ficará vazio')
