from django.db import models
from django.utils.text import slugify
from clientes.models import Cliente
from tecnicos.models import Tecnico
from produtos.models import Produto
from django.core.validators import MinValueValidator, MaxValueValidator
from django.core.exceptions import ValidationError
from decimal import Decimal

class Categoria(models.Model):
    nome = models.CharField('Nome', max_length=100)
    descricao = models.TextField('Descrição', blank=True, null=True)
    slug = models.SlugField('Slug', max_length=150, unique=True, blank=True)
    data_criacao = models.DateTimeField('Data de Criação', auto_now_add=True, null=True)
    
    def __str__(self):
        return self.nome
    
    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.nome)
        super().save(*args, **kwargs)
    
    class Meta:
        verbose_name = 'Categoria'
        verbose_name_plural = 'Categorias'
        ordering = ['nome']

class ProdutoUtilizado(models.Model):
    ordem_servico = models.ForeignKey('OrdemServico', on_delete=models.CASCADE, related_name='produtos_utilizados')
    produto = models.ForeignKey(Produto, on_delete=models.PROTECT, related_name='utilizado_em_ordens')
    quantidade = models.DecimalField('Quantidade Utilizada', max_digits=10, decimal_places=2, default=1.00)
    preco_unitario = models.DecimalField('Preço Unitário (na OS)', max_digits=10, decimal_places=2, blank=True, null=True)

    def clean(self):
        try:
            # Verificar primeiro se produto_id existe usando getattr com default
            produto_id = getattr(self, 'produto_id', None)
            if produto_id is None:
                raise ValidationError('É necessário selecionar um produto válido')
                
            # Tentar acessar o produto com segurança
            try:
                produto = self.produto
                # Validar estoque apenas se conseguir acessar o produto
                if self.pk is None and produto:
                    if self.quantidade > produto.estoque_atual:
                        raise ValidationError(f'Estoque insuficiente para "{produto.nome}". Disponível: {produto.estoque_atual}')
            except Exception as e:
                # Logar o erro e usar uma mensagem mais amigável
                import logging
                logging.error(f"Erro ao acessar produto em ProdutoUtilizado.clean: {str(e)}")
                raise ValidationError('O produto selecionado não existe ou foi removido do sistema')
        except Exception as e:
            # Capturar qualquer outro erro que possa ocorrer
            raise ValidationError(f'Erro ao validar o produto: {str(e)}')

    def save(self, *args, **kwargs):
        try:
            # Verificar que produto_id não é nulo
            produto_id = getattr(self, 'produto_id', None)
            if produto_id is None:
                raise ValidationError('Não é possível salvar um ProdutoUtilizado sem um produto associado')
                
            # Tentar definir o preço unitário se for nulo
            if self.preco_unitario is None:
                try:
                    self.preco_unitario = self.produto.preco_venda
                except Exception:
                    # Se não conseguir acessar o produto, usar valor padrão
                    self.preco_unitario = Decimal('0')
                    
            super().save(*args, **kwargs)
        except Exception as e:
            # Logar o erro e re-lançar
            import logging
            logging.error(f"Erro ao salvar ProdutoUtilizado: {str(e)}")
            raise

    def __str__(self):
        try:
            # Obter os atributos com segurança
            produto_id = getattr(self, 'produto_id', None)
            ordem_id = getattr(self, 'ordem_servico_id', None)
            
            # Se não tem produto_id, não tentar acessar o produto
            if not produto_id:
                if ordem_id:
                    try:
                        numero_os = self.ordem_servico.numero
                        return f"Produto não disponível na OS #{numero_os}"
                    except:
                        return f"Produto não disponível na OS #{ordem_id}"
                return "Produto não definido"
            
            # Tentar obter informações do produto
            try:
                quantidade = getattr(self, 'quantidade', 0)
                produto_nome = self.produto.nome
                numero_os = self.ordem_servico.numero if ordem_id else '?'
                return f"{quantidade} x {produto_nome} na OS #{numero_os}"
            except:
                return f"Produto ID {produto_id} na OS #{ordem_id if ordem_id else '?'}"
                
        except Exception as e:
            # Em caso de qualquer erro, retornar algo seguro
            import logging
            logging.error(f"Erro no __str__ de ProdutoUtilizado: {str(e)}")
            return "ProdutoUtilizado (erro ao exibir informações)"

    class Meta:
        verbose_name = 'Produto Utilizado na OS'
        verbose_name_plural = 'Produtos Utilizados na OS'
        unique_together = ('ordem_servico', 'produto')

