import os
import sys
import django

# Configurar o ambiente Django
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'cyberOS.settings')
django.setup()

from usuarios.models import Perfil, Menu, Permissao
from usuarios.views import cadastrar_menus_padrao

def configurar_permissoes():
    """Configura as permissões padrão do sistema."""
    
    # Cadastrar menus padrão
    cadastrar_menus_padrao()
    
    # Criar perfil de administrador se não existir
    perfil_admin, created = Perfil.objects.get_or_create(
        nome='Administrador',
        defaults={
            'descricao': 'Perfil com acesso total ao sistema'
        }
    )

    # Dar todas as permissões ao perfil de administrador
    menus = Menu.objects.filter(ativo=True)
    for menu in menus:
        Permissao.objects.get_or_create(
            perfil=perfil_admin,
            menu=menu,
            defaults={
                'visualizar': True,
                'cadastrar': True,
                'editar': True,
                'excluir': True
            }
        )

    print('Permissões configuradas com sucesso!')

if __name__ == '__main__':
    configurar_permissoes() 