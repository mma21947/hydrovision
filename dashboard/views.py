from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.db.models import Count, Avg, Sum, F, Q, FloatField, IntegerField, Case, When, Value, ExpressionWrapper
from django.db.models.functions import Cast, TruncMonth, TruncWeek, Coalesce, ExtractMonth, ExtractYear
from django.utils import timezone
from datetime import timedelta
from django.contrib.auth import logout
from django.contrib import messages
import logging

from ordens.models import OrdemServico
from tecnicos.models import Tecnico, LocalizacaoAtendimento
from .models import MetricaDiaria

# Configurar logger
logger = logging.getLogger(__name__)

@login_required
def dashboard(request):
    """
    View principal do dashboard que exibe métricas e status do sistema
    """
    logger.debug("Iniciando view do dashboard")
    logger.debug(f"Usuário: {request.user.username}, autenticado: {request.user.is_authenticated}")
    
    # Obter ordens
    ordens = OrdemServico.objects.all()
    total_ordens = ordens.count()
    
    # Filtrar por status
    ordens_abertas = ordens.filter(status='aberta').count()
    ordens_andamento = ordens.filter(status='em_andamento').count()
    ordens_aguardando_peca = ordens.filter(status='aguardando_peca').count()
    ordens_aguardando_cliente = ordens.filter(status='aguardando_cliente').count()
    ordens_concluidas = ordens.filter(status='concluida').count()
    ordens_canceladas = ordens.filter(status='cancelada').count()
    
    # Calcular ordens pendentes
    ordens_pendentes = ordens_abertas + ordens_andamento + ordens_aguardando_peca + ordens_aguardando_cliente
    
    # Calcular métricas de performance
    taxa_resolucao = 0
    if total_ordens > 0:
        taxa_resolucao = round((ordens_concluidas / total_ordens) * 100)
    
    # Obter dados de avaliação
    avaliacoes = ordens.filter(avaliacao_cliente__isnull=False)
    satisfacao_media = avaliacoes.aggregate(media=Avg('avaliacao_cliente'))['media'] or 0
    
    # Dados para o gráfico de satisfação
    satisfacao_dados = [
        avaliacoes.filter(avaliacao_cliente=1).count(),
        avaliacoes.filter(avaliacao_cliente=2).count(),
        avaliacoes.filter(avaliacao_cliente=3).count(),
        avaliacoes.filter(avaliacao_cliente=4).count(),
        avaliacoes.filter(avaliacao_cliente=5).count(),
    ]
    
    # Dados para o gráfico de status
    status_dados = [
        ordens_abertas,
        ordens_andamento,
        ordens_aguardando_peca + ordens_aguardando_cliente,
        ordens_concluidas,
        ordens_canceladas,
    ]
    
    # Calcular tempo médio de atendimento
    ordens_com_tempo = ordens.filter(
        status='concluida', 
        data_inicio__isnull=False,
        data_conclusao__isnull=False
    )
    
    tempo_medio = "N/A"
    if ordens_com_tempo.exists():
        # Cálculo simplificado do tempo médio
        tempos = []
        for ordem in ordens_com_tempo:
            tempos.append((ordem.data_conclusao - ordem.data_inicio).total_seconds() / 3600)  # em horas
        
        tempo_medio_horas = sum(tempos) / len(tempos)
        tempo_medio = f"{tempo_medio_horas:.1f} horas"
    
    # Calcular faturamento do dia atual
    hoje = timezone.now().date()
    faturamento = ordens.filter(
        status='concluida', 
        data_conclusao__date=hoje
    ).aggregate(total=Sum('valor_total'))['total'] or 0
    
    # Calcular ordens por técnico
    tecnicos_ativos = Tecnico.objects.filter(ativo=True).count()
    ordens_por_tecnico = 0
    if tecnicos_ativos > 0:
        ordens_por_tecnico = total_ordens / tecnicos_ativos
    
    # Obter técnicos disponíveis
    tecnicos_disponiveis = Tecnico.objects.filter(status='disponivel', ativo=True).count()
    
    # Obter últimas ordens
    ultimas_ordens = ordens.order_by('-data_abertura')[:5]
    
    # Atualizar ou criar métrica diária
    MetricaDiaria.gerar_metrica_hoje()
    
    context = {
        'total_ordens': total_ordens,
        'ordens_pendentes': ordens_pendentes,
        'ordens_concluidas': ordens_concluidas,
        'tecnicos_disponiveis': tecnicos_disponiveis,
        'satisfacao_media': satisfacao_media,
        'satisfacao_dados': satisfacao_dados,
        'status_dados': status_dados,
        'taxa_resolucao': taxa_resolucao,
        'tempo_medio': tempo_medio,
        'faturamento': faturamento,
        'ordens_por_tecnico': ordens_por_tecnico,
        'ultimas_ordens': ultimas_ordens,
    }
    
    return render(request, 'dashboard/dashboard.html', context)

