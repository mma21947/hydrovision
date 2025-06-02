from django.db import models
from django.contrib.auth.models import User
from django.utils.text import slugify
from django.utils import timezone
import uuid

class Tecnico(models.Model):
    """
    Modelo para técnicos de campo que atendem às ordens de serviço
    """
    NIVEL_CHOICES = (
        ('junior', 'Júnior'),
        ('pleno', 'Pleno'),
        ('senior', 'Sênior'),
        ('especialista', 'Especialista')
    )
    
    STATUS_CHOICES = (
        ('disponivel', 'Disponível'),
        ('em_atendimento', 'Em Atendimento'),
        ('ausente', 'Ausente'),
        ('ferias', 'Férias'),
        ('licenca', 'Licença')
    )
    
    # Dados básicos
    usuario = models.OneToOneField(User, on_delete=models.CASCADE, related_name='tecnico', null=True, blank=True)
    codigo = models.CharField(max_length=15, unique=True, verbose_name="Código")
    nome_completo = models.CharField(max_length=100)
    slug = models.SlugField(max_length=150, unique=True, null=True, blank=True)
    cpf = models.CharField(max_length=14, unique=True, verbose_name="CPF")
    rg = models.CharField(max_length=20, blank=True, null=True, verbose_name="RG")
    data_nascimento = models.DateField(verbose_name="Data de Nascimento")
    
    # Contato
    email = models.EmailField(max_length=100)
    telefone = models.CharField(max_length=15, blank=True, null=True)
    celular = models.CharField(max_length=15)
    
    # Endereço
    endereco = models.CharField(max_length=100, verbose_name="Endereço")
    numero = models.CharField(max_length=10, verbose_name="Número")
    complemento = models.CharField(max_length=50, blank=True, null=True)
    bairro = models.CharField(max_length=50)
    cidade = models.CharField(max_length=50)
    estado = models.CharField(max_length=2)
    cep = models.CharField(max_length=9, verbose_name="CEP")
    
    # Dados profissionais
    nivel = models.CharField(max_length=20, choices=NIVEL_CHOICES, default='junior')
    especialidade = models.CharField(max_length=100, blank=True, null=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='disponivel')
    data_admissao = models.DateField(verbose_name="Data de Admissão")
    data_demissao = models.DateField(blank=True, null=True, verbose_name="Data de Demissão")
    foto = models.ImageField(upload_to='tecnicos/', blank=True, null=True)
    
    # Status de atividade
    ativo = models.BooleanField(default=True, verbose_name="Ativo")
    
    # Geolocalização
    latitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    longitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    ultima_atualizacao_local = models.DateTimeField(null=True, blank=True)
    
    # Metadados
    certificacoes = models.TextField(blank=True, null=True, verbose_name="Certificações")
    habilidades = models.TextField(blank=True, null=True)
    observacoes = models.TextField(blank=True, null=True, verbose_name="Observações")
    data_criacao = models.DateTimeField(auto_now_add=True)
    data_atualizacao = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Técnico"
        verbose_name_plural = "Técnicos"
        ordering = ['nome_completo']
    
    def __str__(self):
        return f"{self.nome_completo} ({self.codigo})"
    
    def save(self, *args, **kwargs):
        # Gerar slug automaticamente se não existir
        if not self.slug:
            self.slug = slugify(f"{self.nome_completo}-{uuid.uuid4().hex[:8]}")
        
        # Formatar CPF se necessário (remover pontuação)
        if self.cpf:
            self.cpf = ''.join(filter(str.isdigit, self.cpf))
            
            # Reinsere a formatação se não estiver formatado
            if len(self.cpf) == 11 and '.' not in self.cpf:
                self.cpf = f"{self.cpf[:3]}.{self.cpf[3:6]}.{self.cpf[6:9]}-{self.cpf[9:]}"
                
        super().save(*args, **kwargs)
        
    @classmethod
    def cpf_existe(cls, cpf):
        """
        Verifica se um CPF já existe no banco de dados
        Retorna True se o CPF já existir, False caso contrário
        """
        # Remove todos os caracteres não numéricos
        cpf_limpo = ''.join(filter(str.isdigit, cpf))
        
        # Verifica se existe técnico com esse CPF
        # Busca tanto pela versão formatada quanto pela versão sem formatação
        return cls.objects.filter(models.Q(cpf=cpf) | 
                                models.Q(cpf=cpf_limpo) |
                                models.Q(cpf=f"{cpf_limpo[:3]}.{cpf_limpo[3:6]}.{cpf_limpo[6:9]}-{cpf_limpo[9:]}")).exists()
    
    def atualizar_localizacao(self, latitude, longitude):
        self.latitude = latitude
        self.longitude = longitude
        self.ultima_atualizacao_local = timezone.now()
        self.save()
        
        # Verificar se o técnico tem alguma ordem em status 'aberta' atribuída a ele
        # e alterar o status para 'em_andamento'
        from ordens.models import OrdemServico
        ordens_abertas = OrdemServico.objects.filter(
            tecnico=self,
            status='aberta'
        )
        
        for ordem in ordens_abertas:
            # Iniciar o atendimento automaticamente
            ordem.iniciar_atendimento(latitude, longitude)
            
        return ordens_abertas.count() > 0  # Retorna True se alguma ordem foi atualizada
        
    @property
    def disponivel(self):
        return self.status == 'disponivel'
        
    @property
    def localizacao_atualizada(self):
        if not self.ultima_atualizacao_local:
            return False
        diferenca = timezone.now() - self.ultima_atualizacao_local
        return diferenca.total_seconds() < 3600  # Menos de 1 hora

