"""
Template tags personalizadas para o módulo financeiro
"""
from django import template

register = template.Library()


@register.filter
def get_item(dictionary, key):
    """
    Permite acessar items de dicionário via template
    Uso: {{ dict|get_item:key }}
    """
    if dictionary is None:
        return None
    return dictionary.get(key)


@register.filter
def currency(value):
    """
    Formata valor como moeda brasileira
    Uso: {{ valor|currency }}
    """
    try:
        return f"R$ {float(value):,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    except (ValueError, TypeError):
        return value
