from models import *
from django.contrib import admin

class OnlineProductInline(admin.TabularInline):
    model = OnlineProduct
    extra = 1
    fields = ('zopeinstance', 'product', 'version', 'latest_version', )
    readonly_fields = ('zopeinstance','product','version','latest_version', )

class ErrorInline(admin.TabularInline):
    model = Error
    extra = 1
    fields = ('error_type', 'error_name', 'url_clickable', 'solved', 'date')
    readonly_fields =  ('error_type', 'error_name', 'url_clickable', 'solved', 'date')

class ZopeInstanceAdmin(admin.ModelAdmin):
    fieldsets = [
        (None, {'fields': ['instance_name', 'url', 'private_key',
        'revisit']})
    ]
    list_display = ('instance_name', 'url', 'date_added',
                    'date_checked', 'no_products', 'up_to_date', 'status')
    search_fields = ('instance_name', 'url')
    list_filter = ('status', )
    ordering = ('instance_name', '-date_checked', '-no_products')
    inlines = (OnlineProductInline, )

class ProductAdmin(admin.ModelAdmin):
    list_display = ('name', 'origin', 'latest_found_version',
                    'use_count', 'my_notes')
    search_fields = ('name', )
    list_filter = ('origin', )
    ordering = ('name', '-use_count')
    inlines = (OnlineProductInline, )

class PortalAdmin(admin.ModelAdmin):
    list_display = ('portal_name', 'url', 'no_errors',
                    'date_checked', 'status')
    search_fields = ('portal_name', 'url')
    list_filter = ('status', 'parent_instance')
    ordering = ('portal_name', )
    inlines = (ErrorInline, )

class ErrorAdmin(admin.ModelAdmin):
    list_display = ('error_type', 'error_name', 'portal', 'url_clickable', 'solved', 'date')
    search_fields = ('error_type', 'error_name', 'portal', 'url')
    list_filter = ('error_type', 'solved', 'portal')
    ordering = ('-date', )

    def url_clickable(self, obj):
        return "<a href='%s' target='_blank'>%s</a>" % (obj.url, obj.url)
    url_clickable.allow_tags = True 


admin.site.register(ZopeInstance, ZopeInstanceAdmin)
admin.site.register(Product, ProductAdmin)
admin.site.register(Portal, PortalAdmin)
admin.site.register(Error, ErrorAdmin)
