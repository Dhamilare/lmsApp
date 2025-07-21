from django import template

register = template.Library()

@register.filter
def replace(value, arg):
    if isinstance(value, str) and isinstance(arg, str):
        try:
            old, new = arg.split(',')
            return value.replace(old, new)
        except ValueError:
            return value
    return value

