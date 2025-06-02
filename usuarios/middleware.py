from django.shortcuts import redirect
from django.urls import resolve, reverse
from django.contrib import messages
from django.conf import settings

from .models import Perfil, Menu, PermissaoMenu

class PermissaoMiddleware:
    """
    Middleware para verificar as permissões de acesso dos usuários
    com base em seus perfis e redirecioná-los se não tiverem acesso.
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
        
    def __call__(self, request):
        # Se o usuário não estiver autenticado, permita o acesso (o sistema de login cuidará disso)
        if not request.user.is_authenticated:
            return self.get_response(request)
            
        # Verificar se é uma requisição AJAX
        is_ajax_request = request.headers.get('X-Requested-With') == 'XMLHttpRequest'
        
        # Lista de caminhos que sempre são permitidos
        always_allowed = [
            reverse('login'),
            reverse('logout'),
            reverse('sair'),
            settings.STATIC_URL,
            settings.MEDIA_URL
        ]
        
        # Verifica se o caminho atual está na lista de caminhos sempre permitidos
        for path in always_allowed:
            if request.path.startswith(path):
                return self.get_response(request)
                
        # Ignora requisições AJAX, CSS, JS, imagens, etc.
        if is_ajax_request:
            return self.get_response(request)
            
        # Superuser tem acesso total
        if request.user.is_superuser:
            return self.get_response(request)
                
        # Tenta resolver a URL atual para obter o nome da view
        try:
            resolver_match = resolve(request.path)
            view_name = resolver_match.view_name
        except:
            # Se não conseguir resolver, permite o acesso
            return self.get_response(request)
                
        # Verifica se o usuário tem um perfil
        try:
            perfil = request.user.perfil
        except Perfil.DoesNotExist:
            # Se não tiver perfil, cria um padrão como técnico
            perfil = Perfil.objects.create(
                user=request.user,
                tipo='tecnico'
            )
                
        # Se o perfil for de técnico, verificar se existe um registro na tabela Tecnico
        if perfil.tipo == 'tecnico':
            # Importar aqui para evitar importação circular
            from tecnicos.models import Tecnico

            try:
                # Verificar se o usuário tem um registro na tabela Tecnico
                tecnico = Tecnico.objects.get(usuario=request.user)
            except Tecnico.DoesNotExist:
                # Sinal deve criar o técnico, mas vamos verificar novamente
                print(f"Middleware: Usuário {request.user.username} tem perfil de técnico, mas não tem registro na tabela Tecnico")
                # Tentar criar um técnico para o usuário
                from usuarios.models import criar_tecnico_se_necessario
                # Chamar a função para criar o técnico
                criar_tecnico_se_necessario(sender=Perfil, instance=perfil, created=False)
                
        # Verifica qual menu corresponde à URL atual
        try:
            menu = Menu.objects.filter(url=view_name).first()
            if not menu:
                # Tenta alternativa: verificar se a URL contém o namespace
                menus = Menu.objects.all()
                for m in menus:
                    if ':' in m.url and m.url.split(':')[0] in view_name:
                        menu = m
                        break
        except:
            # Se ocorrer algum erro ao buscar o menu, permite o acesso
            return self.get_response(request)
                
        # Se não encontrou um menu correspondente, permite o acesso
        if not menu:
            return self.get_response(request)
        
        # Permitir acesso ao módulo de produtos para todos os perfis exceto técnicos
        if menu.codigo == 'produtos' and perfil.tipo != 'tecnico':
            return self.get_response(request)
                
        # Administrador tem acesso total
        if perfil.tipo == 'administrador':
            return self.get_response(request)
                
        # Gerente não tem acesso a Gestão de Usuários e Administração
        if perfil.tipo == 'gerente':
            if menu.nome in ['Gestão de Usuários', 'Administração']:
                messages.error(request, 'Você não tem permissão para acessar esta área.')
                return redirect('dashboard')
            return self.get_response(request)
                
        # Técnico só tem acesso a Ordens de Serviço
        if perfil.tipo == 'tecnico':
            if menu.nome != 'Ordens de Serviço':
                messages.error(request, 'Você não tem permissão para acessar esta área.')
                return redirect('dashboard')
                
            # Verificar se é uma rota específica para listar ou detalhar ordens
            # que não precisa de verificação adicional (pois a view já faz a verificação)
            ordens_route_names = ['listar_ordens', 'detalhe_ordem', 'editar_ordem', 
                                'adicionar_peca_os', 'novo_comentario', 'imprimir_ordem']
            if view_name in ordens_route_names:
                return self.get_response(request)
                
            # Outras rotas de ordens, sem verificação específica, permitir acesso
            # (as views farão a verificação específica)
            if 'ordens' in view_name:
                return self.get_response(request)
                
            # Se chegou aqui, não é uma rota de ordens permitida
            messages.error(request, 'Você não tem permissão para acessar esta área.')
            return redirect('listar_ordens')
                
        # Atendente não tem acesso a Gestão de Usuários e Administração
        if perfil.tipo == 'atendente':
            if menu.nome in ['Gestão de Usuários', 'Administração']:
                messages.error(request, 'Você não tem permissão para acessar esta área.')
                return redirect('dashboard')
            return self.get_response(request)
                
        # Para perfil personalizado, verifica as permissões específicas
        if perfil.tipo == 'personalizado':
            try:
                permissao = PermissaoMenu.objects.get(perfil=perfil, menu=menu)
                
                # Sem acesso
                if permissao.nivel_acesso == 'nenhum':
                    messages.error(request, 'Você não tem permissão para acessar esta área.')
                    return redirect('dashboard')
                    
                # Para outras permissões, verificar as ações específicas
                metodo = request.method.lower()
                
                # GET (visualizar) - todos os níveis permitem
                if metodo == 'get':
                    return self.get_response(request)
                    
                # POST (criar/alterar/excluir)
                if metodo == 'post':
                    if 'delete' in request.POST and permissao.nivel_acesso != 'excluir':
                        messages.error(request, 'Você não tem permissão para excluir registros.')
                        return redirect(request.path)
                        
                    if permissao.nivel_acesso == 'visualizar':
                        messages.error(request, 'Você tem permissão apenas para visualizar.')
                        return redirect(request.path)
                        
                return self.get_response(request)
                
            except PermissaoMenu.DoesNotExist:
                # Se não tiver permissão definida, não permite o acesso
                messages.error(request, 'Você não tem permissão para acessar esta área.')
                return redirect('dashboard')
                
        # Se passou por todas as verificações, permite o acesso
        return self.get_response(request) 