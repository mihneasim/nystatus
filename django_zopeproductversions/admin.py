from models import *
from django.contrib import admin
from django.forms import ModelForm, CharField, PasswordInput

class ZopeInstanceForm(ModelForm):
    password = CharField(label='Password',
                         widget=PasswordInput(render_value=False))
    class Meta:
        model = ZopeInstance

class OnlineProductInline(admin.TabularInline):
    model = OnlineProduct
    extra = 1
    fields = ('zopeinstance', 'product', 'version', 'latest_version', )
    readonly_fields = ('zopeinstance','product','version','latest_version', )

class ZopeInstanceAdmin(admin.ModelAdmin):
    fieldsets = [
        (None, {'fields': ['instance_name', 'url', 'user', 'password',
        'revisit']})
    ]
    list_display = ('instance_name', 'url', 'date_added',
                    'date_checked', 'no_products', 'up_to_date', 'status')
    search_fields = ('instance_name', 'url')
    list_filter = ('status', )
    ordering = ('instance_name', '-date_checked', '-no_products')
    inlines = (OnlineProductInline, )
    form = ZopeInstanceForm

class ProductAdmin(admin.ModelAdmin):
    list_display = ('name', 'origin', 'latest_found_version',
                    'use_count', 'my_notes')
    search_fields = ('name', )
    list_filter = ('origin', )
    ordering = ('name', '-use_count')
    inlines = (OnlineProductInline, )

admin.site.register(ZopeInstance, ZopeInstanceAdmin)
admin.site.register(Product, ProductAdmin)

