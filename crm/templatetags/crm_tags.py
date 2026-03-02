from django import template

register = template.Library()


@register.filter
def get_item(dictionary, key):
    """Template filter para acessar dict[key]"""
    if dictionary is None:
        return None
    return dictionary.get(key)
