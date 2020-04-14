# coding: utf-8
from __future__ import unicode_literals, print_function, division, absolute_import
from django import template


register = template.Library()


@register.filter(name='lookup')
def lookup(value, arg):
    return value.get(arg)