@login_required
def metricas_api(request):
    """API para obter dados de métricas para gráficos"""
    # Obter datas para o eixo x (últimos 7 dias)
    datas = []
    metricas = []
    
    hoje = timezone.now().date()
    for i in range(6, -1, -1):
        data = hoje - timezone.timedelta(days=i)
        datas.append(data.strftime('%d/%m'))
        
        # Obter ou criar métrica do dia
        metrica, created = MetricaDiaria.objects.get_or_create(
            data=data,
            defaults={
                'total_ordens': 0,
                'ordens_abertas': 0,
                'ordens_andamento': 0,
                'ordens_aguardando': 0,
                'ordens_concluidas': 0,
                'ordens_canceladas': 0,
                'satisfacao_media': 0,
            }
        )
        
        metricas.append({
            'total_ordens': metrica.total_ordens,
            'ordens_abertas': metrica.ordens_abertas,
            'ordens_andamento': metrica.ordens_andamento,
            'ordens_aguardando': metrica.ordens_aguardando,
            'ordens_concluidas': metrica.ordens_concluidas,
            'ordens_canceladas': metrica.ordens_canceladas,
            'satisfacao_media': float(metrica.satisfacao_media),
            'faturamento': float(metrica.faturamento_dia),
        })
    
    return JsonResponse({
        'datas': datas,
        'metricas': metricas,
    })

@login_required
def tecnicos_mapa_api(request):
    """API para obter dados dos técnicos para o mapa"""
    try:
        tecnicos = Tecnico.objects.filter(
            ativo=True,
            latitude__isnull=False,
            longitude__isnull=False
        )
        
        data = []
        for tecnico in tecnicos:
            # Verificar se o técnico está disponível baseado no status
            esta_disponivel = tecnico.status == 'disponivel'
            
            data.append({
                'id': tecnico.id,
                'nome': tecnico.nome_completo,
                'celular': tecnico.celular or '',
                'latitude': float(tecnico.latitude),
                'longitude': float(tecnico.longitude),
                'disponivel': esta_disponivel,  # Compatibilidade com front-end que espera esta propriedade
                'status': tecnico.status,       # Adicionar o status atual
                'status_display': tecnico.get_status_display(),  # Nome formatado do status
                'ultima_atualizacao': tecnico.ultima_atualizacao_local.isoformat() if tecnico.ultima_atualizacao_local else None,
            })
        
        return JsonResponse(data, safe=False)
    
    except Exception as e:
        logger.error(f"Erro na API tecnicos_mapa_api: {e}")
        return JsonResponse({'error': str(e)}, status=500)

