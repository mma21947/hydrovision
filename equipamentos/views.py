from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse, HttpResponse
from django.utils import timezone
from django.urls import reverse
from django.db import transaction, models
import qrcode
from io import BytesIO
from PIL import Image, ImageDraw
import json

from .models import Equipamento, CategoriaEquipamento, ManutencaoEquipamento
from .forms import EquipamentoForm, ManutencaoEquipamentoForm
from clientes.models import Cliente

@login_required
def listar_equipamentos(request):
    # Obter parâmetros de filtro da URL
    status_filter = request.GET.get('status')
    cliente_id = request.GET.get('cliente')
    categoria_id = request.GET.get('categoria')
    search_query = request.GET.get('q')
    
    # Iniciar queryset com prefetch_related para garantir que as fotos sejam carregadas
    queryset = Equipamento.objects.all().select_related('cliente', 'categoria')
    
    # Aplicar filtros
    if status_filter:
        queryset = queryset.filter(status=status_filter)
    
    if cliente_id:
        queryset = queryset.filter(cliente_id=cliente_id)
    
    if categoria_id:
        queryset = queryset.filter(categoria_id=categoria_id)
    
    # Aplicar busca se especificada
    if search_query:
        queryset = queryset.filter(
            # Buscar pelo código, nome, marca ou modelo
            models.Q(codigo__icontains=search_query) |
            models.Q(nome__icontains=search_query) |
            models.Q(marca__icontains=search_query) |
            models.Q(modelo__icontains=search_query) |
            models.Q(numero_serie__icontains=search_query) |
            models.Q(cliente__nome__icontains=search_query) |
            models.Q(descricao__icontains=search_query)
        )
    
    # Ordenar pelos mais recentes primeiro
    equipamentos = list(queryset.order_by('cliente__nome', 'nome'))
    
    # Debug - Verificar se as fotos estão sendo carregadas corretamente
    for eq in equipamentos:
        print(f"Equipamento {eq.codigo} - Nome: {eq.nome}")
        if eq.foto:
            print(f"  Foto: {eq.foto.name} - URL: {eq.foto.url}")
        else:
            print(f"  Sem foto")
    
    # Obter listas para filtros
    clientes = Cliente.objects.filter(ativo=True).order_by('nome')
    categorias = CategoriaEquipamento.objects.all().order_by('nome')
    
    # Adicionar URL base de mídia para depuração
    from django.conf import settings
    media_url = settings.MEDIA_URL
    media_root = settings.MEDIA_ROOT
    print(f"MEDIA_URL: {media_url}, MEDIA_ROOT: {media_root}")
    
    context = {
        'equipamentos': equipamentos,
        'clientes': clientes,
        'categorias': categorias,
        'media_url': media_url,
    }
    
    return render(request, 'equipamentos/listar_equipamentos.html', context)

@login_required
def detalhe_equipamento(request, slug):
    try:
        equipamento = Equipamento.objects.get(slug=slug)
        
        # Buscar manutenções do equipamento
        manutencoes = ManutencaoEquipamento.objects.filter(equipamento=equipamento).order_by('-data')
        
        # Buscar ordens de serviço associadas
        ordens = equipamento.ordens.all().order_by('-data_abertura')
        
        context = {
            'equipamento': equipamento,
            'manutencoes': manutencoes,
            'ordens': ordens,
        }
        
        return render(request, 'equipamentos/detalhe_equipamento.html', context)
    except Equipamento.DoesNotExist:
        messages.error(request, 'Equipamento não encontrado')
        return redirect('listar_equipamentos')

