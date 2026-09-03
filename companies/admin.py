from django.contrib import admin

from .models import Company


@admin.register(Company)
class CompanyAdmin(admin.ModelAdmin):
    list_display = ('trade_name', 'cnpj', 'tenant', 'business_area')
    list_filter = ('tenant', 'business_area')
    search_fields = ('trade_name', 'legal_name', 'cnpj')
