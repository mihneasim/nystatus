from django.conf.urls.defaults import *
import django.views.generic.simple

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
    (r'^' + site_path + 'admin/doc/',
                             include('django.contrib.admindocs.urls')),

    # Uncomment the next line to enable the admin:
    (r'^' + site_path + 'productversions/zopeinstance/check/(?P<id>\d)/$',
                            'django_zopeproductversions.views.admin_trigger'),
    (r'^' + site_path + 'admin/', include(admin.site.urls)),
)

urlpatterns += patterns('django.views.generic.simple',
    ('^' + site_path + '/?$', 'redirect_to', {'url': 'admin/'})
)
