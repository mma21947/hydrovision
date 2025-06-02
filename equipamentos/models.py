from django.db import models
from django.utils.text import slugify
from django.utils import timezone
from clientes.models import Cliente

class CategoriaEquipamento(models.Model):
    nome = models.CharField('Nome', max_length=100)
    descricao = models.TextField('Descrição', blank=True, null=True)
    slug = models.SlugField('Slug', max_length=150, unique=True, blank=True)
    
    def __str__(self):
        return self.nome
    
    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.nome)
        super().save(*args, **kwargs)
    
    class Meta:
        verbose_name = 'Categoria de Equipamento'
        verbose_name_plural = 'Categorias de Equipamentos'
        ordering = ['nome']

class Equipamento(models.Model):
    STATUS_CHOICES = (
        ('ativo', 'Ativo'),
        ('manutencao', 'Em Manutenção'),
        ('inativo', 'Inativo'),
    )
    
    codigo = models.CharField('Código', max_length=30, unique=True, blank=True)
    nome = models.CharField('Nome/Modelo', max_length=200)
    categoria = models.ForeignKey(CategoriaEquipamento, on_delete=models.SET_NULL, null=True, related_name='equipamentos')
    cliente = models.ForeignKey(Cliente, on_delete=models.CASCADE, related_name='equipamentos')
    marca = models.CharField('Marca', max_length=100, blank=True, null=True)
    modelo = models.CharField('Modelo', max_length=100, blank=True, null=True)
    numero_serie = models.CharField('Número de Série', max_length=100, blank=True, null=True)
    data_aquisicao = models.DateField('Data de Aquisição', blank=True, null=True)
    data_instalacao = models.DateField('Data de Instalação', blank=True, null=True)
    data_garantia_fim = models.DateField('Fim da Garantia', blank=True, null=True)
    status = models.CharField('Status', max_length=15, choices=STATUS_CHOICES, default='ativo')
    descricao = models.TextField('Descrição', blank=True, null=True)
    observacoes = models.TextField('Observações', blank=True, null=True)
    
    # Localização
    local_instalacao = models.CharField('Local de Instalação', max_length=200, blank=True, null=True)
    
    # Dados técnicos
    especificacoes_tecnicas = models.TextField('Especificações Técnicas', blank=True, null=True)
    
    # Metadados
    data_cadastro = models.DateTimeField('Data de Cadastro', auto_now_add=True)
    ultima_atualizacao = models.DateTimeField('Última Atualização', auto_now=True)
    foto = models.ImageField('Foto', upload_to='equipamentos', blank=True, null=True)
    manual = models.FileField('Manual', upload_to='equipamentos/manuais', blank=True, null=True)
    slug = models.SlugField(max_length=250, unique=True, blank=True, null=True)
    
    def gerar_codigo_equipamento(self):
        # Obter ano e mês atual
        now = timezone.now()
        ano = now.strftime('%Y')
        mes = now.strftime('%m')
        
        # Prefixo para o código do equipamento baseado em ano e mês
        prefixo = f"EQP{ano}{mes}"
        
        # Buscar o último equipamento com este prefixo
        ultimo_equipamento = Equipamento.objects.filter(
            codigo__startswith=prefixo
        ).order_by('-codigo').first()
        
        # Iniciar contador
        if ultimo_equipamento:
            # Extrair o número sequencial do último código
            try:
                ultimo_numero = int(ultimo_equipamento.codigo[9:])
                numero_sequencial = ultimo_numero + 1
            except (ValueError, IndexError):
                # Se houver algum erro, começar do 1
                numero_sequencial = 1
        else:
            numero_sequencial = 1
        
        # Formatar o número completo do código do equipamento
        return f"{prefixo}{numero_sequencial:04d}"
    
    def save(self, *args, **kwargs):
        # Gerar código do equipamento se não existir
        if not self.codigo:
            self.codigo = self.gerar_codigo_equipamento()
            
        # Gerar slug se não existir
        if not self.slug:
            self.slug = slugify(f"{self.cliente.nome}-{self.nome}-{self.codigo}")
        super().save(*args, **kwargs)
    
    def __str__(self):
        return f"{self.nome} ({self.codigo}) - {self.cliente.nome}"
    
    def em_garantia(self):
        if not self.data_garantia_fim:
            return False
        return timezone.now().date() <= self.data_garantia_fim
    
    @property
    def foto_url(self):
        """Retorna a URL da foto ou None se não houver foto"""
        if self.foto and hasattr(self.foto, 'url'):
            return self.foto.url
        return None
    
    class Meta:
        verbose_name = 'Equipamento'
        verbose_name_plural = 'Equipamentos'
        ordering = ['cliente__nome', 'nome']
        unique_together = ('cliente', 'numero_serie')

class ManutencaoEquipamento(models.Model):
    TIPO_CHOICES = (
        ('preventiva', 'Preventiva'),
        ('corretiva', 'Corretiva'),
        ('instalacao', 'Instalação'),
        ('atualizacao', 'Atualização'),
    )
    
    equipamento = models.ForeignKey(Equipamento, on_delete=models.CASCADE, related_name='manutencoes')
    ordem_servico = models.ForeignKey('ordens.OrdemServico', on_delete=models.SET_NULL, null=True, blank=True, related_name='manutencoes_equipamento')
    tipo = models.CharField('Tipo', max_length=20, choices=TIPO_CHOICES)
    data = models.DateTimeField('Data da Manutenção')
    descricao = models.TextField('Descrição')
    solucao = models.TextField('Solução Aplicada', blank=True, null=True)
    responsavel = models.CharField('Responsável', max_length=100)
    custo = models.DecimalField('Custo', max_digits=10, decimal_places=2, default=0)
    
    def __str__(self):
        return f"{self.get_tipo_display()} em {self.equipamento.nome} - {self.data.strftime('%d/%m/%Y')}"
    
    class Meta:
        verbose_name = 'Manutenção de Equipamento'
        verbose_name_plural = 'Manutenções de Equipamentos'
        ordering = ['-data']