class OrdemServico(models.Model):
    STATUS_CHOICES = (
        ('aberta', 'Aberta'),
        ('em_andamento', 'Em Andamento'),
        ('aguardando_peca', 'Aguardando Peça'),
        ('aguardando_cliente', 'Aguardando Cliente'),
        ('concluida', 'Concluída'),
        ('cancelada', 'Cancelada'),
    )
    
    PRIORIDADE_CHOICES = (
        ('baixa', 'Baixa'),
        ('media', 'Média'),
        ('alta', 'Alta'),
        ('urgente', 'Urgente'),
    )
    
    numero = models.CharField('Número', max_length=20, unique=True)
    cliente = models.ForeignKey(Cliente, on_delete=models.CASCADE, related_name='ordens')
    equipamento = models.ForeignKey('equipamentos.Equipamento', on_delete=models.SET_NULL, null=True, blank=True, related_name='ordens')
    categoria = models.ForeignKey(Categoria, on_delete=models.SET_NULL, null=True, blank=True, related_name='ordens')
    tecnico = models.ForeignKey(Tecnico, on_delete=models.SET_NULL, null=True, blank=True, related_name='ordens')
    id_tecnico = models.IntegerField('ID do Técnico', null=True, blank=True)
    nome_tecnico = models.CharField('Nome do Técnico', max_length=200, null=True, blank=True)
    descricao = models.TextField('Descrição do Problema')
    solucao = models.TextField('Solução Aplicada', blank=True, null=True)
    data_abertura = models.DateTimeField('Data de Abertura', auto_now_add=True)
    data_agendamento = models.DateTimeField('Data de Agendamento', blank=True, null=True)
    data_inicio = models.DateTimeField('Data de Início', blank=True, null=True)
    data_conclusao = models.DateTimeField('Data de Conclusão', blank=True, null=True)
    
    status = models.CharField('Status', max_length=20, choices=STATUS_CHOICES, default='aberta')
    prioridade = models.CharField('Prioridade', max_length=10, choices=PRIORIDADE_CHOICES, default='media')
    
    # Localização do atendimento
    endereco = models.CharField('Endereço', max_length=200, blank=True, null=True)
    numero_endereco = models.CharField('Número', max_length=10, blank=True, null=True)
    complemento = models.CharField('Complemento', max_length=100, blank=True, null=True)
    bairro = models.CharField('Bairro', max_length=100, blank=True, null=True)
    cidade = models.CharField('Cidade', max_length=100, blank=True, null=True)
    estado = models.CharField('Estado', max_length=2, blank=True, null=True)
    cep = models.CharField('CEP', max_length=10, blank=True, null=True)
    
    # Localização do técnico no início e fim do atendimento
    latitude_inicio = models.FloatField('Latitude início', blank=True, null=True)
    longitude_inicio = models.FloatField('Longitude início', blank=True, null=True)
    precisao_inicio = models.FloatField('Precisão início (metros)', blank=True, null=True)
    latitude_fim = models.FloatField('Latitude fim', blank=True, null=True)
    longitude_fim = models.FloatField('Longitude fim', blank=True, null=True)
    precisao_fim = models.FloatField('Precisão fim (metros)', blank=True, null=True)
    
    # Dados financeiros
    valor_servico = models.DecimalField('Valor do Serviço', max_digits=10, decimal_places=2, default=0)
    valor_pecas = models.DecimalField('Valor de Peças/Materiais', max_digits=10, decimal_places=2, default=0)
    valor_deslocamento = models.DecimalField('Valor de Deslocamento', max_digits=10, decimal_places=2, default=0)
    desconto = models.DecimalField('Desconto', max_digits=10, decimal_places=2, default=0)
    valor_total = models.DecimalField('Valor Total', max_digits=10, decimal_places=2, default=0)
    
    # Avaliação e controle
    avaliacao_cliente = models.PositiveSmallIntegerField('Avaliação do Cliente', blank=True, null=True, validators=[MinValueValidator(1), MaxValueValidator(5)])
    comentario_cliente = models.TextField('Comentário do Cliente', blank=True, null=True)
    assinatura_cliente = models.TextField('Assinatura Digital do Cliente', blank=True, null=True)
    
    # Controle interno
    observacoes_internas = models.TextField('Observações Internas', blank=True, null=True)
    link_pagamento = models.URLField('Link de Pagamento', blank=True, null=True)
    preferencia_contato = models.CharField('Preferência de Contato', max_length=50, blank=True, null=True)
    
    # Metadados
    criado_por = models.CharField('Criado por', max_length=100, blank=True, null=True)
    atualizado_por = models.CharField('Atualizado por', max_length=100, blank=True, null=True)
    slug = models.SlugField(max_length=100, unique=True, blank=True, null=True)
    ativa = models.BooleanField('Ativa', default=True)
    
    # Novo campo ManyToMany para produtos utilizados
    produtos = models.ManyToManyField(
        Produto, 
        through=ProdutoUtilizado, 
        related_name='ordens_servico', 
        blank=True
    )
    
    def gerar_numero_os(self):
        from django.utils import timezone
        
        # Obter ano e mês atual
        now = timezone.now()
        ano = now.strftime('%Y')
        mes = now.strftime('%m')
        
        # Prefixo para o número da OS baseado em ano e mês
        prefixo = f"OS{ano}{mes}"
        
        # Buscar a última OS com este prefixo
        ultima_os = OrdemServico.objects.filter(
            numero__startswith=prefixo
        ).order_by('-numero').first()
        
        # Iniciar contador
        if ultima_os:
            # Extrair o número sequencial da última OS
            try:
                ultimo_numero = int(ultima_os.numero[8:])
                numero_sequencial = ultimo_numero + 1
            except (ValueError, IndexError):
                # Se houver algum erro, começar do 1
                numero_sequencial = 1
        else:
            numero_sequencial = 1
        
        # Formatar o número completo da OS
        return f"{prefixo}{numero_sequencial:04d}"
    
    def save(self, *args, **kwargs):
        # Calcular valor total
        self.valor_total = (self.valor_servico + self.valor_pecas + self.valor_deslocamento) - self.desconto
        
        # Gerar número da OS se não existir
        if not self.numero:
            self.numero = self.gerar_numero_os()
        
        # Gerar slug se não existir
        if not self.slug:
            self.slug = slugify(f"os-{self.numero}")
            
        # Atualizar campos do técnico
        if self.tecnico:
            self.id_tecnico = self.tecnico.id
            self.nome_tecnico = self.tecnico.nome_completo
        else:
            self.id_tecnico = None
            self.nome_tecnico = None
        
        super().save(*args, **kwargs)
    
    def __str__(self):
        return f"OS #{self.numero} - {self.cliente.nome}"
    
    class Meta:
        verbose_name = 'Ordem de Serviço'
        verbose_name_plural = 'Ordens de Serviço'
        ordering = ['-data_abertura']
    
    @property
    def dias_aberto(self):
        from django.utils import timezone
        if self.status in ['concluida', 'cancelada']:
            return (self.data_conclusao - self.data_abertura).days
        return (timezone.now() - self.data_abertura).days
    
    @property
    def dentro_do_prazo(self):
        return self.dias_aberto <= 3  # Considere 3 dias como prazo padrão
    
    def iniciar_atendimento(self, latitude=None, longitude=None, precisao=None):
        """
        Registra o início do atendimento da ordem de serviço pelo técnico
        Atualiza o status da ordem para "em_andamento" e registra a localização
        """
        from django.utils import timezone
        from tecnicos.models import LocalizacaoAtendimento
        
        # Verificar se já foi iniciada
        if self.data_inicio:
            return False
            
        # Verificar se tem técnico atribuído
        if not self.tecnico:
            return False
            
        # Atualizar status e data de início
        self.status = 'em_andamento'
        self.data_inicio = timezone.now()
        
        # Registrar coordenadas, se fornecidas
        if latitude and longitude:
            self.latitude_inicio = latitude
            self.longitude_inicio = longitude
            self.precisao_inicio = precisao
            
            # Registrar na tabela de localização
            LocalizacaoAtendimento.registrar_inicio_atendimento(
                self, latitude, longitude, precisao
            )
        
        self.save()
        return True
        
    def finalizar_atendimento(self, latitude=None, longitude=None, precisao=None, solucao=None):
        """
        Registra o fim do atendimento da ordem de serviço pelo técnico
        Atualiza o status da ordem para "concluida" e registra a localização
        """
        from django.utils import timezone
        from tecnicos.models import LocalizacaoAtendimento
        
        # Verificar se já foi concluída
        if self.data_conclusao:
            return False
            
        # Verificar se foi iniciada
        if not self.data_inicio:
            return False
            
        # Atualizar status, data de conclusão e solução
        self.status = 'concluida'
        self.data_conclusao = timezone.now()
        if solucao:
            self.solucao = solucao
        
        # Registrar coordenadas, se fornecidas
        if latitude and longitude:
            self.latitude_fim = latitude
            self.longitude_fim = longitude
            self.precisao_fim = precisao
            
            # Registrar na tabela de localização
            LocalizacaoAtendimento.registrar_fim_atendimento(
                self, latitude, longitude, precisao
            )
        
        self.save()
        return True


