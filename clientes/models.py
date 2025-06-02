from django.db import models
from django.utils.text import slugify
from django.utils import timezone

class Empresa(models.Model):
    nome = models.CharField(max_length=200)
    nome_fantasia = models.CharField(max_length=200, blank=True, null=True)
    cnpj = models.CharField(max_length=18, unique=True)
    inscricao_estadual = models.CharField(max_length=20, blank=True, null=True)
    inscricao_municipal = models.CharField(max_length=20, blank=True, null=True)
    endereco = models.CharField(max_length=200, blank=True, null=True)
    numero = models.CharField(max_length=10, blank=True, null=True)
    complemento = models.CharField(max_length=100, blank=True, null=True)
    bairro = models.CharField(max_length=100, blank=True, null=True)
    cidade = models.CharField(max_length=100, blank=True, null=True)
    estado = models.CharField(max_length=2, blank=True, null=True)
    cep = models.CharField(max_length=9, blank=True, null=True)
    telefone = models.CharField(max_length=20, blank=True, null=True)
    email = models.EmailField(blank=True, null=True)
    site = models.URLField(blank=True, null=True)
    logo = models.ImageField(upload_to='empresas/logos/', blank=True, null=True)
    ativo = models.BooleanField(default=True)
    data_criacao = models.DateTimeField(default=timezone.now)
    ultima_atualizacao = models.DateTimeField(default=timezone.now)
    slug = models.SlugField(max_length=250, unique=True, blank=True, null=True)

    def __str__(self):
        return self.nome

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.nome)
        if not self.data_criacao:
            self.data_criacao = timezone.now()
        self.ultima_atualizacao = timezone.now()
        super().save(*args, **kwargs)

    class Meta:
        verbose_name = 'Empresa'
        verbose_name_plural = 'Empresas'
        ordering = ['nome']

class Cliente(models.Model):
    TIPO_CHOICES = [
        ('PF', 'Pessoa Física'),
        ('PJ', 'Pessoa Jurídica'),
    ]
    
    codigo = models.CharField(max_length=20, unique=True, blank=True, null=True)
    tipo = models.CharField(max_length=2, choices=TIPO_CHOICES, default='PF')
    nome = models.CharField(max_length=200)
    cpf_cnpj = models.CharField(max_length=18, unique=True)
    rg_ie = models.CharField(max_length=20, blank=True, null=True)
    data_nascimento = models.DateField(blank=True, null=True)
    email = models.EmailField(blank=True, null=True)
    telefone = models.CharField(max_length=20, blank=True, null=True)
    celular = models.CharField(max_length=20, blank=True, null=True)
    endereco = models.CharField(max_length=200, blank=True, null=True)
    numero = models.CharField(max_length=10, blank=True, null=True)
    complemento = models.CharField(max_length=100, blank=True, null=True)
    bairro = models.CharField(max_length=100, blank=True, null=True)
    cidade = models.CharField(max_length=100, blank=True, null=True)
    estado = models.CharField(max_length=2, blank=True, null=True)
    cep = models.CharField(max_length=9, blank=True, null=True)
    empresa = models.ForeignKey(Empresa, on_delete=models.SET_NULL, null=True, blank=True)
    observacoes = models.TextField(blank=True, null=True)
    ativo = models.BooleanField(default=True)
    data_criacao = models.DateTimeField(default=timezone.now)
    ultima_atualizacao = models.DateTimeField(default=timezone.now)
    slug = models.SlugField(max_length=250, unique=True, blank=True, null=True)

    def __str__(self):
        return f"{self.nome} ({self.get_tipo_display()})"

    def save(self, *args, **kwargs):
        # Gerar um código único caso não tenha sido fornecido
        if not self.codigo:
            # Format: CLI + ano atual + 4 dígitos sequenciais
            ultimo_cliente = Cliente.objects.order_by('-id').first()
            if ultimo_cliente and ultimo_cliente.codigo and ultimo_cliente.codigo.startswith('CLI'):
                try:
                    ultimo_numero = int(ultimo_cliente.codigo[7:])
                    novo_numero = ultimo_numero + 1
                except (ValueError, IndexError):
                    novo_numero = 1
            else:
                novo_numero = 1
            
            ano_atual = timezone.now().year
            self.codigo = f"CLI{ano_atual}{novo_numero:04d}"
            
        if not self.slug:
            self.slug = slugify(self.nome)
        if not self.data_criacao:
            self.data_criacao = timezone.now()
        self.ultima_atualizacao = timezone.now()
        super().save(*args, **kwargs)

    class Meta:
        verbose_name = 'Cliente'
        verbose_name_plural = 'Clientes'
        ordering = ['nome']

class ContratoEmpresa(models.Model):
    empresa = models.ForeignKey(Empresa, on_delete=models.CASCADE)
    descricao = models.CharField(max_length=200)
    data_inicio = models.DateField()
    data_fim = models.DateField(blank=True, null=True)
    valor_mensal = models.DecimalField(max_digits=10, decimal_places=2)
    observacoes = models.TextField(blank=True, null=True)
    ativo = models.BooleanField(default=True)
    data_criacao = models.DateTimeField(default=timezone.now)
    ultima_atualizacao = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return f"Contrato {self.descricao} - {self.empresa.nome}"

    def save(self, *args, **kwargs):
        if not self.data_criacao:
            self.data_criacao = timezone.now()
        self.ultima_atualizacao = timezone.now()
        super().save(*args, **kwargs)

    class Meta:
        verbose_name = 'Contrato'
        verbose_name_plural = 'Contratos'
        ordering = ['-data_inicio']

class ContratoCliente(models.Model):
    cliente = models.ForeignKey(Cliente, on_delete=models.CASCADE, related_name='contratos')
    arquivo = models.FileField('Arquivo do Contrato', upload_to='contratos/clientes')
    descricao = models.CharField('Descrição', max_length=200)
    data_upload = models.DateTimeField('Data de Upload', auto_now_add=True)
    
    def __str__(self):
        return f"Contrato {self.descricao} - {self.cliente.nome}"
    
    class Meta:
        verbose_name = 'Contrato de Cliente'
        verbose_name_plural = 'Contratos de Clientes'
        ordering = ['-data_upload']