@login_required
def desempenho_tecnicos(request):
    """
    View para exibir o dashboard de desempenho dos técnicos
    """
    # Obter todos os técnicos ativos
    tecnicos = Tecnico.objects.filter(ativo=True).order_by('nome_completo')
    
    # Obter período de filtro (padrão: último mês)
    periodo = request.GET.get('periodo', 'mes')
    
    # Definir datas de início e fim conforme o período
    hoje = timezone.now().date()
    
    if periodo == 'semana':
        inicio = hoje - timedelta(days=7)
        periodo_texto = 'Última Semana'
    elif periodo == 'mes':
        inicio = hoje - timedelta(days=30)
        periodo_texto = 'Último Mês'
    elif periodo == 'trimestre':
        inicio = hoje - timedelta(days=90)
        periodo_texto = 'Último Trimestre'
    else:  # ano
        inicio = hoje - timedelta(days=365)
        periodo_texto = 'Último Ano'
    
    # Calcular KPIs gerais
    ordens = OrdemServico.objects.filter(
        tecnico__isnull=False,
        data_abertura__date__gte=inicio,
        data_abertura__date__lte=hoje
    )
    
    total_ordens = ordens.count()
    
    # Calcular tempo médio de atendimento geral
    ordens_concluidas = ordens.filter(
        status='concluida',
        data_inicio__isnull=False,
        data_conclusao__isnull=False
    )
    
    tempo_medio_geral = None
    if ordens_concluidas.exists():
        tempos = []
        for ordem in ordens_concluidas:
            tempo = (ordem.data_conclusao - ordem.data_inicio).total_seconds() / 3600
            tempos.append(tempo)
        
        tempo_medio_geral = sum(tempos) / len(tempos)
    
    # Calcular satisfação média geral
    avaliacoes = ordens.filter(avaliacao_cliente__isnull=False)
    satisfacao_media_geral = avaliacoes.aggregate(media=Avg('avaliacao_cliente'))['media'] or 0
    
    context = {
        'tecnicos': tecnicos,
        'periodo': periodo,
        'periodo_texto': periodo_texto,
        'total_ordens': total_ordens,
        'tempo_medio_geral': tempo_medio_geral,
        'satisfacao_media_geral': satisfacao_media_geral,
        'data_inicio': inicio,
        'data_fim': hoje,
    }
    
    return render(request, 'dashboard/desempenho_tecnicos.html', context)

