from django import template

def pversion(value):
    """ Turns 0001.0012.0034 in 1.12.34 """
    try:
        return '.'.join(map(str, map(int, value.split('.'))))
    except Exception, e:
        return '-'

def unpversion(value):
    """ Turns 1.12.34 in 0001.0012.0034 """
    ints = map(int, value.split("."))
    return ".".join(["%0.4d" % i for i in ints])

register = template.Library()
register.filter('pversion', pversion)
