from django.conf.urls.defaults import *
import django.views.generic.simple
from settings import SITE_PATH, MEDIA_ROOT

# Uncomment the next two lines to enable the admin:
from django.contrib import admin
admin.autodiscover()

urlpatterns = patterns('',
    # Example:
    # (r'^src/', include('src.foo.urls')),

    # Uncomment the admin/doc line below and add 'django.contrib.admindocs' 
    # to INSTALLED_APPS to enable admin documentation:
    (r'^' + SITE_PATH + 'admin/doc/',
                             include('django.contrib.admindocs.urls')),

    # Uncomment the next line to enable the admin:
    (r'^' + SITE_PATH + 'admin/nystatus/zopeinstance/check/(?P<id>\d)/$',
                            'nystatus.views.admin_trigger'),
    (r'^' + SITE_PATH + 'admin/', include(admin.site.urls)),
    (r'^' + SITE_PATH+ 'media/(.*)', 'django.views.static.serve', {'document_root': MEDIA_ROOT}),
    (r'^' + SITE_PATH + '$', 'nystatus.views.index')
)

#urlpatterns += patterns('django.views.generic.simple',
#    ('^' + SITE_PATH + '/?$', 'redirect_to', {'url': 'admin/'})
#)
