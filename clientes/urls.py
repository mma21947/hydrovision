from django.urls import path
from . import views

urlpatterns = [
    path('novo/', views.novo_cliente, name='novo_cliente'),
    path('listar/', views.listar_clientes, name='listar_clientes'),
    path('detalhe/<slug:slug>/', views.detalhe_cliente, name='detalhe_cliente'),
    path('editar/<slug:slug>/', views.editar_cliente, name='editar_cliente'),
    path('excluir/<slug:slug>/', views.excluir_cliente, name='excluir_cliente'),
    path('contrato/excluir/<int:contrato_id>/', views.excluir_contrato, name='excluir_contrato'),
    path('api/buscar/', views.buscar_cliente_api, name='buscar_cliente_api'),
    path('api/buscar-por-id/', views.buscar_cliente_por_id_api, name='buscar_cliente_por_id_api'),
] 