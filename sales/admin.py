from django.contrib import admin

from .models import Sale, SaleItem


class SaleItemInline(admin.TabularInline):
    model = SaleItem
    extra = 0


@admin.register(Sale)
class SaleAdmin(admin.ModelAdmin):
    list_display = (
        'selling_company', 'buying_company', 'sale_value', 'commission_percentage',
        'sale_date', 'payment_due_date', 'payment_confirmed', 'tenant',
    )
    list_filter = ('tenant', 'payment_confirmed')
    inlines = [SaleItemInline]
