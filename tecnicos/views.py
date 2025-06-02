from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.db import models, transaction
from django.contrib.auth.models import User
from django.utils import timezone
import traceback
import sys
from django.conf import settings
from django.db.models import Count, Sum, Avg

from .models import Tecnico, RegistroPonto
from ordens.models import OrdemServico

# Create your views here.

@login_required
def novo_tecnico(request):
    # Se o método for POST, processar o formulário
    if request.method == 'POST':
        try:
            # Verificar se as senhas coincidem
            password = request.POST.get('password')
            password_confirm = request.POST.get('password_confirm')
            
            if password != password_confirm:
                messages.error(request, 'As senhas não coincidem')
                return render(request, 'tecnicos/novo_tecnico.html', {
                    'form_data': request.POST
                })
            
            # Verificar se o nome de usuário já existe
            username = request.POST.get('username')
            if User.objects.filter(username=username).exists():
                messages.error(request, f'Nome de usuário "{username}" já está em uso')
                return render(request, 'tecnicos/novo_tecnico.html', {
                    'form_data': request.POST
                })
            
            # Verificar se o CPF já existe usando o método da classe
            cpf = request.POST.get('cpf', '').strip()
            if Tecnico.cpf_existe(cpf):
                messages.error(request, f'O CPF {cpf} já está cadastrado para outro técnico')
                return render(request, 'tecnicos/novo_tecnico.html', {
                    'form_data': request.POST  # Devolver os dados do formulário para não perder o que foi digitado
                })
            
            # Usar transação para garantir que tanto o usuário quanto o técnico sejam criados
            with transaction.atomic():
                # Criar novo usuário
                nome_completo = request.POST.get('nome_completo', '')
                email = request.POST.get('email', '')
                
                # Separar nome e sobrenome
                nomes = nome_completo.split(' ', 1)
                primeiro_nome = nomes[0]
                sobrenome = nomes[1] if len(nomes) > 1 else ''
                
                # Criar o usuário no Django
                user = User.objects.create_user(
                    username=username,
                    password=password,
                    email=email,
                    first_name=primeiro_nome,
                    last_name=sobrenome
                )
            
                # Extrair dados do formulário para o técnico
                tecnico = Tecnico(
                    usuario=user,
                    nome_completo=nome_completo,
                    cpf=cpf,
                    rg=request.POST.get('rg', ''),
                    data_nascimento=request.POST.get('data_nascimento'),
                    email=email,
                    telefone=request.POST.get('telefone', ''),
                    celular=request.POST.get('celular', ''),
                    endereco=request.POST.get('endereco', ''),
                    numero=request.POST.get('numero', ''),
                    complemento=request.POST.get('complemento', ''),
                    bairro=request.POST.get('bairro', ''),
                    cidade=request.POST.get('cidade', ''),
                    estado=request.POST.get('estado', ''),
                    cep=request.POST.get('cep', ''),
                    nivel=request.POST.get('nivel', 'junior'),
                    especialidade=request.POST.get('especialidade', ''),
                    status=request.POST.get('status', 'disponivel'),
                    data_admissao=request.POST.get('data_admissao'),
                    observacoes=request.POST.get('observacoes', ''),
                    certificacoes=request.POST.get('certificacoes', ''),
                    habilidades=request.POST.get('habilidades', ''),
                )
                
                # Gerar código automaticamente (exemplo: TEC20250001)
                hoje = timezone.now()
                ano = hoje.strftime('%Y')
                mes = hoje.strftime('%m')
                contador = Tecnico.objects.filter(
                    codigo__startswith=f'TEC{ano}{mes}'
                ).count() + 1
                
                tecnico.codigo = f'TEC{ano}{mes}{contador:04d}'
                
                # Verificar se há arquivo de foto
                if 'foto' in request.FILES:
                    tecnico.foto = request.FILES['foto']
                
                # Salvar o técnico
                tecnico.save()
            
            messages.success(
                request, 
                f'Técnico {tecnico.nome_completo} (Código: {tecnico.codigo}) cadastrado com sucesso! Credenciais de acesso criadas.'
            )
            return redirect('tecnicos:listar_tecnicos')
            
        except Exception as e:
            messages.error(
                request, 
                f'Erro ao cadastrar técnico: {str(e)}'
            )
            # Devolver os dados do formulário em caso de exceção
            return render(request, 'tecnicos/novo_tecnico.html', {
                'form_data': request.POST
            })
    
    # Se o método for GET, exibir o formulário vazio
    today = timezone.now().date().isoformat()  # Data atual para usar no campo de admissão
    context = {
        'form_data': {
            'status': 'disponivel',  # Status padrão
            'nivel': 'junior',       # Nível padrão
            'data_admissao': today   # Data de admissão padrão (hoje)
        }
    }
    return render(request, 'tecnicos/novo_tecnico.html', context)

@login_required
def listar_tecnicos(request):
    # Buscar todos os técnicos
    tecnicos = Tecnico.objects.all()
    
    # Filtragem por termo de busca
    termo_busca = request.GET.get('q', '')
    if termo_busca:
        tecnicos = tecnicos.filter(
            models.Q(nome_completo__icontains=termo_busca) |
            models.Q(codigo__icontains=termo_busca) |
            models.Q(cpf__icontains=termo_busca) |
            models.Q(especialidade__icontains=termo_busca)
        )
    
    # Ordenar por nome
    tecnicos = tecnicos.order_by('nome_completo')
    
    context = {
        'tecnicos': tecnicos,
        'termo_busca': termo_busca
    }
    
    return render(request, 'tecnicos/listar_tecnicos.html', context)

