from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path('admin/', admin.site.urls),
    path('saas/', include('landing.urls')),
    path('conta/', include('accounts.urls')),
    path('dashboard/', include('dashboard.urls')),
    path('empresas/', include('companies.urls')),
    path('produtos/', include('products.urls')),
    path('vendas/', include('sales.urls')),
    path('sugestoes/', include('suggestions.urls')),
    path('', include('portfolio.urls')),
]
