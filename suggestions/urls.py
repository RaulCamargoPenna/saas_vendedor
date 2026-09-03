from django.urls import path

from . import views

app_name = 'suggestions'

urlpatterns = [
    path('', views.ConnectionSuggestionListView.as_view(), name='list'),
    path('atualizar/', views.ConnectionSuggestionRefreshView.as_view(), name='refresh'),
    path('<int:pk>/descartar/', views.ConnectionSuggestionDiscardView.as_view(), name='discard'),
]