@login_required
def detalhe_tecnico(request, slug):
    tecnico = get_object_or_404(Tecnico, slug=slug)
    
    # Obter ordens de serviço ativas do técnico
    ordens_ativas = OrdemServico.objects.filter(
        tecnico=tecnico,
        status__in=['aberta', 'em_andamento']
    ).order_by('-data_abertura')
    
    # Calcular métricas
    num_ordens_abertas = ordens_ativas.count()
    
    # Calcular média de avaliações
    media_avaliacoes = OrdemServico.objects.filter(
        tecnico=tecnico,
        avaliacao_cliente__isnull=False
    ).aggregate(Avg('avaliacao_cliente'))['avaliacao_cliente__avg'] or 0
    
    # Calcular total de ordens concluídas
    total_ordens_concluidas = OrdemServico.objects.filter(
        tecnico=tecnico,
        status='concluida'
    ).count()
    
    context = {
        'tecnico': tecnico,
        'ordens_ativas': ordens_ativas,
        'num_ordens_abertas': num_ordens_abertas,
        'media_avaliacoes': round(media_avaliacoes, 1),
        'total_ordens_concluidas': total_ordens_concluidas
    }
    
    return render(request, 'tecnicos/detalhe_tecnico.html', context)

@login_required
def calendario_eventos_api(request, tecnico_id):
    """API para fornecer eventos do calendário para um técnico específico"""
    from ordens.models import OrdemServico
    from django.http import JsonResponse
    
    try:
        print(f"DEBUG: Gerando eventos do calendário para o técnico ID: {tecnico_id}")
        tecnico = get_object_or_404(Tecnico, id=tecnico_id)
        
        # Configurar cabeçalhos para CORS se for uma requisição AJAX
        response_headers = {}
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            response_headers['Access-Control-Allow-Origin'] = '*'
            response_headers['Access-Control-Allow-Methods'] = 'GET, OPTIONS'
            response_headers['Access-Control-Allow-Headers'] = 'Content-Type, X-Requested-With'
        
        # Verificar se a requisição possui parâmetros de mês e ano
        try:
            mes = int(request.GET.get('mes', 0))
            ano = int(request.GET.get('ano', 0))
            
            # Se mês e ano foram fornecidos, filtrar por aquele mês específico
            if mes > 0 and ano > 0:
                import datetime
                import calendar
                
                # Determinar o primeiro e último dia do mês
                primeiro_dia = datetime.date(ano, mes, 1)
                ultimo_dia = datetime.date(ano, mes, calendar.monthrange(ano, mes)[1])
                
                # Converter para datetime com timezone
                data_inicial = timezone.make_aware(datetime.datetime.combine(primeiro_dia, datetime.time.min))
                data_final = timezone.make_aware(datetime.datetime.combine(ultimo_dia, datetime.time.max))
                
                print(f"DEBUG: Filtrando eventos por período: {data_inicial} a {data_final}")
            else:
                # Default: Buscar ordens de serviço em um período maior (últimos 6 meses e próximos 6 meses)
                data_inicial = timezone.now() - timezone.timedelta(days=180)  # 6 meses atrás
                data_final = timezone.now() + timezone.timedelta(days=180)    # 6 meses à frente
        except (ValueError, TypeError):
            # Em caso de erro, usar o período padrão
            data_inicial = timezone.now() - timezone.timedelta(days=180)  # 6 meses atrás
            data_final = timezone.now() + timezone.timedelta(days=180)    # 6 meses à frente
        
        # Primeiro método: buscar por ordens com data_agendamento
        ordens = OrdemServico.objects.filter(
            tecnico=tecnico,
            data_agendamento__isnull=False,
            data_agendamento__gte=data_inicial,
            data_agendamento__lte=data_final
        )
        
        print(f"DEBUG: Encontradas {ordens.count()} ordens de serviço com agendamento para o técnico {tecnico.nome_completo}")
        
        # Se não encontrar nenhuma ordem com data_agendamento, tentar outra abordagem
        if ordens.count() == 0:
            # Verificar se existem ordens para este técnico com qualquer status
            todas_ordens = OrdemServico.objects.filter(tecnico=tecnico)
            print(f"DEBUG: Total de ordens atribuídas ao técnico (com ou sem agendamento): {todas_ordens.count()}")
            
            # Segunda tentativa: buscar por ordens com status ativo
            ordens_ativas = OrdemServico.objects.filter(
                tecnico=tecnico,
                status__in=['aberta', 'em_andamento']
            )
            print(f"DEBUG: Ordens ativas para o técnico (status aberta/em_andamento): {ordens_ativas.count()}")
            
            # Adicionar ordens ativas sem data de agendamento, usando data_abertura como fallback
            for ordem in ordens_ativas:
                if not ordem.data_agendamento and ordem.data_abertura:
                    print(f"DEBUG: Adicionando ordem {ordem.numero} usando data_abertura como fallback")
                    # Recriar a ordem com data_abertura como data_agendamento para exibição no calendário
                    ordem.data_agendamento = ordem.data_abertura
                    ordens = list(ordens) + [ordem]
        
        # Converter para o formato de eventos do FullCalendar
        eventos = []
        for ordem in ordens:
            # Determinar classe CSS baseado no status
            classe = f"ordem-{ordem.status}"
            cor = "#3498db"  # Cor padrão - azul
            
            if ordem.status == 'concluida':
                cor = "#28a745"  # Verde
            elif ordem.status == 'em_andamento':
                cor = "#17a2b8"  # Azul esverdeado
            elif ordem.status == 'cancelada':
                cor = "#dc3545"  # Vermelho
            elif ordem.status == 'aberta':
                cor = "#fd7e14"  # Laranja
            
            # Formatando datas corretamente - garantindo que sempre haverá uma data válida
            data_evento = ordem.data_agendamento or ordem.data_abertura or timezone.now()
            inicio = data_evento.isoformat()
            fim = None
            
            # Se tiver duração estimada, usar ela, senão usar padrão de 2 horas
            duracao = getattr(ordem, 'duracao_estimada', 2)  # Padrão: 2 horas
            fim = (data_evento + timezone.timedelta(hours=duracao)).isoformat()
                
            # Criar evento
            cliente_nome = getattr(ordem.cliente, 'nome', 'Cliente') if ordem.cliente else "Cliente"
            evento = {
                'id': f"ordem-{ordem.id}",
                'title': f'OS #{ordem.numero} - {cliente_nome}',
                'start': inicio,
                'end': fim,
                'className': classe,
                'color': cor,
                'url': f'/ordens/detalhe/{ordem.slug}/',
                'slug': ordem.slug,
                'status': ordem.get_status_display(),
                'extendedProps': {
                    'tipo': 'ordem',
                    'status': ordem.status,
                    'descricao': getattr(ordem, 'descricao_curta', '') or "Sem descrição"
                }
            }
            eventos.append(evento)
        
        # Adicionar períodos de indisponibilidade baseados no status do técnico
        if tecnico.status in ['ferias', 'licenca', 'ausente']:
            # Para férias ou licença, vamos adicionar um evento de período inteiro
            hoje = timezone.now().date()
            evento_status = {
                'id': f"status-{tecnico.id}",
                'title': f'{tecnico.get_status_display()}',
                'start': hoje.isoformat(),
                'end': (hoje + timezone.timedelta(days=7)).isoformat(),  # Período estimado de 1 semana
                'allDay': True,
                'className': tecnico.status,
                'color': '#f39c12' if tecnico.status == 'ferias' else '#e74c3c',
                'extendedProps': {
                    'tipo': 'status',
                    'status': tecnico.status
                }
            }
            eventos.append(evento_status)
        
        print(f"DEBUG: Retornando {len(eventos)} eventos para o calendário")
        
        # Se não encontrou nenhum evento, adicionar pelo menos um evento de exemplo
        # para garantir que o calendário não fique vazio
        if len(eventos) == 0:
            print("DEBUG: Criando evento de exemplo pois nenhum evento foi encontrado")
            hoje = timezone.now()
            evento_exemplo = {
                'id': f"exemplo-{tecnico.id}",
                'title': f'Exemplo: OS #OS2025040001 - {tecnico.nome_completo}',
                'start': hoje.isoformat(),
                'end': (hoje + timezone.timedelta(hours=2)).isoformat(),
                'className': 'ordem-exemplo',
                'color': '#fd7e14',  # Laranja
                'url': '#',
                'extendedProps': {
                    'tipo': 'exemplo',
                    'descricao': "Evento de exemplo - nenhuma ordem real foi encontrada"
                }
            }
            eventos.append(evento_exemplo)
        
        # Retornar eventos em formato compatível com diferentes versões do FullCalendar
        # Enviar como array simples e não como objeto com subarrays
        response = JsonResponse(eventos, safe=False)
        
        # Adicionar cabeçalhos CORS se necessário
        for key, value in response_headers.items():
            response[key] = value
            
        return response
        
    except Exception as e:
        print("ERRO no calendário de eventos:", str(e))
        traceback.print_exc(file=sys.stdout)
        # Retornar uma resposta de erro mais informativa
        return JsonResponse({
            'error': 'Ocorreu um erro ao gerar os eventos do calendário',
            'message': str(e),
            'detalhe': "Problemas com o formato da resposta da API ou formato do JSON. Verifique o console para mais detalhes."
        }, status=500)

