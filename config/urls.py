from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path('admin/', admin.site.urls),
    path('saas/', include('landing.urls')),
    path('saas/conta/', include('accounts.urls')),
    path('saas/dashboard/', include('dashboard.urls')),
    path('saas/empresas/', include('companies.urls')),
    path('saas/produtos/', include('products.urls')),
    path('saas/vendas/', include('sales.urls')),
    path('saas/sugestoes/', include('suggestions.urls')),
    path('', include('portfolio.urls')),
]
