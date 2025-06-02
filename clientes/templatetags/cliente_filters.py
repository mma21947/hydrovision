from django import template

register = template.Library()

@register.filter
def sub(value, arg):
    """Subtrai o valor do argumento."""
    try:
        return int(value) - int(arg)
    except (ValueError, TypeError):
        return 0 