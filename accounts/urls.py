from django.urls import path

from . import views

app_name = 'accounts'

urlpatterns = [
    path('cadastro/', views.SignUpView.as_view(), name='signup'),
    path('cadastro/concluido/', views.SignUpDoneView.as_view(), name='signup_done'),
    path('ativar/<uidb64>/<token>/', views.ActivateAccountView.as_view(), name='activate'),
    path('login/', views.EmailLoginView.as_view(), name='login'),
    path('logout/', views.LogoutView.as_view(), name='logout'),
    path('funcionarios/', views.EmployeeListView.as_view(), name='employee_list'),
    path('funcionarios/novo/', views.EmployeeCreateView.as_view(), name='employee_create'),
]