@login_required
def calendario_eventos_por_slug(request, slug):
    """API para fornecer eventos do calendário para um técnico usando seu slug"""
    from ordens.models import OrdemServico
    from django.http import JsonResponse
    
    try:
        print(f"DEBUG: Gerando eventos do calendário para o técnico com slug: {slug}")
        tecnico = get_object_or_404(Tecnico, slug=slug)
        
        # Configurar cabeçalhos para CORS se for uma requisição AJAX
        response_headers = {}
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            response_headers['Access-Control-Allow-Origin'] = '*'
            response_headers['Access-Control-Allow-Methods'] = 'GET, OPTIONS'
            response_headers['Access-Control-Allow-Headers'] = 'Content-Type, X-Requested-With'
        
        # Redirecionar para a função principal de API de eventos do calendário
        response = calendario_eventos_api(request, tecnico.id)
        
        # Adicionar cabeçalhos CORS se necessário
        for key, value in response_headers.items():
            response[key] = value
            
        return response
        
    except Exception as e:
        print("ERRO no calendário de eventos por slug:", str(e))
        traceback.print_exc(file=sys.stdout)
        # Retornar uma resposta de erro mais informativa
        return JsonResponse({
            'error': 'Ocorreu um erro ao gerar os eventos do calendário',
            'message': str(e),
            'detalhe': f"Técnico com slug '{slug}' encontrado, mas ocorreu um erro ao processar os eventos. Verifique os logs para mais detalhes."
        }, status=500)

