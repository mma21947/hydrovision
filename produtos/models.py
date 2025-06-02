from django.db import models
from django.utils.text import slugify
from django.urls import reverse

class Categoria(models.Model):
    nome = models.CharField(max_length=100)
    descricao = models.TextField(blank=True, null=True)
    slug = models.SlugField(max_length=120, unique=True, blank=True)
    
    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.nome)
        super().save(*args, **kwargs)
    
    def __str__(self):
        return self.nome
    
    class Meta:
        verbose_name = "Categoria"
        verbose_name_plural = "Categorias"
        ordering = ['nome']


class UnidadeMedida(models.Model):
    sigla = models.CharField(max_length=5, unique=True, verbose_name="Sigla")
    nome = models.CharField(max_length=50, verbose_name="Nome da Unidade")

    def __str__(self):
        return f"{self.nome} ({self.sigla})"

    class Meta:
        verbose_name = "Unidade de Medida"
        verbose_name_plural = "Unidades de Medida"
        ordering = ['nome']


class Produto(models.Model):
    codigo = models.CharField(max_length=30, unique=True)
    nome = models.CharField(max_length=200)
    descricao = models.TextField(blank=True, null=True)
    categoria = models.ForeignKey(Categoria, on_delete=models.SET_NULL, related_name="produtos", null=True, blank=True)
    preco_custo = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Preço de Custo")
    preco_venda = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Preço de Venda")
    estoque_atual = models.PositiveIntegerField(default=0)
    estoque_minimo = models.PositiveIntegerField(default=1)
    unidade = models.ForeignKey(UnidadeMedida, on_delete=models.PROTECT, related_name="produtos", verbose_name="Unidade")
    imagem = models.ImageField(upload_to='produtos/', blank=True, null=True)
    observacoes = models.TextField(blank=True, null=True, verbose_name="Observações")
    ativo = models.BooleanField(default=True)
    data_cadastro = models.DateTimeField(auto_now_add=True)
    ultima_atualizacao = models.DateTimeField(auto_now=True, verbose_name="Última Atualização")
    slug = models.SlugField(max_length=250, unique=True, blank=True)
    
    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(f"{self.codigo}-{self.nome}")
        super().save(*args, **kwargs)
    
    def __str__(self):
        return f"{self.codigo} - {self.nome}"
    
    def get_absolute_url(self):
        return reverse('detalhe_produto', kwargs={'slug': self.slug})
    
    @property
    def em_estoque(self):
        return self.estoque_atual > 0
    
    @property
    def estoque_baixo(self):
        return self.estoque_atual <= self.estoque_minimo
    
    class Meta:
        verbose_name = "Produto"
        verbose_name_plural = "Produtos"
        ordering = ['nome']


class MovimentacaoEstoque(models.Model):
    TIPO_CHOICES = [
        ('entrada', 'Entrada'),
        ('saida', 'Saída'),
        ('ajuste', 'Ajuste de Estoque'),
    ]
    
    produto = models.ForeignKey(Produto, on_delete=models.PROTECT, related_name="movimentacoes")
    tipo = models.CharField(max_length=20, choices=TIPO_CHOICES)
    quantidade = models.PositiveIntegerField()
    data = models.DateTimeField(auto_now_add=True)
    usuario = models.ForeignKey('auth.User', on_delete=models.PROTECT, related_name="movimentacoes_usuario")
    observacao = models.TextField(blank=True, null=True, verbose_name="Observação")
    ordem_servico = models.ForeignKey('ordens.OrdemServico', on_delete=models.SET_NULL, blank=True, null=True, related_name="movimentacoes_estoque")
    
    def __str__(self):
        return f"{self.tipo.capitalize()} de {self.quantidade} {self.produto.unidade.sigla} de {self.produto.nome}"
    
    class Meta:
        verbose_name = "Movimentação de Estoque"
        verbose_name_plural = "Movimentações de Estoque"
        ordering = ['-data'] 