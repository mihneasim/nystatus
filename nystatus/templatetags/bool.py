from django import template

from nystatus.helpers import reSTify

def bool_tick(value):
    if value:
        return ''
    else:
        return ''

register = template.Library()
register.filter('bool', bool_tick)
