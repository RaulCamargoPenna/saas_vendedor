from django.urls import path

from . import views

app_name = 'portfolio'

urlpatterns = [
    path('robots.txt', views.RobotsView.as_view(), name='robots'),
    path('sitemap.xml', views.SitemapView.as_view(), name='sitemap'),
    path('', views.LandingHomeView.as_view(), name='home'),
]
