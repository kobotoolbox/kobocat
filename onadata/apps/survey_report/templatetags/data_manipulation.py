from django import template

register = template.Library()

@register.filter
def index(l, i):
    try:
        return l[i]
    except:
        return None
        
@register.filter
def subtract(value, arg):
    return value - arg
