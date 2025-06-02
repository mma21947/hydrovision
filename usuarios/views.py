from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.urls import reverse_lazy
from django.db import transaction
from django.forms import inlineformset_factory
from django.db.models import Q

from .models import Perfil, Menu, GrupoPermissao, Permissao
from .forms import (
    UsuarioForm, PerfilForm, UsuarioEditForm, PermissaoMenuFormSet,
    GrupoPermissaoForm, PermissaoForm, PerfilPermissoesForm, PermissaoFormSet,
    AlterarSenhaForm
)

def is_admin(user):
    """Verifica se o usuário é um administrador."""
    if not user.is_authenticated:
        return False
    return user.is_superuser or user.perfil.tem_permissao(Menu.objects.get(nome='Gestão de Usuários'), 'visualizar')

@login_required
@user_passes_test(is_admin)
def listar_usuarios(request):
    """Lista todos os usuários do sistema."""
    # Podemos usar select_related novamente, já que os campos problemáticos agora são propriedades
    usuarios = User.objects.select_related('perfil').all().order_by('username')
    return render(request, 'usuarios/listar_usuarios.html', {'usuarios': usuarios})

@login_required
@user_passes_test(is_admin)
def criar_usuario(request):
    """Cria um novo usuário com perfil."""
    if request.method == 'POST':
        form_usuario = UsuarioForm(request.POST)
        form_perfil = PerfilForm(request.POST)
        
        if form_usuario.is_valid() and form_perfil.is_valid():
            with transaction.atomic():
                usuario = form_usuario.save()
                perfil = form_perfil.save(commit=False)
                perfil.user = usuario
                perfil.save()
                
                # Salva os grupos de permissão selecionados
                form_perfil.save_m2m()
                
                # Se for perfil personalizado, redirecionar para configurar permissões
                if perfil.tipo == 'personalizado':
                    return redirect('usuarios:configurar_permissoes', perfil_id=perfil.id)
                
                # Se não for personalizado, configurar permissões conforme o tipo
                configurar_permissoes_padrao(perfil)
                
                messages.success(request, 'Usuário criado com sucesso.')
                return redirect('usuarios:listar_usuarios')
    else:
        form_usuario = UsuarioForm()
        form_perfil = PerfilForm()
    
    return render(request, 'usuarios/criar_usuario.html', {
        'form_usuario': form_usuario,
        'form_perfil': form_perfil
    })

@login_required
@user_passes_test(is_admin)
def editar_usuario(request, usuario_id):
    """Edita um usuário existente."""
    usuario = get_object_or_404(User, id=usuario_id)
    try:
        perfil = usuario.perfil
    except Perfil.DoesNotExist:
        perfil = Perfil.objects.create(user=usuario, tipo='tecnico')
    
    if request.method == 'POST':
        form_usuario = UsuarioEditForm(request.POST, instance=usuario)
        form_perfil = PerfilForm(request.POST, instance=perfil)
        
        if form_usuario.is_valid() and form_perfil.is_valid():
            with transaction.atomic():
                form_usuario.save()
                perfil_anterior = perfil.tipo
                perfil = form_perfil.save()
                
                # Se mudou para perfil personalizado ou já era personalizado
                if perfil.tipo == 'personalizado':
                    return redirect('usuarios:configurar_permissoes', perfil_id=perfil.id)
                
                # Se mudou de perfil, reconfigurar permissões
                if perfil_anterior != perfil.tipo:
                    configurar_permissoes_padrao(perfil)
                
                messages.success(request, 'Usuário atualizado com sucesso.')
                return redirect('usuarios:listar_usuarios')
    else:
        form_usuario = UsuarioEditForm(instance=usuario)
        form_perfil = PerfilForm(instance=perfil)
    
    return render(request, 'usuarios/editar_usuario.html', {
        'form_usuario': form_usuario,
        'form_perfil': form_perfil,
        'usuario': usuario
    })