@login_required
def novo_equipamento(request):
    # Pegar o cliente_id da query string, se existir
    cliente_id = request.GET.get('cliente_id')
    
    if request.method == 'POST':
        # Log para debug
        print(f"FILES recebidos: {request.FILES}")
        print(f"Foto no FILES: {'foto' in request.FILES}")
        
        form = EquipamentoForm(request.POST, request.FILES)
        if form.is_valid():
            try:
                # Log campos do form para debug
                print(f"Formulário válido. Foto presente: {bool(form.cleaned_data.get('foto'))}")
                
                equipamento = form.save()
                messages.success(
                    request, 
                    f'Equipamento {equipamento.codigo} cadastrado com sucesso!'
                )
                # Log do equipamento salvo
                print(f"Equipamento salvo: {equipamento.id}, Foto: {equipamento.foto}")
                
                return redirect('detalhe_equipamento', slug=equipamento.slug)
            except Exception as e:
                print(f"ERRO ao salvar equipamento: {str(e)}")
                messages.error(
                    request, 
                    f'Erro ao cadastrar equipamento: {str(e)}'
                )
        else:
            print(f"Erros no form: {form.errors}")
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f'Erro no campo {field}: {error}')
    else:
        # Inicializar o form com cliente_id se fornecido
        initial_data = {}
        if cliente_id:
            try:
                cliente = Cliente.objects.get(id=cliente_id)
                initial_data = {'cliente': cliente}
            except Cliente.DoesNotExist:
                pass
        
        form = EquipamentoForm(initial=initial_data)
    
    # Obter listas para os campos de seleção
    clientes = Cliente.objects.filter(ativo=True).order_by('nome')
    categorias = CategoriaEquipamento.objects.all().order_by('nome')
    
    context = {
        'form': form,
        'clientes': clientes,
        'categorias': categorias,
        'cliente_id': cliente_id,  # Passar o cliente_id para o template
    }
    return render(request, 'equipamentos/novo_equipamento.html', context)

@login_required
def editar_equipamento(request, slug):
    equipamento = get_object_or_404(Equipamento, slug=slug)
    
    if request.method == 'POST':
        form = EquipamentoForm(request.POST, request.FILES, instance=equipamento)
        if form.is_valid():
            try:
                equipamento = form.save()
                messages.success(
                    request, 
                    f'Equipamento {equipamento.codigo} atualizado com sucesso!'
                )
                return redirect('detalhe_equipamento', slug=equipamento.slug)
            except Exception as e:
                messages.error(
                    request, 
                    f'Erro ao atualizar equipamento: {str(e)}'
                )
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f'Erro no campo {field}: {error}')
    else:
        form = EquipamentoForm(instance=equipamento)
    
    clientes = Cliente.objects.filter(ativo=True).order_by('nome')
    categorias = CategoriaEquipamento.objects.all().order_by('nome')
    
    context = {
        'form': form,
        'equipamento': equipamento,
        'clientes': clientes,
        'categorias': categorias,
    }
    return render(request, 'equipamentos/editar_equipamento.html', context)

@login_required
def excluir_equipamento(request, slug):
    equipamento = get_object_or_404(Equipamento, slug=slug)
    
    if request.method == 'POST':
        try:
            nome = equipamento.nome
            codigo = equipamento.codigo
            equipamento.delete()
            messages.success(request, f'Equipamento {codigo} - {nome} excluído com sucesso!')
            return redirect('listar_equipamentos')
        except Exception as e:
            messages.error(request, f'Erro ao excluir equipamento: {str(e)}')
            return redirect('detalhe_equipamento', slug=equipamento.slug)
    
    context = {
        'equipamento': equipamento
    }
    return render(request, 'equipamentos/excluir_equipamento.html', context)

@login_required
def categorias_equipamento(request):
    # Obter parâmetros de filtro da URL
    search_query = request.GET.get('q')
    ordenacao = request.GET.get('ordenar', 'nome')
    
    # Iniciar queryset
    queryset = CategoriaEquipamento.objects.all()
    
    # Aplicar busca se especificada
    if search_query:
        queryset = queryset.filter(
            models.Q(nome__icontains=search_query) |
            models.Q(descricao__icontains=search_query)
        )
    
    # Aplicar ordenação
    if ordenacao:
        queryset = queryset.order_by(ordenacao)
    else:
        queryset = queryset.order_by('nome')
    
    categorias = queryset
    
    context = {
        'categorias': categorias
    }
    return render(request, 'equipamentos/categorias_equipamento.html', context)

