from django.urls import path

from . import views

app_name = 'portfolio'

urlpatterns = [
    path('', views.LandingHomeView.as_view(), name='home'),
]