@login_required
@user_passes_test(is_admin)
def configurar_permissoes(request, perfil_id):
    """Configura permissões personalizadas para um perfil."""
    perfil = get_object_or_404(Perfil, id=perfil_id)
    
    # Verifica se existem os menus no banco de dados. Se não, cadastra os padrões
    if Menu.objects.count() == 0:
        cadastrar_menus_padrao()
    
    if request.method == 'POST':
        formset = PermissaoMenuFormSet(request.POST, queryset=PermissaoMenu.objects.filter(perfil=perfil), perfil=perfil)
        
        if formset.is_valid():
            # Precisamos salvar o nivel_acesso antes de salvar as instâncias
            permissoes = formset.save(commit=False)
            for form, permissao in zip(formset.forms, permissoes):
                # Pegamos o valor do campo tipo_permissao do formulário e o atribuímos ao campo nivel_acesso
                permissao.nivel_acesso = form.cleaned_data.get('tipo_permissao', 'nenhum')
                permissao.save()
            
            messages.success(request, 'Permissões configuradas com sucesso.')
            return redirect('usuarios:listar_usuarios')
    else:
        formset = PermissaoMenuFormSet(queryset=PermissaoMenu.objects.filter(perfil=perfil), perfil=perfil)
        
        # Inicializa o campo tipo_permissao do formulário com o valor de nivel_acesso da instância
        for form in formset.forms:
            if form.instance and form.instance.pk:
                form.initial['tipo_permissao'] = form.instance.nivel_acesso
    
    return render(request, 'usuarios/configurar_permissoes.html', {
        'formset': formset,
        'perfil': perfil
    })

@login_required
@user_passes_test(is_admin)
def excluir_usuario(request, usuario_id):
    """Exclui um usuário."""
    usuario = get_object_or_404(User, id=usuario_id)
    
    if request.method == 'POST':
        usuario.delete()
        messages.success(request, 'Usuário excluído com sucesso.')
        return redirect('usuarios:listar_usuarios')
    
    return render(request, 'usuarios/confirmar_exclusao.html', {'usuario': usuario})

def configurar_permissoes_padrao(perfil):
    """Configura as permissões padrão baseadas no tipo de perfil."""
    # Verificar se os menus existem. Se não, cadastrar os padrões.
    if Menu.objects.count() == 0:
        cadastrar_menus_padrao()
    
    # Limpar permissões existentes
    Permissao.objects.filter(perfil=perfil).delete()
    
    # Obter todos os menus
    menus = Menu.objects.all()
    
    # Definir o nível de acesso com base no tipo de perfil
    for menu in menus:
        acoes = {
            'visualizar': False,
            'criar': False,
            'editar': False,
            'excluir': False,
            'alterar_senha': False
        }
        
        # Definir nível de acesso conforme o tipo de perfil
        if perfil.tipo == 'administrador':
            acoes = {
                'visualizar': True,
                'criar': True,
                'editar': True,
                'excluir': True,
                'alterar_senha': True
            }
        elif perfil.tipo in ['gerente', 'atendente']:
            # Conceder acesso total a todos os menus, exceto administração e usuários
            if menu.codigo not in ['admin', 'usuarios']:
                acoes = {
                    'visualizar': True,
                    'criar': True,
                    'editar': True,
                    'excluir': True,
                    'alterar_senha': False
                }
            # Permitir alterar senha apenas no menu de usuários
            elif menu.codigo == 'usuarios':
                acoes['visualizar'] = True
                acoes['alterar_senha'] = True
        elif perfil.tipo == 'tecnico':
            # Conceder acesso limitado às ordens de serviço e dashboard
            if menu.codigo in ['ordens', 'dashboard']:
                acoes = {
                    'visualizar': True,
                    'criar': False,
                    'editar': False,
                    'excluir': False,
                    'alterar_senha': False
                }
            # Permitir alterar senha apenas no menu de usuários
            elif menu.codigo == 'usuarios':
                acoes['visualizar'] = True
                acoes['alterar_senha'] = True
        
        # Garantir que o menu de produtos seja visível para todos exceto técnicos
        if menu.codigo == 'produtos' and perfil.tipo != 'tecnico':
            acoes['visualizar'] = True
        
        # Criar a permissão para o menu
        Permissao.objects.create(
            perfil=perfil,
            menu=menu,
            acoes=acoes
        )
    
    # Aplicar permissões dos grupos selecionados
    for grupo in perfil.grupos_permissao.all():
        for permissao_grupo in grupo.permissoes.all():
            # Buscar ou criar a permissão do perfil para este menu
            permissao_perfil, criada = Permissao.objects.get_or_create(
                perfil=perfil,
                menu=permissao_grupo.menu,
                defaults={'acoes': permissao_grupo.acoes}
            )
            
            if not criada:
                # Se a permissão já existia, atualizar as ações combinando com as do grupo
                acoes_atualizadas = permissao_perfil.acoes.copy()
                for acao, valor in permissao_grupo.acoes.items():
                    if valor:  # Se o grupo tem permissão, conceder ao perfil
                        acoes_atualizadas[acao] = True
                permissao_perfil.acoes = acoes_atualizadas
                permissao_perfil.save()