@login_required
def nova_categoria_equipamento(request):
    if request.method == 'POST':
        try:
            nome = request.POST.get('nome')
            descricao = request.POST.get('descricao', '')
            
            categoria = CategoriaEquipamento(nome=nome, descricao=descricao)
            categoria.save()
            
            messages.success(request, f'Categoria "{nome}" cadastrada com sucesso!')
            return redirect('categorias_equipamento')
        except Exception as e:
            messages.error(request, f'Erro ao cadastrar categoria: {str(e)}')
    
    return render(request, 'equipamentos/nova_categoria_equipamento.html')

@login_required
def editar_categoria_equipamento(request, slug):
    categoria = get_object_or_404(CategoriaEquipamento, slug=slug)
    
    if request.method == 'POST':
        try:
            categoria.nome = request.POST.get('nome')
            categoria.descricao = request.POST.get('descricao', '')
            categoria.save()
            
            messages.success(request, f'Categoria "{categoria.nome}" atualizada com sucesso!')
            return redirect('categorias_equipamento')
        except Exception as e:
            messages.error(request, f'Erro ao atualizar categoria: {str(e)}')
    
    context = {
        'categoria': categoria
    }
    return render(request, 'equipamentos/editar_categoria_equipamento.html', context)

@login_required
def detalhes_categoria_equipamento(request, categoria_id):
    # Buscar a categoria pelo ID
    categoria = get_object_or_404(CategoriaEquipamento, id=categoria_id)
    
    # Buscar equipamentos desta categoria
    equipamentos = Equipamento.objects.filter(categoria=categoria).order_by('cliente__nome', 'nome')
    
    context = {
        'categoria': categoria,
        'equipamentos': equipamentos,
    }
    
    return render(request, 'equipamentos/detalhes_categoria_equipamento.html', context)

@login_required
def gerar_qrcode_equipamento(request, slug):
    equipamento = get_object_or_404(Equipamento, slug=slug)
    
    # URL para o detalhe do equipamento
    url = request.build_absolute_uri(reverse('detalhe_equipamento', args=[equipamento.slug]))
    
    # Criar QR Code
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=4,
    )
    qr.add_data(url)
    qr.make(fit=True)
    
    img = qr.make_image(fill_color="black", back_color="white")
    
    # Adicionar texto descritivo abaixo do QR code
    buffer = BytesIO()
    img.save(buffer, format="PNG")
    
    # Retornar a imagem como resposta
    response = HttpResponse(buffer.getvalue(), content_type='image/png')
    response['Content-Disposition'] = f'attachment; filename="qrcode-{equipamento.codigo}.png"'
    
    return response

@login_required
def equipamentos_cliente(request, slug):
    cliente = get_object_or_404(Cliente, slug=slug)
    
    # Buscar todos os equipamentos do cliente, independente do status
    equipamentos = Equipamento.objects.filter(cliente=cliente).order_by('nome')
    
    # Log detalhado para diagnóstico
    print(f"DEBUG - Cliente ID: {cliente.id} - {cliente.nome}")
    print(f"DEBUG - Total de equipamentos encontrados: {equipamentos.count()}")
    for eq in equipamentos:
        print(f"DEBUG - Equipamento: {eq.id} - {eq.codigo} - {eq.nome} - {eq.status}")
    
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest' or request.GET.get('format') == 'json':
        # Retornar dados JSON para solicitações AJAX ou parâmetro format=json
        equipamentos_data = []
        for equipamento in equipamentos:
            equipamentos_data.append({
                'id': equipamento.id,
                'codigo': equipamento.codigo or '',
                'nome': equipamento.nome or '',
                'marca': equipamento.marca or '',
                'modelo': equipamento.modelo or '',
                'local': equipamento.local_instalacao or '',
                'status': equipamento.status or 'ativo'
            })
        
        data = {
            'cliente': {
                'id': cliente.id, 
                'nome': cliente.nome
            },
            'equipamentos': equipamentos_data
        }
        
        # Log detalhado dos dados sendo retornados
        print(f"DEBUG - Retornando JSON com {len(equipamentos_data)} equipamentos para o cliente {cliente.nome}")
        
        return JsonResponse(data)
    
    # Renderizar template para solicitações regulares
    context = {
        'cliente': cliente,
        'equipamentos': equipamentos
    }
    return render(request, 'equipamentos/equipamentos_cliente.html', context)