class Anexo(models.Model):
    ordem = models.ForeignKey(OrdemServico, on_delete=models.CASCADE, related_name='anexos')
    titulo = models.CharField('Título', max_length=100)
    arquivo = models.FileField('Arquivo', upload_to='anexos')
    data_upload = models.DateTimeField('Data de Upload', auto_now_add=True)
    
    def __str__(self):
        return self.titulo
    
    class Meta:
        verbose_name = 'Anexo'
        verbose_name_plural = 'Anexos'
        ordering = ['-data_upload']


class Comentario(models.Model):
    TIPO_AUTOR_CHOICES = (
        ('tecnico', 'Técnico'),
        ('operador', 'Operador'),
        ('sistema', 'Sistema'),
        ('cliente', 'Cliente'),
    )
    
    TIPO_PROBLEMA_CHOICES = (
        ('sem_problema', 'Sem Problema'),
        ('acesso', 'Problema de Acesso'),
        ('material', 'Falta de Material'),
        ('cliente', 'Problema com Cliente'),
        ('equipamento', 'Problema com Equipamento'),
        ('tecnico', 'Problema com Técnico'),
        ('outro', 'Outro Problema'),
    )
    
    ordem = models.ForeignKey(OrdemServico, on_delete=models.CASCADE, related_name='comentarios')
    autor = models.CharField('Autor', max_length=100)
    tipo_autor = models.CharField('Tipo de Autor', max_length=20, choices=TIPO_AUTOR_CHOICES, default='operador')
    texto = models.TextField('Texto')
    data_criacao = models.DateTimeField('Data de Criação', auto_now_add=True)
    interno = models.BooleanField('Interno', default=False)
    
    # Novos campos para destacar problemas
    reportando_problema = models.BooleanField('Reportando Problema', default=False)
    tipo_problema = models.CharField('Tipo de Problema', max_length=20, choices=TIPO_PROBLEMA_CHOICES, default='sem_problema')
    resolvido = models.BooleanField('Problema Resolvido', default=False)
    data_resolucao = models.DateTimeField('Data de Resolução', null=True, blank=True)
    
    def __str__(self):
        return f"Comentário de {self.autor} em {self.data_criacao.strftime('%d/%m/%Y %H:%M')}"
    
    class Meta:
        verbose_name = 'Comentário'
        verbose_name_plural = 'Comentários'
        ordering = ['-data_criacao']
