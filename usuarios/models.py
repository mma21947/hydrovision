from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils.text import slugify
import datetime

class Perfil(models.Model):
    TIPO_PERFIL_CHOICES = [
        ('administrador', 'Administrador'),
        ('gerente', 'Gerente'),
        ('tecnico', 'Técnico'),
        ('atendente', 'Atendente'),
        ('cliente', 'Cliente'),
        ('personalizado', 'Personalizado'),
    ]
    
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='perfil')
    tipo = models.CharField(max_length=20, choices=TIPO_PERFIL_CHOICES, default='tecnico')
    telefone = models.CharField(max_length=20, blank=True, null=True)
    cargo = models.CharField(max_length=100, blank=True, null=True)
    foto = models.ImageField(upload_to='usuarios/fotos/', blank=True, null=True)
    bio = models.TextField(blank=True, null=True)
    ultimo_acesso = models.DateTimeField(blank=True, null=True)
    grupos_permissao = models.ManyToManyField('GrupoPermissao', blank=True)
    permissoes_customizadas = models.ManyToManyField('Permissao', blank=True, related_name='perfis_customizados')
    data_criacao = models.DateTimeField(auto_now_add=True)
    ultima_atualizacao = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.user.username} - {self.get_tipo_display()}"
    
    class Meta:
        verbose_name = "Perfil"
        verbose_name_plural = "Perfis"

    def tem_permissao(self, menu, acao):
        # Verifica permissões customizadas primeiro
        for permissao in self.permissoes_customizadas.filter(menu=menu):
            if permissao.acoes.get(acao, False):
                return True

        # Verifica permissões dos grupos
        for grupo in self.grupos_permissao.all():
            try:
                permissao = Permissao.objects.get(menu=menu, grupo=grupo)
                if permissao.acoes.get(acao, False):
                    return True
            except Permissao.DoesNotExist:
                continue

        return False

# Sinal para criar um técnico automaticamente quando um usuário recebe perfil de técnico
@receiver(post_save, sender=Perfil)
def criar_tecnico_se_necessario(sender, instance, created, **kwargs):
    """
    Cria um técnico automaticamente se um usuário recebe o perfil de técnico
    e ainda não tem um registro na tabela Tecnico.
    """
    # Verificar se o perfil é do tipo técnico
    if instance.tipo == 'tecnico':
        # Importar aqui para evitar importação circular
        from tecnicos.models import Tecnico
        
        # Verificar se já existe um técnico para este usuário
        try:
            Tecnico.objects.get(usuario=instance.user)
            # Já existe, não precisamos criar
        except Tecnico.DoesNotExist:
            # Não existe, vamos criar um técnico básico
            try:
                # Gerar um código para o técnico (TEC + ID do usuário)
                codigo = f"TEC{instance.user.id:04d}"
                
                # Obter dados básicos do usuário
                nome_completo = f"{instance.user.first_name} {instance.user.last_name}".strip()
                if not nome_completo:
                    nome_completo = instance.user.username
                    
                # Criar técnico com dados básicos
                tecnico = Tecnico(
                    usuario=instance.user,
                    codigo=codigo,
                    nome_completo=nome_completo,
                    cpf="000.000.000-00",  # CPF temporário
                    data_nascimento=datetime.date.today(),  # Data temporária
                    celular="(00) 00000-0000",  # Celular temporário
                    email=instance.user.email,
                    endereco="Endereço não informado",
                    numero="S/N",
                    bairro="Bairro não informado",
                    cidade="Cidade não informada",
                    estado="SP",
                    cep="00000-000",
                    data_admissao=datetime.date.today(),
                    nivel="junior"
                )
                tecnico.save()
                print(f"Técnico criado automaticamente para o usuário {instance.user.username}")
            except Exception as e:
                print(f"Erro ao criar técnico automático: {str(e)}")

class GrupoPermissao(models.Model):
    nome = models.CharField(max_length=100)
    descricao = models.TextField(blank=True)
    data_criacao = models.DateTimeField(auto_now_add=True)
    ultima_atualizacao = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.nome

    class Meta:
        verbose_name = "Grupo de Permissão"
        verbose_name_plural = "Grupos de Permissões"

class Menu(models.Model):
    nome = models.CharField(max_length=100)
    codigo = models.CharField(max_length=50, unique=True)
    descricao = models.TextField(blank=True)
    url = models.CharField(max_length=200)
    icone = models.CharField(max_length=50, default='fas fa-circle')
    ordem = models.IntegerField(default=0)
    menu_pai = models.ForeignKey('self', null=True, blank=True, on_delete=models.CASCADE, related_name='submenus')
    ativo = models.BooleanField(default=True)
    data_criacao = models.DateTimeField(auto_now_add=True)
    ultima_atualizacao = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.nome

    class Meta:
        ordering = ['ordem', 'nome']

class Permissao(models.Model):
    ACOES = [
        ('visualizar', 'Visualizar'),
        ('criar', 'Criar'),
        ('editar', 'Editar'),
        ('excluir', 'Excluir'),
        ('alterar_senha', 'Alterar Senha'),
    ]

    menu = models.ForeignKey(Menu, on_delete=models.CASCADE)
    grupo = models.ForeignKey(GrupoPermissao, on_delete=models.CASCADE, null=True, blank=True, related_name='permissoes')
    perfil = models.ForeignKey(Perfil, on_delete=models.CASCADE, null=True, blank=True, related_name='permissoes_diretas')
    acoes = models.JSONField(default=dict)  # Armazena as ações permitidas como {acao: boolean}
    data_criacao = models.DateTimeField(auto_now_add=True)
    ultima_atualizacao = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = [('menu', 'grupo'), ('menu', 'perfil')]
        constraints = [
            models.CheckConstraint(
                check=models.Q(grupo__isnull=False) | models.Q(perfil__isnull=False),
                name='permissao_grupo_ou_perfil'
            )
        ]

class PermissaoMenu(models.Model):
    PERMISSAO_CHOICES = [
        ('nenhum', 'Sem Acesso'),
        ('visualizar', 'Apenas Visualizar'),
        ('inserir', 'Inserir'),
        ('editar', 'Editar'),
        ('excluir', 'Excluir'),
        ('total', 'Acesso Total'),
    ]
    
    perfil = models.ForeignKey(Perfil, on_delete=models.CASCADE, related_name='permissoes_menu')
    menu = models.ForeignKey(Menu, on_delete=models.CASCADE)
    # O campo nivel_acesso existe no banco de dados conforme definido nas migrações
    nivel_acesso = models.CharField(max_length=20, choices=PERMISSAO_CHOICES, default='nenhum')
    
    def __str__(self):
        return f"{self.perfil} - {self.menu} - {self.get_nivel_acesso_display()}"
    
    class Meta:
        unique_together = ('perfil', 'menu')
        verbose_name = "Permissão de Menu"
        verbose_name_plural = "Permissões de Menu"
    
    @property
    def tipo_permissao(self):
        """Propriedade que retorna o valor de nivel_acesso."""
        return self.nivel_acesso
    
    def get_tipo_permissao_display(self):
        """Função para exibir o valor da permissão de forma legível."""
        return self.get_nivel_acesso_display()
