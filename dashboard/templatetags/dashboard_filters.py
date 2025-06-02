from django import template

register = template.Library()

@register.filter(name='mul')
def mul(value, arg):
    """
    Multiplica o valor pelo argumento.
    Uso: {{ value|mul:arg }}
    """
    try:
        return float(value) * float(arg)
    except (ValueError, TypeError):
        return ''

@register.filter(name='div')
def div(value, arg):
    try:
        # Evitar divisão por zero
        divisor = float(arg)
        if divisor == 0:
            return 0 # Ou None, ou 'Erro', dependendo do que fizer sentido
        return float(value) / divisor
    except (ValueError, TypeError, ZeroDivisionError):
         # Tentar conversão para int como fallback
        try:
             divisor_int = int(arg)
             if divisor_int == 0:
                 return 0
             return int(value) / divisor_int
        except (ValueError, TypeError, ZeroDivisionError):
            return 0 # Retorna 0 em caso de erro ou divisão por zero

@register.filter(name='as_percentage_of')
def as_percentage_of(part, whole):
    """
    Calcula parte como porcentagem do todo.
    Uso: {{ part|as_percentage_of:whole }}
    """
    try:
        return int(float(part) / float(whole) * 100)
    except (ValueError, TypeError, ZeroDivisionError):
        return 0

@register.filter(name='add_class')
def add_class(field, css_class):
    """
    Adiciona uma classe CSS a um widget de formulário
    Uso: {{ form.field|add_class:"form-control" }}
    """
    return field.as_widget(attrs={"class": f"{field.field.widget.attrs.get('class', '')} {css_class}".strip()})

@register.filter(name='add_error_class')
def add_error_class(field, css_class):
    """
    Adiciona uma classe CSS a um widget de formulário se ele contiver erros
    Uso: {{ form.field|add_error_class:"is-invalid" }}
    """
    if hasattr(field, 'errors') and field.errors:
        return field.as_widget(attrs={"class": f"{field.field.widget.attrs.get('class', '')} {css_class}".strip()})
    return field 