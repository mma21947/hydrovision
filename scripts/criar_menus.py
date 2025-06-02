from usuarios.models import Menu, GrupoPermissao, Permissao, PermissaoMenu, Perfil
from django.contrib.auth.models import User

def criar_menus_e_permissoes():
    # Limpar dados existentes
    Menu.objects.all().delete()
    GrupoPermissao.objects.all().delete()
    Permissao.objects.all().delete()
    PermissaoMenu.objects.all().delete()

    # Criar menus
    menus = [
        {
            'nome': 'Dashboard',
            'descricao': 'Página inicial do sistema',
            'url': '/',
            'icone': 'fas fa-tachometer-alt',
            'ordem': 1,
            'ativo': True
        },
        {
            'nome': 'Clientes',
            'descricao': 'Gestão de clientes',
            'url': '/clientes/',
            'icone': 'fas fa-users',
            'ordem': 2,
            'ativo': True
        },
        {
            'nome': 'Ordens de Serviço',
            'descricao': 'Gestão de ordens de serviço',
            'url': '/ordens/',
            'icone': 'fas fa-clipboard-list',
            'ordem': 3,
            'ativo': True
        },
        {
            'nome': 'Técnicos',
            'descricao': 'Gestão de técnicos',
            'url': '/tecnicos/',
            'icone': 'fas fa-user-cog',
            'ordem': 4,
            'ativo': True
        },
        {
            'nome': 'Produtos',
            'descricao': 'Gestão de produtos',
            'url': '/produtos/',
            'icone': 'fas fa-box',
            'ordem': 5,
            'ativo': True
        },
        {
            'nome': 'Relatórios',
            'descricao': 'Relatórios do sistema',
            'url': '/relatorios/',
            'icone': 'fas fa-chart-bar',
            'ordem': 6,
            'ativo': True
        },
        {
            'nome': 'Usuários',
            'descricao': 'Gestão de usuários',
            'url': '/usuarios/',
            'icone': 'fas fa-users-cog',
            'ordem': 7,
            'ativo': True
        },
        {
            'nome': 'Configurações',
            'descricao': 'Configurações do sistema',
            'url': '/configuracoes/',
            'icone': 'fas fa-cog',
            'ordem': 8,
            'ativo': True
        }
    ]

    created_menus = []
    for menu_data in menus:
        menu = Menu.objects.create(**menu_data)
        created_menus.append(menu)
        print(f'Menu {menu.nome} criado com sucesso!')

    # Criar grupo de administradores
    grupo_admin = GrupoPermissao.objects.create(
        nome='Administradores',
        descricao='Grupo com todas as permissões do sistema'
    )
    print('Grupo Administradores criado com sucesso!')

    # Criar permissões para o grupo
    for menu in created_menus:
        permissao = Permissao.objects.create(
            menu=menu,
            grupo=grupo_admin,
            acoes={
                'visualizar': True,
                'criar': True,
                'editar': True,
                'excluir': True
            }
        )
        print(f'Permissões criadas para o menu {menu.nome}')

    # Adicionar permissões ao perfil do admin
    try:
        admin_user = User.objects.get(username='admin')
        admin_perfil = Perfil.objects.get(user=admin_user)
        admin_perfil.grupos_permissao.add(grupo_admin)
        
        # Criar PermissaoMenu para cada menu
        for menu in created_menus:
            PermissaoMenu.objects.create(
                perfil=admin_perfil,
                menu=menu,
                nivel_acesso='total'
            )
        print('Permissões adicionadas ao perfil do admin')
    except (User.DoesNotExist, Perfil.DoesNotExist):
        print('Usuário admin ou perfil não encontrado')

if __name__ == '__main__':
    criar_menus_e_permissoes() 