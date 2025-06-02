from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.http import JsonResponse
from django.utils import timezone
from django.db import models
from django.core.paginator import Paginator

from .models import Cliente, ContratoCliente, Empresa, ContratoEmpresa
from usuarios.views import is_admin

# Função para verificar se o usuário não é um técnico
def not_tecnico(user):
    """Verifica se o usuário não é um técnico."""
    if not user.is_authenticated:
        return False
    try:
        # Verificar se o usuário é superusuário
        if user.is_superuser:
            return True
        
        # Verificar se o perfil existe
        if not hasattr(user, 'perfil'):
            # Se não tiver perfil, retorna True para evitar loop
            print(f"Usuário {user.username} não tem perfil associado")
            return True
            
        # Verificar o tipo de perfil
        if user.perfil.tipo != 'tecnico':
            print(f"Usuário {user.username} tem perfil {user.perfil.tipo}")
            return True
        else:
            print(f"Usuário {user.username} é técnico e não deve acessar")
            return False
    except Exception as e:
        print(f"Erro ao verificar permissões: {str(e)}")
        # Em caso de erro, permitir acesso para evitar loops
        return True

# Wrapped login_required que redireciona técnicos
def non_tecnico_required(view_func):
    """
    Decorator personalizado que combina login_required e verificação de perfil técnico.
    Redireciona técnicos para o dashboard.
    """
    @login_required
    def _wrapped_view(request, *args, **kwargs):
        # Verificar se o usuário é técnico
        if hasattr(request.user, 'perfil') and request.user.perfil.tipo == 'tecnico':
            messages.error(request, 'Você não tem permissão para acessar esta área.')
            return redirect('dashboard')
        return view_func(request, *args, **kwargs)
    return _wrapped_view

@non_tecnico_required
def novo_cliente(request):
    if request.method == 'POST':
        try:
            # Extrair dados do formulário
            cliente = Cliente(
                nome=request.POST.get('nome', ''),
                tipo=request.POST.get('tipo', 'PF'),
                cpf_cnpj=request.POST.get('cpf_cnpj', ''),
                email=request.POST.get('email', ''),
                telefone=request.POST.get('telefone', ''),
                celular=request.POST.get('celular', ''),
                endereco=request.POST.get('endereco', ''),
                numero=request.POST.get('numero', ''),
                complemento=request.POST.get('complemento', ''),
                bairro=request.POST.get('bairro', ''),
                cidade=request.POST.get('cidade', ''),
                estado=request.POST.get('estado', ''),
                cep=request.POST.get('cep', ''),
                observacoes=request.POST.get('observacoes', ''),
            )
            
            # Campos opcionais
            data_nascimento = request.POST.get('data_nascimento')
            if data_nascimento:
                cliente.data_nascimento = data_nascimento
            
            # Salvar o cliente - o código será gerado automaticamente pelo método save()
            cliente.save()
            
            messages.success(
                request, 
                f'Cliente {cliente.nome} (Código: {cliente.codigo}) cadastrado com sucesso!'
            )
            return redirect('listar_clientes')
            
        except Exception as e:
            messages.error(
                request, 
                f'Erro ao cadastrar cliente: {str(e)}'
            )
    
    return render(request, 'clientes/novo_cliente.html')

@non_tecnico_required
def listar_clientes(request):
    # Buscar todos os clientes
    clientes = Cliente.objects.all()
    
    # Filtragem por termo de busca
    termo_busca = request.GET.get('q', '')
    if termo_busca:
        clientes = clientes.filter(
            models.Q(nome__icontains=termo_busca) |
            models.Q(codigo__icontains=termo_busca) |
            models.Q(cpf_cnpj__icontains=termo_busca)
        )
    
    # Ordenar por nome
    clientes = clientes.order_by('nome')
    
    context = {
        'clientes': clientes,
        'termo_busca': termo_busca
    }
    
    return render(request, 'clientes/listar_clientes.html', context)

@non_tecnico_required
def detalhe_cliente(request, slug):
    try:
        cliente = Cliente.objects.get(slug=slug)
        contratos = ContratoCliente.objects.filter(cliente=cliente).order_by('-data_upload')
        return render(request, 'clientes/detalhe_cliente.html', {'cliente': cliente, 'contratos': contratos})
    except Cliente.DoesNotExist:
        messages.error(request, 'Cliente não encontrado')
        return redirect('listar_clientes')

