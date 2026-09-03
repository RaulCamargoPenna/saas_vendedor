from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as DjangoUserAdmin

from .models import User


@admin.register(User)
class UserAdmin(DjangoUserAdmin):
    ordering = ('email',)
    list_display = ('email', 'first_name', 'last_name', 'tenant', 'is_tenant_admin', 'is_active')
    list_filter = ('is_tenant_admin', 'is_active', 'tenant')
    search_fields = ('email', 'first_name', 'last_name')
    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        ('Informações pessoais', {'fields': ('first_name', 'last_name', 'role')}),
        ('Tenant e permissões', {
            'fields': ('tenant', 'is_tenant_admin', 'feature_permissions', 'is_active', 'is_staff', 'is_superuser', 'is_demo', 'groups', 'user_permissions'),
        }),
    )
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'password1', 'password2', 'tenant', 'is_tenant_admin', 'is_demo'),
        }),
    )
