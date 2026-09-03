from django.contrib import admin

from .models import ConnectionSuggestion


@admin.register(ConnectionSuggestion)
class ConnectionSuggestionAdmin(admin.ModelAdmin):
    list_display = ('selling_company', 'buying_company', 'product', 'status', 'tenant')
    list_filter = ('status', 'tenant')
