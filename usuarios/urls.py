from django.urls import path
from . import views

app_name = 'usuarios'

urlpatterns = [
    path('', views.listar_usuarios, name='listar_usuarios'),
    path('criar/', views.criar_usuario, name='criar_usuario'),
    path('editar/<int:usuario_id>/', views.editar_usuario, name='editar_usuario'),
    path('excluir/<int:usuario_id>/', views.excluir_usuario, name='excluir_usuario'),
    path('permissoes/<int:usuario_id>/', views.configurar_permissoes_usuario, name='configurar_permissoes_usuario'),
    path('alterar-senha/<int:usuario_id>/', views.alterar_senha, name='alterar_senha'),
    
    # Grupos de Permissões
    path('grupos/', views.listar_grupos_permissao, name='listar_grupos_permissao'),
    path('grupos/criar/', views.criar_grupo_permissao, name='criar_grupo_permissao'),
    path('grupos/<int:grupo_id>/editar/', views.editar_grupo_permissao, name='editar_grupo_permissao'),
    path('grupos/<int:grupo_id>/excluir/', views.excluir_grupo_permissao, name='excluir_grupo_permissao'),
    path('grupos/<int:grupo_id>/permissoes/', views.configurar_grupo_permissao, name='configurar_grupo_permissao'),
] 