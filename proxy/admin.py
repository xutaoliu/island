from django.contrib import admin
from proxy.models import Proxy


@admin.register(Proxy)
class ProxyAdmin(admin.ModelAdmin):
    list_display = ['ip', 'port', 'location', 'delay', 'last_update']
    ordering = ['delay']
