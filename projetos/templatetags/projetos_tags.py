from django import template

register = template.Library()


@register.filter
def get_item_original_name(orcamento_item):
    """
    Retorna o código e descrição original do item baseado no item_ref
    Exemplo: "123 - Barra de alumínio"
    """
    if not orcamento_item.item_ref:
        return "-"
    
    # Se tem item_codigo salvo, usar como base
    codigo = orcamento_item.item_codigo or ""
    
    # Tentar buscar a descrição original
    descricao = ""
    
    if '_' in orcamento_item.item_ref:
        try:
            prefixo, item_id = orcamento_item.item_ref.split('_', 1)
            
            if prefixo == 'produto':
                from cadastros.models import Produto
                produto = Produto.objects.get(pk=int(item_id))
                codigo = produto.codigo
                descricao = produto.descricao
            elif prefixo == 'servico':
                from cadastros.models import Produto
                servico = Produto.objects.get(pk=int(item_id))
                codigo = servico.codigo
                descricao = servico.descricao
            elif prefixo == 'item':
                from estoque.models import Item
                estoque_item = Item.objects.get(pk=int(item_id))
                codigo = estoque_item.codigo
                descricao = estoque_item.descricao
        except:
            # Se não encontrar, usar o código salvo
            pass
    
    # Retornar formatado
    if codigo and descricao:
        return f"{codigo} - {descricao}"
    elif codigo:
        return codigo
    else:
        return "-"
