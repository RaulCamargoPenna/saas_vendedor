from django.contrib import admin
from django.contrib import messages

from .models import Tenant


@admin.action(description='Ativar tenants selecionados')
def activate_tenants(modeladmin, request, queryset):
    updated = queryset.update(is_active=True)
    messages.success(request, f'{updated} tenant(s) ativado(s) com sucesso.')


@admin.register(Tenant)
class TenantAdmin(admin.ModelAdmin):
    list_display = ('name', 'cnpj', 'is_active', 'created_at')
    list_filter = ('is_active',)
    search_fields = ('name', 'cnpj')
    actions = [activate_tenants]
