from django import template

from nystatus.helpers import reSTify

def resthtml(value):
    return reSTify(value)

register = template.Library()
register.filter('resthtml', resthtml)