@non_tecnico_required
def editar_cliente(request, slug):
    cliente = get_object_or_404(Cliente, slug=slug)
    contratos = ContratoCliente.objects.filter(cliente=cliente).order_by('-data_upload')
    
    if request.method == 'POST':
        try:
            # Verifica se existe um arquivo de contrato no request
            if 'contrato' in request.FILES:
                arquivo_contrato = request.FILES['contrato']
                descricao_contrato = request.POST.get('descricao_contrato', 'Contrato')
                
                # Salva o contrato
                contrato = ContratoCliente(
                    cliente=cliente,
                    arquivo=arquivo_contrato,
                    descricao=descricao_contrato
                )
                contrato.save()
                
                messages.success(
                    request, 
                    f'Contrato "{descricao_contrato}" adicionado com sucesso!'
                )
                return redirect('editar_cliente', slug=cliente.slug)
            
            # Atualizar dados do cliente
            cliente.nome = request.POST.get('nome', '')
            cliente.tipo = request.POST.get('tipo', 'PF')
            cliente.cpf_cnpj = request.POST.get('cpf_cnpj', '')
            cliente.email = request.POST.get('email', '')
            cliente.telefone = request.POST.get('telefone', '')
            cliente.celular = request.POST.get('celular', '')
            cliente.endereco = request.POST.get('endereco', '')
            cliente.numero = request.POST.get('numero', '')
            cliente.complemento = request.POST.get('complemento', '')
            cliente.bairro = request.POST.get('bairro', '')
            cliente.cidade = request.POST.get('cidade', '')
            cliente.estado = request.POST.get('estado', '')
            cliente.cep = request.POST.get('cep', '')
            cliente.observacoes = request.POST.get('observacoes', '')
            
            # Campos opcionais
            data_nascimento = request.POST.get('data_nascimento')
            if data_nascimento:
                cliente.data_nascimento = data_nascimento
                
            cliente.save()
            
            messages.success(
                request, 
                f'Cliente {cliente.nome} atualizado com sucesso!'
            )
            return redirect('detalhe_cliente', slug=cliente.slug)
            
        except Exception as e:
            messages.error(
                request, 
                f'Erro ao atualizar cliente: {str(e)}'
            )
    
    return render(request, 'clientes/editar_cliente.html', {'cliente': cliente, 'contratos': contratos})

@non_tecnico_required
def excluir_contrato(request, contrato_id):
    contrato = get_object_or_404(ContratoCliente, id=contrato_id)
    cliente_slug = contrato.cliente.slug
    
    try:
        descricao = contrato.descricao
        contrato.delete()
        messages.success(request, f'Contrato "{descricao}" excluído com sucesso!')
    except Exception as e:
        messages.error(request, f'Erro ao excluir contrato: {str(e)}')
        
    return redirect('editar_cliente', slug=cliente_slug)

@non_tecnico_required
def excluir_cliente(request, slug):
    """Exclui um cliente do sistema."""
    cliente = get_object_or_404(Cliente, slug=slug)
    
    if request.method == 'POST':
        nome_cliente = cliente.nome
        try:
            cliente.delete()
            messages.success(request, f'Cliente "{nome_cliente}" excluído com sucesso!')
        except Exception as e:
            messages.error(request, f'Erro ao excluir cliente: {str(e)}')
        return redirect('listar_clientes')
    
    # Se não for POST, redirect para a página de detalhes
    # Isso não deve acontecer pois a exclusão é feita via modal
    return redirect('detalhe_cliente', slug=slug)

@non_tecnico_required
def buscar_cliente_api(request):
    termo = request.GET.get('termo', '')
    if not termo:
        return JsonResponse({'clientes': []})
    
    clientes = Cliente.objects.filter(
        models.Q(nome__icontains=termo) |
        models.Q(cpf_cnpj__icontains=termo) |
        models.Q(codigo__icontains=termo)
    )[:10]
    
    resultado = []
    for cliente in clientes:
        resultado.append({
            'id': cliente.id,
            'nome': cliente.nome,
            'cpf_cnpj': cliente.cpf_cnpj,
            'telefone': cliente.celular,
            'codigo': cliente.codigo,
            'url': f'/clientes/detalhe/{cliente.slug}/'
        })
    
    return JsonResponse({'clientes': resultado})

@non_tecnico_required
def buscar_cliente_por_id_api(request):
    """Retorna os dados completos de um cliente específico por ID"""
    cliente_id = request.GET.get('id')
    
    if not cliente_id:
        return JsonResponse({'success': False, 'message': 'ID do cliente não fornecido'})
    
    try:
        cliente = Cliente.objects.get(id=cliente_id)
        
        # Retorna dados completos incluindo endereço
        dados_cliente = {
            'success': True,
            'id': cliente.id,
            'nome': cliente.nome,
            'cpf_cnpj': cliente.cpf_cnpj,
            'telefone': cliente.telefone,
            'celular': cliente.celular,
            'email': cliente.email,
            # Dados de endereço
            'endereco': cliente.endereco,
            'numero': cliente.numero,
            'complemento': cliente.complemento or '',
            'bairro': cliente.bairro,
            'cidade': cliente.cidade,
            'estado': cliente.estado,
            'cep': cliente.cep
        }
        
        return JsonResponse(dados_cliente)
        
    except Cliente.DoesNotExist:
        return JsonResponse({'success': False, 'message': 'Cliente não encontrado'})
    except Exception as e:
        return JsonResponse({'success': False, 'message': f'Erro ao buscar cliente: {str(e)}'})

