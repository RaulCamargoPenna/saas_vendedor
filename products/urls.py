from django.urls import path

from . import views

app_name = 'products'

urlpatterns = [
    path('', views.ProductListView.as_view(), name='list'),
    path('novo/', views.ProductCreateView.as_view(), name='create'),
    path('<int:pk>/editar/', views.ProductUpdateView.as_view(), name='update'),
    path('<int:pk>/excluir/', views.ProductDeleteView.as_view(), name='delete'),

    path('categorias/', views.CategoryListView.as_view(), name='category_list'),
    path('categorias/nova/', views.CategoryCreateView.as_view(), name='category_create'),
    path('categorias/<int:pk>/editar/', views.CategoryUpdateView.as_view(), name='category_update'),
    path('categorias/<int:pk>/excluir/', views.CategoryDeleteView.as_view(), name='category_delete'),

    path('empresas/<int:company_pk>/vincular/', views.CompanyProductCreateView.as_view(), name='company_product_create'),
    path('vinculos/<int:company_pk>/<int:pk>/update/', views.CompanyProductUpdateView.as_view(), name='company_product_update'),
    path('vinculos/<int:pk>/excluir/', views.CompanyProductDeleteView.as_view(), name='company_product_delete'),
]
