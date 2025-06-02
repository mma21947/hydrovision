from django.urls import path
from . import views

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    path('api/metricas/', views.metricas_api, name='metricas_api'),
    path('api/tecnicos-mapa/', views.tecnicos_mapa_api, name='tecnicos_mapa_api'),
    path('relatorios/desempenho-tecnicos/', views.desempenho_tecnicos, name='desempenho_tecnicos'),
    path('api/desempenho-tecnicos-dados/', views.desempenho_tecnicos_api, name='desempenho_tecnicos_api'),
] 