@login_required
@user_passes_test(lambda u: not u.is_tecnico)
def nova_empresa(request):
    if request.method == 'POST':
        form = EmpresaForm(request.POST, request.FILES)
        if form.is_valid():
            empresa = form.save()
            messages.success(request, 'Empresa cadastrada com sucesso!')
            return redirect('detalhe_empresa', slug=empresa.slug)
        else:
            messages.error(request, 'Por favor, corrija os erros abaixo.')
    else:
        form = EmpresaForm()
    
    return render(request, 'empresas/form.html', {
        'form': form,
        'titulo': 'Nova Empresa'
    })

@login_required
@user_passes_test(lambda u: not u.is_tecnico)
def listar_empresas(request):
    empresas = Empresa.objects.all()
    
    filtro = request.GET.get('filtro', '')
    if filtro:
        empresas = empresas.filter(
            Q(razao_social__icontains=filtro) |
            Q(nome_fantasia__icontains=filtro) |
            Q(cnpj__icontains=filtro) |
            Q(codigo__icontains=filtro)
        )
    
    paginator = Paginator(empresas, 10)
    page = request.GET.get('page')
    empresas_paginadas = paginator.get_page(page)
    
    return render(request, 'empresas/lista.html', {
        'empresas': empresas_paginadas,
        'filtro': filtro
    })

@login_required
@user_passes_test(lambda u: not u.is_tecnico)
def detalhe_empresa(request, slug):
    empresa = get_object_or_404(Empresa, slug=slug)
    contratos = empresa.contratos.all()
    
    if request.method == 'POST':
        form_contrato = ContratoEmpresaForm(request.POST, request.FILES)
        if form_contrato.is_valid():
            contrato = form_contrato.save(commit=False)
            contrato.empresa = empresa
            contrato.save()
            messages.success(request, 'Contrato adicionado com sucesso!')
            return redirect('detalhe_empresa', slug=empresa.slug)
    else:
        form_contrato = ContratoEmpresaForm()
    
    return render(request, 'empresas/detalhes.html', {
        'empresa': empresa,
        'contratos': contratos,
        'form_contrato': form_contrato
    })

@login_required
@user_passes_test(lambda u: not u.is_tecnico)
def editar_empresa(request, slug):
    empresa = get_object_or_404(Empresa, slug=slug)
    
    if request.method == 'POST':
        form = EmpresaForm(request.POST, request.FILES, instance=empresa)
        if form.is_valid():
            empresa = form.save()
            messages.success(request, 'Empresa atualizada com sucesso!')
            return redirect('detalhe_empresa', slug=empresa.slug)
        else:
            messages.error(request, 'Por favor, corrija os erros abaixo.')
    else:
        form = EmpresaForm(instance=empresa)
    
    return render(request, 'empresas/form.html', {
        'form': form,
        'empresa': empresa,
        'titulo': 'Editar Empresa'
    })

@login_required
@user_passes_test(lambda u: not u.is_tecnico)
def excluir_empresa(request, slug):
    empresa = get_object_or_404(Empresa, slug=slug)
    
    if request.method == 'POST':
        empresa.delete()
        messages.success(request, 'Empresa excluída com sucesso!')
        return redirect('listar_empresas')
    
    return render(request, 'empresas/confirmar_exclusao.html', {
        'empresa': empresa
    })

@login_required
@user_passes_test(lambda u: not u.is_tecnico)
def excluir_contrato_empresa(request, pk):
    contrato = get_object_or_404(ContratoEmpresa, pk=pk)
    empresa = contrato.empresa
    
    if request.method == 'POST':
        contrato.delete()
        messages.success(request, 'Contrato excluído com sucesso!')
        return redirect('detalhe_empresa', slug=empresa.slug)
    
    return render(request, 'empresas/confirmar_exclusao_contrato.html', {
        'contrato': contrato,
        'empresa': empresa
    })

@login_required
def buscar_empresas(request):
    termo = request.GET.get('termo', '')
    empresas = []
    
    if termo:
        empresas = Empresa.objects.filter(
            Q(razao_social__icontains=termo) |
            Q(nome_fantasia__icontains=termo) |
            Q(cnpj__icontains=termo)
        )[:10]
    
    data = [{
        'id': empresa.id,
        'razao_social': empresa.razao_social,
        'nome_fantasia': empresa.nome_fantasia,
        'cnpj': empresa.cnpj,
        'codigo': empresa.codigo
    } for empresa in empresas]
    
    return JsonResponse(data, safe=False)