@login_required
def editar_tecnico(request, slug):
    tecnico = get_object_or_404(Tecnico, slug=slug)
    
    if request.method == 'POST':
        try:
            # Atualizar dados do técnico
            tecnico.nome_completo = request.POST.get('nome_completo', '')
            tecnico.cpf = request.POST.get('cpf', '')
            tecnico.rg = request.POST.get('rg', '')
            tecnico.data_nascimento = request.POST.get('data_nascimento')
            tecnico.email = request.POST.get('email', '')
            tecnico.telefone = request.POST.get('telefone', '')
            tecnico.celular = request.POST.get('celular', '')
            tecnico.endereco = request.POST.get('endereco', '')
            tecnico.numero = request.POST.get('numero', '')
            tecnico.complemento = request.POST.get('complemento', '')
            tecnico.bairro = request.POST.get('bairro', '')
            tecnico.cidade = request.POST.get('cidade', '')
            tecnico.estado = request.POST.get('estado', '')
            tecnico.cep = request.POST.get('cep', '')
            tecnico.nivel = request.POST.get('nivel', 'junior')
            tecnico.especialidade = request.POST.get('especialidade', '')
            tecnico.status = request.POST.get('status', 'disponivel')
            tecnico.data_admissao = request.POST.get('data_admissao')
            tecnico.observacoes = request.POST.get('observacoes', '')
            tecnico.certificacoes = request.POST.get('certificacoes', '')
            tecnico.habilidades = request.POST.get('habilidades', '')
            
            # Atualizar usuário
            user = tecnico.usuario
            
            # Separar nome e sobrenome
            nomes = tecnico.nome_completo.split(' ', 1)
            primeiro_nome = nomes[0]
            sobrenome = nomes[1] if len(nomes) > 1 else ''
            
            user.first_name = primeiro_nome
            user.last_name = sobrenome
            user.email = tecnico.email
            
            # Verificar se há nova senha
            new_password = request.POST.get('password')
            if new_password and new_password.strip():
                # Verificar se as senhas coincidem
                password_confirm = request.POST.get('password_confirm')
                if new_password != password_confirm:
                    messages.error(request, 'As senhas não coincidem')
                    return render(request, 'tecnicos/editar_tecnico.html', {'tecnico': tecnico})
                
                # Definir nova senha
                user.set_password(new_password)
                messages.info(request, 'Senha do usuário atualizada com sucesso')
            
            # Verificar se há novo arquivo de foto
            if 'foto' in request.FILES:
                tecnico.foto = request.FILES['foto']
            
            # Salvar alterações
            with transaction.atomic():
                user.save()
                tecnico.save()
            
            messages.success(
                request, 
                f'Técnico {tecnico.nome_completo} (Código: {tecnico.codigo}) atualizado com sucesso!'
            )
            return redirect('tecnicos:detalhe_tecnico', slug=tecnico.slug)
            
        except Exception as e:
            messages.error(
                request, 
                f'Erro ao atualizar técnico: {str(e)}'
            )
    
    # Se o método for GET, exibir o formulário preenchido
    return render(request, 'tecnicos/editar_tecnico.html', {'tecnico': tecnico})

@login_required
def mapa_tecnicos(request):
    # Buscar todos os técnicos que possuem coordenadas de geolocalização
    tecnicos = Tecnico.objects.filter(
        latitude__isnull=False,
        longitude__isnull=False
    ).order_by('nome_completo')
    
    # Buscar também os técnicos sem coordenadas para exibir em uma lista separada
    tecnicos_sem_coordenadas = Tecnico.objects.filter(
        models.Q(latitude__isnull=True) | models.Q(longitude__isnull=True)
    ).order_by('nome_completo')
    
    # Contar técnicos por status para os indicadores
    tecnicos_disponiveis = Tecnico.objects.filter(status='disponivel').count()
    tecnicos_em_atendimento = Tecnico.objects.filter(status='em_atendimento').count()
    
    context = {
        'tecnicos': tecnicos,
        'tecnicos_sem_coordenadas': tecnicos_sem_coordenadas,
        'total_tecnicos': Tecnico.objects.count(),
        'total_com_coordenadas': tecnicos.count(),
        'tecnicos_disponiveis': tecnicos_disponiveis,
        'tecnicos_em_atendimento': tecnicos_em_atendimento,
    }
    
    return render(request, 'tecnicos/mapa_tecnicos.html', context)

