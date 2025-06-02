from django.urls import path
from . import views

app_name = 'relatorios'

urlpatterns = [
    path('', views.lista_relatorios, name='lista_relatorios'),
    path('por-cliente/', views.relatorio_por_cliente, name='relatorio_por_cliente'),
    path('por-tecnico/', views.relatorio_por_tecnico, name='relatorio_por_tecnico'),
    path('por-periodo/', views.relatorio_por_periodo, name='relatorio_por_periodo'),
    path('financeiro/', views.relatorio_financeiro, name='relatorio_financeiro'),
] 