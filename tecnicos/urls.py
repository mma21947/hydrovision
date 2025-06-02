from django.urls import path
from . import views

app_name = 'tecnicos'

urlpatterns = [
    path('novo/', views.novo_tecnico, name='novo_tecnico'),
    path('listar/', views.listar_tecnicos, name='listar_tecnicos'),
    path('editar/<slug:slug>/', views.editar_tecnico, name='editar_tecnico'),
    path('detalhe/<slug:slug>/', views.detalhe_tecnico, name='detalhe_tecnico'),
    path('mapa/', views.mapa_tecnicos, name='mapa_tecnicos'),
    path('api/atualizar-localizacao/', views.atualizar_localizacao_api, name='atualizar_localizacao_api'),
    
    # Rotas para a API do calendário (com várias opções para garantir compatibilidade)
    path('calendario/eventos/<int:tecnico_id>/', views.calendario_eventos_api, name='calendario_eventos_api'),
    path('api/calendario-eventos/<int:tecnico_id>/', views.calendario_eventos_api, name='calendario_eventos_api_alt'),
    path('ordens/<int:tecnico_id>/', views.calendario_eventos_api, name='ordens_tecnico'),
    
    path('calendario/diagnostico/<int:tecnico_id>/', views.diagnosticar_calendario_api, name='diagnosticar_calendario_api'),
    path('api/calendario-eventos/slug/<slug:slug>/', views.calendario_eventos_por_slug, name='calendario_eventos_por_slug'),
    # Removido temporariamente até ser implementado corretamente
    # path('api/calendario-status/', views.verificar_status_calendario, name='verificar_status_calendario'),
    
    path('ponto/', views.apontamento_ponto, name='apontamento_ponto'),
    path('ponto/registrar/', views.registrar_ponto, name='registrar_ponto'),
    path('ponto/relatorio/', views.relatorio_ponto, name='relatorio_ponto'),
] 