@login_required
def atualizar_localizacao_api(request):
    """
    API para atualizar a localização de um técnico durante um atendimento ou em tempo real.
    
    Parâmetros POST:
    - latitude (obrigatório): latitude atual do técnico
    - longitude (obrigatório): longitude atual do técnico
    - precisao (opcional): precisão da localização em metros
    - ordem_id (opcional): ID da ordem de serviço em atendimento
    - acao (opcional): 'iniciar' ou 'finalizar' para marcar início/fim de atendimento
    """
    if request.method != 'POST':
        return JsonResponse({"status": "erro", "mensagem": "Método não permitido"}, status=405)
    
    # Verificar se o usuário é um técnico
    try:
        tecnico = request.user.tecnico
    except:
        return JsonResponse({"status": "erro", "mensagem": "Usuário não é um técnico"}, status=403)
    
    # Validar dados obrigatórios
    try:
        latitude = float(request.POST.get('latitude'))
        longitude = float(request.POST.get('longitude'))
    except (ValueError, TypeError):
        return JsonResponse({"status": "erro", "mensagem": "Coordenadas inválidas"}, status=400)
    
    # Obter precisão se fornecida
    try:
        precisao = float(request.POST.get('precisao')) if request.POST.get('precisao') else None
    except ValueError:
        precisao = None
    
    # Processar ação específica se fornecida com uma ordem
    ordem_id = request.POST.get('ordem_id')
    acao = request.POST.get('acao')
    
    if ordem_id and acao:
        from ordens.models import OrdemServico
        from django.shortcuts import get_object_or_404
        
        # Buscar a ordem de serviço
        ordem = get_object_or_404(OrdemServico, id=ordem_id)
        
        # Verificar se o técnico está atribuído a esta ordem
        if ordem.tecnico_id != tecnico.id:
            return JsonResponse({
                "status": "erro", 
                "mensagem": "Técnico não está atribuído a esta ordem"
            }, status=403)
        
        # Processar conforme a ação solicitada
        if acao == 'iniciar':
            # Iniciar atendimento
            resultado = ordem.iniciar_atendimento(latitude, longitude, precisao)
            if not resultado:
                return JsonResponse({
                    "status": "erro", 
                    "mensagem": "Não foi possível iniciar o atendimento. A ordem já foi iniciada ou não tem técnico."
                }, status=400)
                
            return JsonResponse({
                "status": "ok",
                "mensagem": "Atendimento iniciado com sucesso",
                "data": {
                    "ordem_id": ordem.id,
                    "numero": ordem.numero,
                    "status": ordem.status,
                    "data_inicio": ordem.data_inicio.isoformat() if ordem.data_inicio else None
                }
            })
            
        elif acao == 'finalizar':
            # Obter solução aplicada se fornecida
            solucao = request.POST.get('solucao')
            
            # Finalizar atendimento
            resultado = ordem.finalizar_atendimento(latitude, longitude, precisao, solucao)
            if not resultado:
                return JsonResponse({
                    "status": "erro", 
                    "mensagem": "Não foi possível finalizar o atendimento. A ordem já foi finalizada ou não foi iniciada."
                }, status=400)
                
            return JsonResponse({
                "status": "ok",
                "mensagem": "Atendimento finalizado com sucesso",
                "data": {
                    "ordem_id": ordem.id,
                    "numero": ordem.numero,
                    "status": ordem.status,
                    "data_conclusao": ordem.data_conclusao.isoformat() if ordem.data_conclusao else None
                }
            })
    
    # Caso não seja uma ação específica, apenas atualiza a localização do técnico
    ordens_atualizadas = tecnico.atualizar_localizacao(latitude, longitude)
    
    mensagem = "Localização atualizada com sucesso"
    if ordens_atualizadas:
        mensagem += ". Ordem(ns) capturada(s) alterada(s) para Em Andamento"
    
    return JsonResponse({
        "status": "ok",
        "mensagem": mensagem,
        "data": {
            "tecnico_id": tecnico.id,
            "latitude": latitude,
            "longitude": longitude,
            "ordens_atualizadas": ordens_atualizadas,
            "ultima_atualizacao": tecnico.ultima_atualizacao_local.isoformat() if tecnico.ultima_atualizacao_local else None
        }
    })

@login_required
def apontamento_ponto(request):
    """View para exibir a página de apontamento de ponto dos técnicos"""
    # Verificar se o usuário está associado a um técnico
    try:
        tecnico = request.user.tecnico
    except:
        messages.error(request, 'Você não é um técnico registrado no sistema.')
        return redirect('dashboard')
    
    # Obter o último registro de ponto do técnico
    ultimo_registro = RegistroPonto.objects.filter(tecnico=tecnico).order_by('-data_hora').first()
    
    # Pegar o último tipo para determinar o próximo tipo de registro
    proximo_tipo = 'entrada'
    if ultimo_registro:
        if ultimo_registro.tipo == 'entrada':
            proximo_tipo = 'saida'
        elif ultimo_registro.tipo == 'saida':
            proximo_tipo = 'entrada'
        elif ultimo_registro.tipo == 'inicio_intervalo':
            proximo_tipo = 'fim_intervalo'
        elif ultimo_registro.tipo == 'fim_intervalo':
            proximo_tipo = 'entrada'
    
    # Registros de ponto do dia atual
    hoje = timezone.now().date()
    registros_hoje = RegistroPonto.objects.filter(
        tecnico=tecnico,
        data_hora__date=hoje
    ).order_by('data_hora')
    
    # Histórico dos últimos 7 dias
    data_inicio = hoje - timezone.timedelta(days=7)
    historico_registros = RegistroPonto.objects.filter(
        tecnico=tecnico,
        data_hora__date__gte=data_inicio,
        data_hora__date__lt=hoje
    ).order_by('-data_hora')
    
    # Agrupar registros por dia para o histórico
    historico_por_dia = {}
    for registro in historico_registros:
        data = registro.data_hora.date()
        if data not in historico_por_dia:
            historico_por_dia[data] = []
        historico_por_dia[data].append(registro)
    
    context = {
        'tecnico': tecnico,
        'ultimo_registro': ultimo_registro,
        'proximo_tipo': proximo_tipo,
        'registros_hoje': registros_hoje,
        'historico_por_dia': historico_por_dia,
    }
    
    return render(request, 'tecnicos/apontamento_ponto.html', context)

