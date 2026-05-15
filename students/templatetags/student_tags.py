from django import template

register = template.Library()

@register.filter
def get_item(dictionary, key):
    """Get dict item by key - used in grade templates"""
    return dictionary.get(key)

@register.filter
def mul(value, arg):
    try:
        return float(value) * float(arg)
    except (ValueError, TypeError):
        return 0

@register.filter
def div(value, arg):
    try:
        return float(value) / float(arg)
    except (ValueError, TypeError, ZeroDivisionError):
        return 0

@register.filter
def pct(value, total):
    try:
        return round(float(value) / float(total) * 100, 1)
    except (ValueError, TypeError, ZeroDivisionError):
        return 0
