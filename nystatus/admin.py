# Python imports
from helpers import reSTify
import re

#Django imports
from models import *
from django.contrib import admin
from django import forms

class ErrorInline(admin.TabularInline):
    model = Error
    extra = 1
    fields = ('error_type', 'error_name', 'url', 'count', 'solved', 'date')
    readonly_fields =  ('error_type', 'error_name',
                        'url', 'count', 'solved', 'date')

class OnlineProductInline(admin.TabularInline):
    model = OnlineProduct
    extra = 1
    fields = ('zopeinstance', 'product', 'version', 'latest_version', )
    readonly_fields = ('zopeinstance','product','version','latest_version', )

class ZopeInstanceAdmin(admin.ModelAdmin):
    fieldsets = [
        (None, {'fields': ['instance_name', 'url', 'private_key',
        'revisit']})
    ]
    list_display = ('instance_name', 'url', 'date_added', 'date_checked',
                    'no_products', 'up_to_date', 'status', 'trigger_check')
    search_fields = ('instance_name', 'url')
    list_filter = ('status', )
    ordering = ('instance_name', '-date_checked', '-no_products')
    inlines = (OnlineProductInline, )

    def trigger_check(self, obj):
        return '<a href="check/%s/">Check now</a>' % obj.pk

    trigger_check.allow_tags = True

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
    list_display = ('error_type', 'error_name', 'portal', 'count',
                    'url_clickable', 'solved', 'date')
    search_fields = ('error_type', 'error_name', 'portal', 'url')
    list_filter = ('error_type', 'solved', 'portal')
    ordering = ('-date', )
    readonly_fields = ('error_traceback', )
    exclude = ('traceback', )

    def error_traceback(self, obj):
        return obj.traceback.replace("\n","<br />")
    error_traceback.allow_tags = True

    def url_clickable(self, obj):
        return "<a href='%s' target='_blank'>%s</a>" % (obj.url, obj.url)
    url_clickable.allow_tags = True

class ValidateCommitNumber(forms.ModelForm):

    class Meta:
        model = Release

    def clean_number(self):
        if re.match(r'r[1-9]+[0-9]*', self.data['number']) is None:
            # not a svn revision
            raise forms.ValidationError(("Not a valid commit (revision) "
                                         " number. Expected r[1-9]"
                                         "+[0-9]* format"))
        else:
            return self.cleaned_data['number']

class ReleaseAdmin(admin.ModelAdmin):
    form = ValidateCommitNumber
    list_display = ('product', 'version', 'datev', 'record_type',

                    'number',  #'also_affects_set',
                    'author', 'message', 'changelog', 'datec',

                    'doc_update', 'requires_update', 'update_info',
                    'obs', 
                    'date')
    search_fields = ('number', 'obs', 'update_info', 'changelog')
    ordering = ('product', '-version', '-number', '-date')
    readonly_fields = ('product', 'version', 'datev',
                       'number',  'datec', 'author', 'message', 'changelog',)
    list_filter = ('record_type', 'requires_update', 'product',
                   'author', 'doc_update')

admin.site.register(ZopeInstance, ZopeInstanceAdmin)
admin.site.register(Product, ProductAdmin)
admin.site.register(Portal, PortalAdmin)
admin.site.register(Error, ErrorAdmin)
admin.site.register(Release, ReleaseAdmin)
