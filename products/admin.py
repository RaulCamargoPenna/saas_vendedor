from django.contrib import admin

from .models import Category, CompanyProduct, Product


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'tenant')
    list_filter = ('tenant',)
    search_fields = ('name',)


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('name', 'category', 'unit', 'tenant')
    list_filter = ('tenant', 'category')
    search_fields = ('name',)


@admin.register(CompanyProduct)
class CompanyProductAdmin(admin.ModelAdmin):
    list_display = ('company', 'product', 'relation_type', 'daily_avg_consumption', 'last_purchase_quantity', 'last_movement_date')
    list_filter = ('relation_type',)
