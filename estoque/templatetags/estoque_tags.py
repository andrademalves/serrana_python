from django import template

register = template.Library()

@register.filter(name='get_item')
def get_item(dictionary, key):
    """
    Permite acessar valores de dicionário no template
    Uso: {{ dict|get_item:key }}
    """
    if dictionary is None:
        return None
    return dictionary.get(key)