@login_required
def historico_equipamento(request, slug):
    equipamento = get_object_or_404(Equipamento, slug=slug)
    
    # Buscar todas as ordens de serviço deste equipamento
    ordens = equipamento.ordens.all().order_by('-data_abertura')
    
    context = {
        'equipamento': equipamento,
        'ordens': ordens
    }
    
    return render(request, 'equipamentos/historico_equipamento.html', context)

@login_required
def nova_manutencao(request, equipamento_slug):
    equipamento = get_object_or_404(Equipamento, slug=equipamento_slug)
    
    if request.method == 'POST':
        try:
            with transaction.atomic():
                # Criar registro de manutenção
                manutencao = ManutencaoEquipamento(
                    equipamento=equipamento,
                    tipo=request.POST.get('tipo'),
                    data=timezone.now(),
                    descricao=request.POST.get('descricao'),
                    solucao=request.POST.get('solucao', ''),
                    responsavel=request.POST.get('responsavel'),
                    custo=request.POST.get('custo', 0) or 0
                )
                
                # Associar ordem de serviço se fornecida
                ordem_id = request.POST.get('ordem_servico')
                if ordem_id:
                    manutencao.ordem_servico_id = ordem_id
                
                manutencao.save()
                
                # Atualizar status do equipamento para "manutenção" se for manutenção corretiva
                if manutencao.tipo == 'corretiva' and not request.POST.get('manter_status'):
                    equipamento.status = 'manutencao'
                    equipamento.save()
                
                messages.success(request, 'Manutenção registrada com sucesso!')
                return redirect('detalhe_equipamento', slug=equipamento.slug)
                
        except Exception as e:
            messages.error(request, f'Erro ao registrar manutenção: {str(e)}')
    
    context = {
        'equipamento': equipamento,
        'now': timezone.now()  # Adicionar a data atual no contexto
    }
    return render(request, 'equipamentos/nova_manutencao.html', context)

@login_required
def adicionar_categoria_equipamento_ajax(request):
    """
    View para adicionar uma nova categoria de equipamento via AJAX
    Retorna um objeto JSON com o resultado da operação
    """
    if request.method != 'POST':
        return JsonResponse({'success': False, 'errors': ['Método não permitido']})
    
    try:
        nome = request.POST.get('nome', '').strip()
        descricao = request.POST.get('descricao', '').strip()
        
        # Validação
        errors = []
        if not nome:
            errors.append('O nome da categoria é obrigatório')
        
        if errors:
            return JsonResponse({'success': False, 'errors': errors})
        
        # Criar nova categoria
        categoria = CategoriaEquipamento(nome=nome, descricao=descricao)
        categoria.save()
        
        # Retornar dados da categoria criada
        return JsonResponse({
            'success': True,
            'message': f'Categoria "{nome}" criada com sucesso',
            'categoria': {
                'id': categoria.id,
                'nome': categoria.nome,
                'descricao': categoria.descricao
            }
        })
        
    except Exception as e:
        return JsonResponse({'success': False, 'errors': [str(e)]})

