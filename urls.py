from django.conf.urls.defaults import *
import django.views.generic.simple
from settings import SITE_PATH

# Uncomment the next two lines to enable the admin:
from django.contrib import admin
admin.autodiscover()

# path where the website resides relative to domain,
# ending slash, unless empty string
site_path = ''

urlpatterns = patterns('',
    # Example:
    # (r'^src/', include('src.foo.urls')),

    # Uncomment the admin/doc line below and add 'django.contrib.admindocs' 
    # to INSTALLED_APPS to enable admin documentation:
    (r'^' + SITE_PATH + 'admin/doc/',
                             include('django.contrib.admindocs.urls')),

    # Uncomment the next line to enable the admin:
    (r'^' + SITE_PATH + 'admin/django_zopeproductversions/zopeinstance/check/(?P<id>\d)/$',
                            'django_zopeproductversions.views.admin_trigger'),
    (r'^' + SITE_PATH + 'admin/', include(admin.site.urls)),
    (r'^' + SITE_PATH + '$', 'django_zopeproductversions.views.index')
)

#urlpatterns += patterns('django.views.generic.simple',
#    ('^' + SITE_PATH + '/?$', 'redirect_to', {'url': 'admin/'})
#)