@login_required
def registrar_ponto(request):
    """API para registrar um novo ponto"""
    if request.method != 'POST':
        return JsonResponse({'error': 'Método não permitido'}, status=405)
    
    # Verificar se o usuário está associado a um técnico
    try:
        tecnico = request.user.tecnico
    except:
        return JsonResponse({'error': 'Usuário não é um técnico'}, status=403)
    
    # Obter dados do formulário
    tipo = request.POST.get('tipo')
    latitude = request.POST.get('latitude')
    longitude = request.POST.get('longitude')
    precisao = request.POST.get('precisao')
    observacao = request.POST.get('observacao', '')
    
    # Validar tipo
    tipos_validos = ['entrada', 'saida', 'inicio_intervalo', 'fim_intervalo']
    if tipo not in tipos_validos:
        return JsonResponse({'error': 'Tipo de registro inválido'}, status=400)
    
    # Converter coordenadas para float se fornecidas
    if latitude and longitude:
        try:
            latitude = float(latitude)
            longitude = float(longitude)
            if precisao:
                precisao = float(precisao)
        except ValueError:
            return JsonResponse({'error': 'Coordenadas inválidas'}, status=400)
    
    # Obter IP do cliente
    ip = request.META.get('REMOTE_ADDR') or request.META.get('HTTP_X_FORWARDED_FOR')
    
    # Criar o registro de ponto
    registro = RegistroPonto(
        tecnico=tecnico,
        tipo=tipo,
        latitude=latitude if latitude else None,
        longitude=longitude if longitude else None,
        precisao=precisao if precisao else None,
        observacao=observacao,
        ip=ip
    )
    registro.save()
    
    # Atualizar a localização do técnico se coordenadas fornecidas
    if latitude and longitude:
        tecnico.atualizar_localizacao(latitude, longitude)
    
    return JsonResponse({
        'success': True,
        'message': f'{registro.get_tipo_display()} registrado com sucesso!',
        'registro': {
            'id': registro.id,
            'tipo': registro.get_tipo_display(),
            'data_hora': registro.data_hora.strftime('%d/%m/%Y %H:%M:%S'),
            'localizacao': registro.localizacao_formatada
        }
    })

@login_required
def relatorio_ponto(request):
    """View para exibir relatório de ponto do técnico"""
    # Verificar se o usuário está associado a um técnico
    try:
        tecnico = request.user.tecnico
    except:
        messages.error(request, 'Você não é um técnico registrado no sistema.')
        return redirect('dashboard')
    
    # Obter parâmetros de data
    data_inicio_str = request.GET.get('data_inicio')
    data_fim_str = request.GET.get('data_fim')
    
    # Se não houver datas, usar o mês atual
    hoje = timezone.now().date()
    primeiro_dia_mes = hoje.replace(day=1)
    if not data_inicio_str:
        data_inicio = primeiro_dia_mes
    else:
        try:
            data_inicio = timezone.datetime.strptime(data_inicio_str, '%Y-%m-%d').date()
        except ValueError:
            data_inicio = primeiro_dia_mes
    
    if not data_fim_str:
        data_fim = hoje
    else:
        try:
            data_fim = timezone.datetime.strptime(data_fim_str, '%Y-%m-%d').date()
        except ValueError:
            data_fim = hoje
    
    # Buscar registros no período
    registros = RegistroPonto.objects.filter(
        tecnico=tecnico,
        data_hora__date__gte=data_inicio,
        data_hora__date__lte=data_fim
    ).order_by('data_hora')
    
    # Agrupar registros por dia
    registros_por_dia = {}
    for registro in registros:
        data = registro.data_hora.date()
        if data not in registros_por_dia:
            registros_por_dia[data] = []
        registros_por_dia[data].append(registro)
    
    # Calcular horas trabalhadas por dia
    horas_por_dia = {}
    total_horas = timezone.timedelta(0)
    
    for data, regs in registros_por_dia.items():
        # Organizar registros por tipo
        entradas = [r for r in regs if r.tipo == 'entrada']
        saidas = [r for r in regs if r.tipo == 'saida']
        inicios_intervalo = [r for r in regs if r.tipo == 'inicio_intervalo']
        fins_intervalo = [r for r in regs if r.tipo == 'fim_intervalo']
        
        # Calcular tempo trabalhado
        tempo_trabalhado = timezone.timedelta(0)
        
        # Para cada par entrada/saída, calcular a diferença
        for i in range(min(len(entradas), len(saidas))):
            if i < len(saidas) and entradas[i].data_hora < saidas[i].data_hora:
                tempo_trabalhado += saidas[i].data_hora - entradas[i].data_hora
        
        # Subtrair os intervalos
        for i in range(min(len(inicios_intervalo), len(fins_intervalo))):
            if i < len(fins_intervalo) and inicios_intervalo[i].data_hora < fins_intervalo[i].data_hora:
                tempo_trabalhado -= fins_intervalo[i].data_hora - inicios_intervalo[i].data_hora
        
        # Armazenar as horas trabalhadas
        horas_por_dia[data] = tempo_trabalhado
        total_horas += tempo_trabalhado
    
    # Formatar o total de horas
    horas_total = total_horas.total_seconds() // 3600
    minutos_total = (total_horas.total_seconds() % 3600) // 60
    total_formatado = f"{int(horas_total)}h {int(minutos_total)}min"
    
    context = {
        'tecnico': tecnico,
        'data_inicio': data_inicio,
        'data_fim': data_fim,
        'registros_por_dia': registros_por_dia,
        'horas_por_dia': horas_por_dia,
        'total_horas': total_formatado,
    }
    
    return render(request, 'tecnicos/relatorio_ponto.html', context)

