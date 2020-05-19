from django.contrib import admin
from system.models import BlockedAddress
from django.core.cache import cache


@admin.register(BlockedAddress)
class BlockedAddressAdmin(admin.ModelAdmin):
    list_display = ['ip', 'create_time']
    ordering = ['create_time']

    def delete_model(self, request, obj):
        super().delete_model(request, obj)
        cache.delete(f'island/blocked/{obj.ip}')

    def save_model(self, request, obj, form, change):
        super().save_model(request, obj, form, change)
        cache.set(f'island/blocked/{obj.ip}', True)
