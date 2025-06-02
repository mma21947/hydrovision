from django.contrib.auth.models import User
from usuarios.models import Perfil

# Criar ou atualizar superusuário
try:
    admin = User.objects.get(username='admin')
    admin.set_password('admin')
    admin.email = 'admin@admin.com'
    admin.is_superuser = True
    admin.is_staff = True
    admin.save()
except User.DoesNotExist:
    admin = User.objects.create_superuser('admin', 'admin@admin.com', 'admin')

# Criar ou atualizar perfil de administrador
try:
    perfil = Perfil.objects.get(user=admin)
    perfil.tipo = 'administrador'
    perfil.save()
except Perfil.DoesNotExist:
    Perfil.objects.create(user=admin, tipo='administrador')

print('Superusuário admin criado/atualizado com sucesso!') 