@login_required
def diagnosticar_calendario_api(request, tecnico_id):
    """API para diagnosticar e corrigir problemas no calendário de um técnico"""
    try:
        tecnico = get_object_or_404(Tecnico, id=tecnico_id)
        acao = request.GET.get('acao', 'diagnostico')  # 'diagnostico' ou 'corrigir'
        
        result = {
            'status': 'sucesso',
            'tecnico': {
                'id': tecnico.id,
                'nome': tecnico.nome_completo,
            },
            'problemas': [],
            'correcoes': [],
        }
        
        # Verificar ordens de serviço
        from ordens.models import OrdemServico
        ordens = OrdemServico.objects.filter(tecnico=tecnico)
        result['estatisticas'] = {
            'total_ordens': ordens.count(),
        }
        
        # Verificar ordens sem data de agendamento
        ordens_sem_agendamento = ordens.filter(data_agendamento__isnull=True, status__in=['aberta', 'em_andamento'])
        if ordens_sem_agendamento.exists():
            result['problemas'].append({
                'tipo': 'ordens_sem_agendamento',
                'quantidade': ordens_sem_agendamento.count(),
                'mensagem': f"{ordens_sem_agendamento.count()} ordens de serviço sem data de agendamento"
            })
            
            # Se for para corrigir, usar a data de abertura como data de agendamento
            if acao == 'corrigir':
                for ordem in ordens_sem_agendamento:
                    if ordem.data_abertura:
                        ordem.data_agendamento = ordem.data_abertura
                        ordem.save(update_fields=['data_agendamento'])
                        result['correcoes'].append({
                            'tipo': 'ordem_agendamento_corrigida',
                            'ordem_id': ordem.id,
                            'ordem_numero': ordem.numero,
                            'mensagem': f"OS #{ordem.numero} agora agendada para {ordem.data_agendamento.strftime('%d/%m/%Y %H:%M')}"
                        })
        
        # Verificar ordens sem cliente
        ordens_sem_cliente = ordens.filter(cliente__isnull=True)
        if ordens_sem_cliente.exists():
            result['problemas'].append({
                'tipo': 'ordens_sem_cliente',
                'quantidade': ordens_sem_cliente.count(),
                'mensagem': f"{ordens_sem_cliente.count()} ordens de serviço sem cliente associado"
            })
            # Não corrigimos este problema pois não temos como determinar o cliente
        
        # Verificar se o técnico tem coordenadas de localização
        if tecnico.latitude is None or tecnico.longitude is None:
            result['problemas'].append({
                'tipo': 'sem_coordenadas',
                'mensagem': "Técnico sem coordenadas de localização"
            })
        
        # Verificar se o técnico tem slug
        if not tecnico.slug:
            result['problemas'].append({
                'tipo': 'sem_slug',
                'mensagem': "Técnico sem identificador único (slug)"
            })
            
            # Se for para corrigir, gerar o slug
            if acao == 'corrigir':
                tecnico.save()  # O método save() já gera o slug se não existir
                result['correcoes'].append({
                    'tipo': 'slug_gerado',
                    'mensagem': f"Gerado identificador único: {tecnico.slug}"
                })
        
        # Verificar se há ordens em status inconsistente
        ordens_inconsistentes = ordens.filter(
            status='em_andamento', 
            data_inicio__isnull=True
        )
        
        if ordens_inconsistentes.exists():
            result['problemas'].append({
                'tipo': 'ordens_status_inconsistente',
                'quantidade': ordens_inconsistentes.count(),
                'mensagem': f"{ordens_inconsistentes.count()} ordens em andamento sem data de início"
            })
            
            # Se for para corrigir, atualizar o status para aberta quando não houver data de início
            if acao == 'corrigir':
                for ordem in ordens_inconsistentes:
                    ordem.status = 'aberta'
                    ordem.save(update_fields=['status'])
                    result['correcoes'].append({
                        'tipo': 'ordem_status_corrigido',
                        'ordem_id': ordem.id,
                        'ordem_numero': ordem.numero,
                        'mensagem': f"OS #{ordem.numero} corrigida para status 'aberta'"
                    })
        
        # Resumo do diagnóstico
        result['resumo'] = {
            'total_problemas': len(result['problemas']),
            'total_correcoes': len(result['correcoes']),
            'calendario_saudavel': len(result['problemas']) == 0
        }
        
        return JsonResponse(result)
        
    except Exception as e:
        traceback.print_exc(file=sys.stdout)
        return JsonResponse({
            'status': 'erro',
            'mensagem': f"Erro ao diagnosticar calendário: {str(e)}"
        }, status=500)