@login_required
def desempenho_tecnicos_api(request):
    """
    API para fornecer dados de desempenho dos técnicos para o dashboard
    """
    # Obter período de filtro (padrão: último mês)
    periodo = request.GET.get('periodo', 'mes')
    
    # Definir datas de início e fim conforme o período
    hoje = timezone.now().date()
    
    if periodo == 'semana':
        inicio = hoje - timedelta(days=7)
    elif periodo == 'mes':
        inicio = hoje - timedelta(days=30)
    elif periodo == 'trimestre':
        inicio = hoje - timedelta(days=90)
    else:  # ano
        inicio = hoje - timedelta(days=365)
    
    # Obter técnicos ativos com suas métricas
    tecnicos = Tecnico.objects.filter(ativo=True)
    
    dados_tecnicos = []
    for tecnico in tecnicos:
        # Ordens atribuídas ao técnico no período
        ordens_tecnico = OrdemServico.objects.filter(
            tecnico=tecnico,
            data_abertura__date__gte=inicio,
            data_abertura__date__lte=hoje
        )
        
        total_ordens = ordens_tecnico.count()
        
        if total_ordens == 0:
            continue  # Pular técnicos sem ordens no período
        
        # Calcular status das ordens
        ordens_concluidas = ordens_tecnico.filter(status='concluida').count()
        ordens_pendentes = total_ordens - ordens_concluidas
        
        # Taxa de conclusão
        taxa_conclusao = round((ordens_concluidas / total_ordens) * 100 if total_ordens > 0 else 0)
        
        # Tempo médio de atendimento
        ordens_com_tempo = ordens_tecnico.filter(
            status='concluida',
            data_inicio__isnull=False,
            data_conclusao__isnull=False
        )
        
        tempo_medio = None
        if ordens_com_tempo.exists():
            tempos = []
            for ordem in ordens_com_tempo:
                tempo = (ordem.data_conclusao - ordem.data_inicio).total_seconds() / 3600
                tempos.append(tempo)
            
            tempo_medio = sum(tempos) / len(tempos)
        
        # Satisfação média dos clientes
        avaliacoes = ordens_tecnico.filter(avaliacao_cliente__isnull=False)
        satisfacao_media = avaliacoes.aggregate(media=Avg('avaliacao_cliente'))['media'] or 0
        total_avaliacoes = avaliacoes.count()
        
        # Produtividade diária (ordens por dia de trabalho)
        dias_periodo = (hoje - inicio).days
        produtividade = round(total_ordens / dias_periodo, 2) if dias_periodo > 0 else 0
        
        # Distribuição de avaliações
        distribuicao_avaliacoes = [
            avaliacoes.filter(avaliacao_cliente=1).count(),
            avaliacoes.filter(avaliacao_cliente=2).count(),
            avaliacoes.filter(avaliacao_cliente=3).count(),
            avaliacoes.filter(avaliacao_cliente=4).count(),
            avaliacoes.filter(avaliacao_cliente=5).count(),
        ]
        
        # Tendência de ordens por semana
        tendencia_ordens = []
        
        # Dividir o período em semanas
        data_atual = inicio
        while data_atual <= hoje:
            data_fim_semana = min(data_atual + timedelta(days=6), hoje)
            
            # Contar ordens nesta semana
            ordens_semana = ordens_tecnico.filter(
                data_abertura__date__gte=data_atual,
                data_abertura__date__lte=data_fim_semana
            ).count()
            
            tendencia_ordens.append({
                'semana': data_atual.strftime('%d/%m'),
                'ordens': ordens_semana
            })
            
            # Avançar para próxima semana
            data_atual += timedelta(days=7)
        
        # Calcular histórico de distância percorrida a partir das localizações
        localizacoes = LocalizacaoAtendimento.objects.filter(
            tecnico=tecnico,
            data_hora__date__gte=inicio,
            data_hora__date__lte=hoje
        ).order_by('data_hora')
        
        # Agrupar por dia
        from collections import defaultdict
        import math
        
        distancia_por_dia = defaultdict(float)
        
        # Calcular distância entre pontos consecutivos por dia
        last_lat, last_lon, last_date = None, None, None
        
        for loc in localizacoes:
            data = loc.data_hora.date()
            
            if last_lat and last_lon and last_date == data:
                # Distância haversine simplificada (em km)
                R = 6371  # raio da Terra em km
                dlat = math.radians(loc.latitude - last_lat)
                dlon = math.radians(loc.longitude - last_lon)
                a = (math.sin(dlat/2)**2 + 
                    math.cos(math.radians(last_lat)) * math.cos(math.radians(loc.latitude)) * 
                    math.sin(dlon/2)**2)
                c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
                distancia = R * c
                
                distancia_por_dia[data.strftime('%d/%m')] += distancia
            
            last_lat, last_lon, last_date = loc.latitude, loc.longitude, data
        
        # Converter para lista para o gráfico
        distancia_percorrida = []
        for data, distancia in distancia_por_dia.items():
            distancia_percorrida.append({
                'data': data,
                'distancia': round(distancia, 1)
            })
        
        # Ordenar por data
        distancia_percorrida.sort(key=lambda x: x['data'])
        
        # Adicionar dados deste técnico
        dados_tecnicos.append({
            'id': tecnico.id,
            'nome': tecnico.nome_completo,
            'foto': tecnico.foto.url if tecnico.foto else None,
            'total_ordens': total_ordens,
            'ordens_concluidas': ordens_concluidas,
            'ordens_pendentes': ordens_pendentes,
            'taxa_conclusao': taxa_conclusao,
            'tempo_medio': tempo_medio,
            'satisfacao_media': satisfacao_media,
            'total_avaliacoes': total_avaliacoes,
            'produtividade': produtividade,
            'distribuicao_avaliacoes': distribuicao_avaliacoes,
            'tendencia_ordens': tendencia_ordens,
            'distancia_percorrida': distancia_percorrida
        })
    
    # Ordenar por taxa de conclusão (do maior para o menor)
    dados_tecnicos.sort(key=lambda x: x['taxa_conclusao'], reverse=True)
    
    return JsonResponse({
        'tecnicos': dados_tecnicos,
        'periodo': {
            'inicio': inicio.strftime('%Y-%m-%d'),
            'fim': hoje.strftime('%Y-%m-%d')
        }
    })

def custom_logout(request):
    """
    View personalizada para logout que renderiza um template de despedida
    ao invés de redirecionar imediatamente.
    """
    logout(request)
    messages.success(request, 'Você foi desconectado com sucesso.')
    return render(request, 'logout.html')
