from django import template

register = template.Library()

@register.filter
def index(l, i):
    try:
        return l[i]
    except:
        return None