def cadastrar_menus_padrao():
    """Cadastra os menus padrão do sistema."""
    menus_data = [
        {
            'nome': 'Dashboard',
            'descricao': 'Página inicial do sistema',
            'url': '/',
            'icone': 'fas fa-tachometer-alt',
            'ordem': 1,
            'ativo': True,
            'codigo': 'dashboard'
        },
        {
            'nome': 'Clientes',
            'descricao': 'Gestão de clientes',
            'url': '/clientes/',
            'icone': 'fas fa-users',
            'ordem': 2,
            'ativo': True,
            'codigo': 'clientes'
        },
        {
            'nome': 'Ordens de Serviço',
            'descricao': 'Gestão de ordens de serviço',
            'url': '/ordens/',
            'icone': 'fas fa-clipboard-list',
            'ordem': 3,
            'ativo': True,
            'codigo': 'ordens'
        },
        {
            'nome': 'Técnicos',
            'descricao': 'Gestão de técnicos',
            'url': '/tecnicos/',
            'icone': 'fas fa-user-cog',
            'ordem': 4,
            'ativo': True,
            'codigo': 'tecnicos'
        },
        {
            'nome': 'Produtos',
            'descricao': 'Gestão de produtos',
            'url': '/produtos/',
            'icone': 'fas fa-box',
            'ordem': 5,
            'ativo': True,
            'codigo': 'produtos'
        },
        {
            'nome': 'Relatórios',
            'descricao': 'Relatórios do sistema',
            'url': '/relatorios/',
            'icone': 'fas fa-chart-bar',
            'ordem': 6,
            'ativo': True,
            'codigo': 'relatorios'
        },
        {
            'nome': 'Usuários',
            'descricao': 'Gestão de usuários',
            'url': '/usuarios/',
            'icone': 'fas fa-users-cog',
            'ordem': 7,
            'ativo': True,
            'codigo': 'usuarios'
        },
        {
            'nome': 'Configurações',
            'descricao': 'Configurações do sistema',
            'url': '/configuracoes/',
            'icone': 'fas fa-cog',
            'ordem': 8,
            'ativo': True,
            'codigo': 'configuracoes'
        }
    ]

    # Criar menus que não existem
    for menu_data in menus_data:
        Menu.objects.get_or_create(
            codigo=menu_data['codigo'],
            defaults=menu_data
        )

@login_required
@user_passes_test(is_admin)
def listar_grupos_permissao(request):
    grupos = GrupoPermissao.objects.all().order_by('nome')
    return render(request, 'usuarios/grupos_permissao/listar.html', {
        'grupos': grupos
    })

@login_required
@user_passes_test(is_admin)
def criar_grupo_permissao(request):
    if request.method == 'POST':
        form = GrupoPermissaoForm(request.POST)
        if form.is_valid():
            grupo = form.save()
            messages.success(request, 'Grupo de permissões criado com sucesso.')
            return redirect('usuarios:configurar_grupo_permissao', grupo_id=grupo.id)
    else:
        form = GrupoPermissaoForm()
    
    return render(request, 'usuarios/grupos_permissao/form.html', {
        'form': form,
        'titulo': 'Novo Grupo de Permissões'
    })

@login_required
@user_passes_test(is_admin)
def editar_grupo_permissao(request, grupo_id):
    grupo = get_object_or_404(GrupoPermissao, id=grupo_id)
    
    if request.method == 'POST':
        form = GrupoPermissaoForm(request.POST, instance=grupo)
        if form.is_valid():
            form.save()
            messages.success(request, 'Grupo de permissões atualizado com sucesso.')
            return redirect('usuarios:listar_grupos_permissao')
    else:
        form = GrupoPermissaoForm(instance=grupo)
    
    return render(request, 'usuarios/grupos_permissao/form.html', {
        'form': form,
        'titulo': 'Editar Grupo de Permissões',
        'grupo': grupo
    })

