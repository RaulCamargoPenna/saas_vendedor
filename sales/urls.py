from django.urls import path

from . import views

app_name = 'sales'

urlpatterns = [
    path('', views.SaleListView.as_view(), name='list'),
    path('nova/', views.SaleCreateView.as_view(), name='create'),
    path('<int:pk>/', views.SaleDetailView.as_view(), name='detail'),
    path('<int:pk>/confirmar-pagamento/', views.SalePaymentConfirmView.as_view(), name='confirm_payment'),
]
