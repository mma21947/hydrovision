from django.contrib.auth.models import User
from usuarios.models import Perfil, Menu, GrupoPermissao, Permissao
from clientes.models import Empresa, Cliente
from tecnicos.models import Tecnico
from django.utils import timezone
import datetime

def criar_dados_iniciais():
    # Criar empresa exemplo
    empresa = Empresa.objects.create(
        nome='CyberOS Tecnologia',
        nome_fantasia='CyberOS',
        cnpj='12.345.678/0001-90',
        inscricao_estadual='123456789',
        endereco='Rua da Tecnologia',
        numero='1000',
        bairro='Centro',
        cidade='São Paulo',
        estado='SP',
        cep='01234-567',
        telefone='(11) 1234-5678',
        email='contato@cyberos.com.br',
        site='www.cyberos.com.br'
    )
    print('Empresa criada com sucesso!')

    # Criar cliente exemplo
    cliente = Cliente.objects.create(
        tipo='PJ',
        nome='Empresa Cliente Exemplo',
        cpf_cnpj='98.765.432/0001-10',
        rg_ie='987654321',
        email='cliente@exemplo.com.br',
        telefone='(11) 9876-5432',
        celular='(11) 98765-4321',
        endereco='Avenida Cliente',
        numero='500',
        bairro='Vila Exemplo',
        cidade='São Paulo',
        estado='SP',
        cep='04321-876',
        empresa=empresa
    )
    print('Cliente criado com sucesso!')

    # Criar técnico exemplo
    user_tecnico = User.objects.create_user(
        username='tecnico',
        password='tecnico123',
        first_name='João',
        last_name='Silva',
        email='tecnico@cyberos.com.br'
    )
    
    perfil_tecnico = Perfil.objects.create(
        user=user_tecnico,
        tipo='tecnico',
        telefone='(11) 97777-8888'
    )
    
    tecnico = Tecnico.objects.create(
        usuario=user_tecnico,
        codigo='TEC001',
        nome_completo='João Silva',
        cpf='123.456.789-00',
        data_nascimento=datetime.date(1990, 1, 1),
        celular='(11) 97777-8888',
        email='tecnico@cyberos.com.br',
        endereco='Rua dos Técnicos',
        numero='100',
        bairro='Vila Técnica',
        cidade='São Paulo',
        estado='SP',
        cep='04567-890',
        data_admissao=timezone.now().date(),
        nivel='senior'
    )
    print('Técnico criado com sucesso!')

    # Criar menus básicos
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
    
    # Limpar menus existentes
    Menu.objects.all().delete()
    
    # Criar novos menus
    for menu_data in menus:
        menu = Menu.objects.create(**menu_data)
        print(f'Menu {menu.nome} criado com sucesso!')

    # Criar grupo de permissão básico
    grupo_admin = GrupoPermissao.objects.create(
        nome='Administradores',
        descricao='Grupo com todas as permissões do sistema'
    )
    print('Grupo de permissão criado com sucesso!')

    # Criar permissões para cada menu
    for menu in Menu.objects.all():
        Permissao.objects.create(
            menu=menu,
            grupo=grupo_admin,
            acoes={
                'visualizar': True,
                'criar': True,
                'editar': True,
                'excluir': True
            }
        )
    print('Permissões criadas com sucesso!')

if __name__ == '__main__':
    criar_dados_iniciais() 