@login_required
def excluir_categoria_equipamento(request, categoria_id):
    """
    View para excluir categoria de equipamento via formulário
    Recebe o ID da categoria por URL e redireciona para a listagem após exclusão
    """
    # Buscar a categoria pelo ID
    categoria = get_object_or_404(CategoriaEquipamento, id=categoria_id)
    
    try:
        # Verificar se tem equipamentos associados
        equipamentos_associados = Equipamento.objects.filter(categoria=categoria).count()
        
        # Tentar excluir a categoria
        nome_categoria = categoria.nome
        categoria.delete()
        
        # Mensagem de sucesso com aviso sobre equipamentos afetados
        if equipamentos_associados > 0:
            messages.success(request, f'Categoria "{nome_categoria}" excluída com sucesso. {equipamentos_associados} equipamento(s) foram afetados.')
        else:
            messages.success(request, f'Categoria "{nome_categoria}" excluída com sucesso.')
            
        return redirect('categorias_equipamento')
    except Exception as e:
        messages.error(request, f'Erro ao excluir categoria: {str(e)}')
        return redirect('detalhes_categoria_equipamento', categoria_id=categoria_id)

@login_required
def excluir_categoria_equipamento_ajax(request):
    """
    View para excluir categoria de equipamento via AJAX
    Recebe o ID da categoria por POST e retorna resultado via JSON
    """
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'Método não permitido'})
    
    try:
        # Obter ID da categoria do JSON recebido
        data = json.loads(request.body)
        categoria_id = data.get('categoria_id')
        
        if not categoria_id:
            return JsonResponse({'success': False, 'error': 'ID da categoria não fornecido'})
        
        # Buscar categoria
        categoria = get_object_or_404(CategoriaEquipamento, id=categoria_id)
        
        # Verificar se tem equipamentos associados
        equipamentos_associados = Equipamento.objects.filter(categoria=categoria).count()
        
        # Tentar excluir a categoria
        nome_categoria = categoria.nome
        categoria.delete()
        
        # Retornar resultado
        if equipamentos_associados > 0:
            mensagem = f'Categoria "{nome_categoria}" excluída com sucesso. {equipamentos_associados} equipamento(s) foram afetados.'
        else:
            mensagem = f'Categoria "{nome_categoria}" excluída com sucesso.'
            
        return JsonResponse({'success': True, 'message': mensagem})
    except CategoriaEquipamento.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Categoria não encontrada'})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})

@login_required
def editar_categoria_equipamento_ajax(request):
    """
    View para editar categoria de equipamento via AJAX
    Recebe os dados da categoria por POST e retorna resultado via JSON
    """
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'Método não permitido'})
    
    try:
        categoria_id = request.POST.get('categoria_id')
        nome = request.POST.get('nome', '').strip()
        descricao = request.POST.get('descricao', '').strip()
        
        # Validação
        errors = []
        if not categoria_id:
            errors.append('ID da categoria não fornecido')
        if not nome:
            errors.append('O nome da categoria é obrigatório')
        
        if errors:
            return JsonResponse({'success': False, 'error': errors[0]})
        
        # Buscar categoria
        categoria = get_object_or_404(CategoriaEquipamento, id=categoria_id)
        
        # Atualizar dados
        categoria.nome = nome
        categoria.descricao = descricao
        categoria.save()
        
        # Retornar resultado
        return JsonResponse({
            'success': True,
            'message': f'Categoria "{nome}" atualizada com sucesso',
            'categoria': {
                'id': categoria.id,
                'nome': categoria.nome,
                'descricao': categoria.descricao
            }
        })
        
    except CategoriaEquipamento.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Categoria não encontrada'})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})

@login_required
def categoria_json(request, categoria_id):
    """
    View para retornar os dados de uma categoria em formato JSON
    """
    try:
        categoria = get_object_or_404(CategoriaEquipamento, id=categoria_id)
        
        return JsonResponse({
            'success': True,
            'categoria': {
                'id': categoria.id,
                'nome': categoria.nome,
                'descricao': categoria.descricao or '',
                'slug': categoria.slug
            }
        })
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})

@login_required
def verificar_equipamentos_categoria(request, categoria_id):
    """
    View para verificar se uma categoria tem equipamentos associados
    """
    try:
        categoria = get_object_or_404(CategoriaEquipamento, id=categoria_id)
        count = Equipamento.objects.filter(categoria=categoria).count()
        
        return JsonResponse({
            'success': True,
            'tem_equipamentos': count > 0,
            'count': count
        })
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})
