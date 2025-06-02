from django.urls import path
from . import views

urlpatterns = [
    path('', views.listar_equipamentos, name='listar_equipamentos'),
    path('novo/', views.novo_equipamento, name='novo_equipamento'),
    path('detalhe/<slug:slug>/', views.detalhe_equipamento, name='detalhe_equipamento'),
    path('editar/<slug:slug>/', views.editar_equipamento, name='editar_equipamento'),
    path('excluir/<slug:slug>/', views.excluir_equipamento, name='excluir_equipamento'),
    path('qrcode/<slug:slug>/', views.gerar_qrcode_equipamento, name='gerar_qrcode_equipamento'),
    path('historico/<slug:slug>/', views.historico_equipamento, name='historico_equipamento'),
    path('categorias/', views.categorias_equipamento, name='categorias_equipamento'),
    path('categorias/nova/', views.nova_categoria_equipamento, name='nova_categoria_equipamento'),
    path('categorias/editar/<slug:slug>/', views.editar_categoria_equipamento, name='editar_categoria_equipamento'),
    path('categorias/detalhe/<int:categoria_id>/', views.detalhes_categoria_equipamento, name='detalhes_categoria_equipamento'),
    path('categorias/excluir/<int:categoria_id>/', views.excluir_categoria_equipamento, name='excluir_categoria_equipamento'),
    path('categorias/excluir/ajax/', views.excluir_categoria_equipamento_ajax, name='excluir_categoria_equipamento_ajax'),
    path('categorias/editar/ajax/', views.editar_categoria_equipamento_ajax, name='editar_categoria_equipamento_ajax'),
    path('categorias/<int:categoria_id>/json/', views.categoria_json, name='categoria_json'),
    path('categorias/<int:categoria_id>/check-equipamentos/', views.verificar_equipamentos_categoria, name='verificar_equipamentos_categoria'),
    path('cliente/<slug:slug>/', views.equipamentos_cliente, name='equipamentos_cliente'),
    path('manutencao/nova/<slug:equipamento_slug>/', views.nova_manutencao, name='nova_manutencao'),
    path('categorias/adicionar/ajax/', views.adicionar_categoria_equipamento_ajax, name='adicionar_categoria_equipamento_ajax'),
] 