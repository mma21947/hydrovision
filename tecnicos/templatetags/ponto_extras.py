from django import template
from datetime import timedelta

register = template.Library()

@register.filter
def get_item(dictionary, key):
    """Obtém um item de um dicionário por chave"""
    return dictionary.get(key)

@register.filter
def format_timedelta(td):
    """Formata um objeto timedelta para exibição em horas e minutos"""
    if not isinstance(td, timedelta):
        return ""
    
    total_seconds = td.total_seconds()
    hours = int(total_seconds // 3600)
    minutes = int((total_seconds % 3600) // 60)
    
    return f"{hours}h {minutes}min" 