@login_required
@user_passes_test(is_admin)
def configurar_grupo_permissao(request, grupo_id):
    grupo = get_object_or_404(GrupoPermissao, id=grupo_id)
    
    # Verifica se existem os menus no banco de dados. Se não, cadastra os padrões
    if Menu.objects.count() == 0:
        cadastrar_menus_padrao()
    
    # Obter todos os menus ativos
    menus = Menu.objects.filter(ativo=True)
    
    if request.method == 'POST':
        formset = PermissaoFormSet(request.POST, queryset=Permissao.objects.filter(grupo=grupo))
        if formset.is_valid():
            # Salvamos ou atualizamos as permissões existentes
            instances = formset.save(commit=False)
            
            # Lista para controlar quais menus foram processados
            menus_processados = []
            
            for instance in instances:
                if instance.menu_id:
                    menus_processados.append(instance.menu_id)
                    # Verifica se já existe uma permissão para este menu e grupo
                    permissao_existente = Permissao.objects.filter(
                        menu=instance.menu,
                        grupo=grupo
                    ).first()
                    
                    if permissao_existente:
                        # Atualiza a permissão existente
                        permissao_existente.acoes = instance.acoes
                        permissao_existente.save()
                    else:
                        # Cria uma nova permissão
                        instance.grupo = grupo
                        instance.save()
            
            # Remove permissões que não estão mais no formset
            Permissao.objects.filter(grupo=grupo).exclude(menu_id__in=menus_processados).delete()
            
            messages.success(request, 'Permissões configuradas com sucesso.')
            return redirect('usuarios:listar_grupos_permissao')
    else:
        # Criar permissões para menus que ainda não têm
        for menu in menus:
            Permissao.objects.get_or_create(
                menu=menu,
                grupo=grupo,
                defaults={
                    'acoes': {
                        'visualizar': False,
                        'criar': False,
                        'editar': False,
                        'excluir': False
                    }
                }
            )
        
        formset = PermissaoFormSet(queryset=Permissao.objects.filter(grupo=grupo))
    
    return render(request, 'usuarios/grupos_permissao/configurar_permissoes.html', {
        'formset': formset,
        'grupo': grupo
    })

@login_required
@user_passes_test(is_admin)
def excluir_grupo_permissao(request, grupo_id):
    grupo = get_object_or_404(GrupoPermissao, id=grupo_id)
    
    if request.method == 'POST':
        grupo.delete()
        messages.success(request, 'Grupo de permissões excluído com sucesso.')
        return redirect('usuarios:listar_grupos_permissao')
    
    return render(request, 'usuarios/grupos_permissao/confirmar_exclusao.html', {
        'grupo': grupo
    })

@login_required
@user_passes_test(is_admin)
def configurar_permissoes_usuario(request, usuario_id):
    usuario = get_object_or_404(User, id=usuario_id)
    perfil = usuario.perfil
    
    if request.method == 'POST':
        form = PerfilPermissoesForm(request.POST, instance=perfil)
        formset = PermissaoFormSet(
            request.POST,
            queryset=perfil.permissoes_customizadas.all(),
            prefix='permissoes'
        )
        
        if form.is_valid() and formset.is_valid():
            form.save()
            instances = formset.save(commit=False)
            
            for instance in instances:
                instance.save()
                perfil.permissoes_customizadas.add(instance)
            
            # Remove permissões excluídas
            for obj in formset.deleted_objects:
                perfil.permissoes_customizadas.remove(obj)
                obj.delete()
            
            messages.success(request, 'Permissões do usuário configuradas com sucesso.')
            return redirect('usuarios:listar_usuarios')
    else:
        form = PerfilPermissoesForm(instance=perfil)
        formset = PermissaoFormSet(
            queryset=perfil.permissoes_customizadas.all(),
            prefix='permissoes'
        )
    
    return render(request, 'usuarios/configurar_permissoes_usuario.html', {
        'form': form,
        'formset': formset,
        'usuario': usuario
    })

@login_required
def alterar_senha(request, usuario_id):
    """Altera a senha de um usuário."""
    usuario = get_object_or_404(User, id=usuario_id)
    
    # Verifica se o usuário tem permissão para alterar a senha
    if not request.user.is_superuser and not request.user.perfil.tem_permissao(Menu.objects.get(codigo='usuarios'), 'alterar_senha'):
        messages.error(request, 'Você não tem permissão para alterar senhas.')
        return redirect('usuarios:listar_usuarios')
    
    if request.method == 'POST':
        form = AlterarSenhaForm(request.POST)
        if form.is_valid():
            nova_senha = form.cleaned_data['nova_senha']
            usuario.set_password(nova_senha)
            usuario.save()
            
            messages.success(request, 'Senha alterada com sucesso.')
            return redirect('usuarios:listar_usuarios')
    else:
        form = AlterarSenhaForm()
    
    return render(request, 'usuarios/alterar_senha.html', {
        'form': form,
        'usuario': usuario
    })

def editar_ordem(request, slug):
    ordem = get_object_or_404(OrdemServico, slug=slug)
    
    if request.method == 'POST':
        form = OrdemServicoForm(request.POST, instance=ordem)
        
        # Adicionar os campos do management form se estiverem faltando
        post_data = request.POST.copy()
        if 'produtos-TOTAL_FORMS' not in post_data:
            post_data['produtos-TOTAL_FORMS'] = '0'
            post_data['produtos-INITIAL_FORMS'] = '0'
            post_data['produtos-MIN_NUM_FORMS'] = '0'
            post_data['produtos-MAX_NUM_FORMS'] = '1000'
        
        formset = ProdutoUtilizadoFormSet(post_data, request.FILES, instance=ordem, prefix='produtos')
        
        # Restante do código...