class LocalizacaoAtendimento(models.Model):
    """
    Modelo para armazenar o histórico de localizações dos técnicos durante atendimentos
    """
    tecnico = models.ForeignKey(Tecnico, on_delete=models.CASCADE, related_name='localizacoes_atendimento')
    ordem_servico = models.ForeignKey('ordens.OrdemServico', on_delete=models.CASCADE, related_name='localizacoes')
    latitude = models.FloatField('Latitude')
    longitude = models.FloatField('Longitude')
    data_hora = models.DateTimeField('Data e Hora', auto_now_add=True)
    tipo = models.CharField('Tipo', max_length=20, choices=(
        ('inicio', 'Início do Atendimento'),
        ('fim', 'Fim do Atendimento'),
        ('atualizacao', 'Atualização Durante Atendimento'),
    ))
    precisao = models.FloatField('Precisão (metros)', null=True, blank=True)
    
    def __str__(self):
        return f"Localização de {self.tecnico.nome_completo} em {self.data_hora.strftime('%d/%m/%Y %H:%M')}"
    
    class Meta:
        verbose_name = 'Localização de Atendimento'
        verbose_name_plural = 'Localizações de Atendimento'
        ordering = ['-data_hora']
        
    @classmethod
    def registrar_inicio_atendimento(cls, ordem_servico, latitude, longitude, precisao=None):
        """
        Registra a localização do técnico no início do atendimento
        """
        if not ordem_servico.tecnico:
            return None
            
        localizacao = cls(
            tecnico=ordem_servico.tecnico,
            ordem_servico=ordem_servico,
            latitude=latitude,
            longitude=longitude,
            tipo='inicio',
            precisao=precisao
        )
        localizacao.save()
        
        # Atualiza também a localização atual do técnico
        ordem_servico.tecnico.atualizar_localizacao(latitude, longitude)
        
        # Atualiza o status do técnico para em_atendimento
        ordem_servico.tecnico.status = 'em_atendimento'
        ordem_servico.tecnico.save()
        
        return localizacao
        
    @classmethod
    def registrar_fim_atendimento(cls, ordem_servico, latitude, longitude, precisao=None):
        """
        Registra a localização do técnico no fim do atendimento
        """
        if not ordem_servico.tecnico:
            return None
            
        localizacao = cls(
            tecnico=ordem_servico.tecnico,
            ordem_servico=ordem_servico,
            latitude=latitude,
            longitude=longitude,
            tipo='fim',
            precisao=precisao
        )
        localizacao.save()
        
        # Atualiza também a localização atual do técnico
        ordem_servico.tecnico.atualizar_localizacao(latitude, longitude)
        
        # Atualiza o status do técnico para disponível
        ordem_servico.tecnico.status = 'disponivel'
        ordem_servico.tecnico.save()
        
        return localizacao

class RegistroPonto(models.Model):
    """
    Modelo para registrar os pontos de entrada e saída dos técnicos
    """
    TIPO_CHOICES = (
        ('entrada', 'Entrada'),
        ('saida', 'Saída'),
        ('inicio_intervalo', 'Início do Intervalo'),
        ('fim_intervalo', 'Fim do Intervalo'),
    )
    
    tecnico = models.ForeignKey(Tecnico, on_delete=models.CASCADE, related_name='registros_ponto')
    tipo = models.CharField('Tipo', max_length=20, choices=TIPO_CHOICES)
    data_hora = models.DateTimeField('Data e Hora', auto_now_add=True)
    latitude = models.FloatField('Latitude', null=True, blank=True)
    longitude = models.FloatField('Longitude', null=True, blank=True)
    precisao = models.FloatField('Precisão (metros)', null=True, blank=True)
    observacao = models.TextField('Observação', blank=True, null=True)
    ip = models.GenericIPAddressField('Endereço IP', null=True, blank=True)
    
    class Meta:
        verbose_name = 'Registro de Ponto'
        verbose_name_plural = 'Registros de Ponto'
        ordering = ['-data_hora']
    
    def __str__(self):
        return f"{self.tecnico.nome_completo} - {self.get_tipo_display()} em {self.data_hora.strftime('%d/%m/%Y %H:%M')}"
    
    @property
    def localizacao_formatada(self):
        if self.latitude and self.longitude:
            return f"{self.latitude:.6f}, {self.longitude:.6f}"
        return "Não registrada"
