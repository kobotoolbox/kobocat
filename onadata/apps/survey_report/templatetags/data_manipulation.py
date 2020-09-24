# coding: utf-8
from __future__ import unicode_literals, print_function, division, absolute_import
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