@login_required
def verificar_status_calendario(request):
    """Verifica o status da API do calendário e retorna informações de diagnóstico"""
    from django.http import JsonResponse
    from ordens.models import OrdemServico
    
    try:
        # Verificar conexão com o banco de dados
        tecnico_count = Tecnico.objects.count()
        ordem_count = OrdemServico.objects.count()
        
        # Verificar se existem técnicos com ordens
        tecnicos_com_ordens = Tecnico.objects.filter(
            ordemservico__isnull=False
        ).distinct().count()
        
        # Verificar se existem ordens com agendamento
        ordens_agendadas = OrdemServico.objects.filter(
            data_agendamento__isnull=False
        ).count()
        
        # Verificar URLs configuradas
        from django.urls import reverse, NoReverseMatch
        
        urls_status = {}
        urls_para_verificar = [
            'tecnicos:calendario_eventos_api',
            'tecnicos:calendario_eventos_por_slug',
            'tecnicos:diagnosticar_calendario_api',
        ]
        
        for url_name in urls_para_verificar:
            try:
                # Tentar resolver a URL com parâmetros fictícios
                if url_name == 'tecnicos:calendario_eventos_api':
                    reverse(url_name, args=[1])
                elif url_name == 'tecnicos:calendario_eventos_por_slug':
                    reverse(url_name, args=['teste'])
                elif url_name == 'tecnicos:diagnosticar_calendario_api':
                    reverse(url_name, args=[1])
                
                urls_status[url_name] = {
                    'status': 'configurada',
                    'mensagem': 'URL está corretamente configurada'
                }
            except NoReverseMatch as e:
                urls_status[url_name] = {
                    'status': 'erro',
                    'mensagem': f'Erro ao resolver URL: {str(e)}'
                }
        
        # Verificar campos necessários no modelo de Técnico
        from django.db import connection
        
        campos_tecnico = {}
        try:
            with connection.cursor() as cursor:
                cursor.execute("PRAGMA table_info(tecnicos_tecnico)")
                colunas = cursor.fetchall()
                # Formato: (id, nome, tipo, not_null, default, pk)
                campos_tecnico = {col[1]: {'tipo': col[2], 'nullable': col[3] == 0} for col in colunas}
        except Exception as e:
            campos_tecnico = {'erro': f'Não foi possível verificar os campos: {str(e)}'}
        
        # Verificar model de OrdemServico
        campos_ordem = {}
        try:
            with connection.cursor() as cursor:
                cursor.execute("PRAGMA table_info(ordens_ordemservico)")
                colunas = cursor.fetchall()
                campos_ordem = {col[1]: {'tipo': col[2], 'nullable': col[3] == 0} for col in colunas}
        except Exception as e:
            campos_ordem = {'erro': f'Não foi possível verificar os campos: {str(e)}'}
        
        # Verificar se há erros com data_criacao
        problemas_schema = []
        if 'data_criacao' not in campos_tecnico and 'tecnicos_tecnico.data_criacao' in str(campos_tecnico):
            problemas_schema.append("Erro detectado: campo 'data_criacao' referenciado mas não existe na tabela tecnicos_tecnico")
        
        # Resumo e resultado
        status_geral = 'operacional'
        mensagem_geral = 'API do calendário está operacional'
        
        if tecnicos_com_ordens == 0:
            status_geral = 'aviso'
            mensagem_geral = 'API operacional, mas nenhum técnico tem ordens cadastradas'
        
        if ordens_agendadas == 0:
            status_geral = 'aviso'
            mensagem_geral = 'API operacional, mas nenhuma ordem tem data de agendamento'
        
        if problemas_schema:
            status_geral = 'erro'
            mensagem_geral = 'Problemas detectados no esquema do banco de dados'
        
        return JsonResponse({
            'status': status_geral,
            'mensagem': mensagem_geral,
            'diagnostico': {
                'database': {
                    'tecnicos': tecnico_count,
                    'ordens': ordem_count,
                    'tecnicos_com_ordens': tecnicos_com_ordens,
                    'ordens_agendadas': ordens_agendadas
                },
                'urls': urls_status,
                'schema': {
                    'campos_tecnico': campos_tecnico,
                    'campos_ordem': campos_ordem,
                    'problemas': problemas_schema
                }
            },
            'timestamp': timezone.now().isoformat(),
            'ambiente': {
                'debug': settings.DEBUG
            }
        })
    
    except Exception as e:
        print("ERRO na verificação do status do calendário:", str(e))
        traceback.print_exc(file=sys.stdout)
        return JsonResponse({
            'status': 'erro',
            'mensagem': f'Erro ao verificar status da API: {str(e)}',
            'timestamp': timezone.now().isoformat()
        }, status=500)
