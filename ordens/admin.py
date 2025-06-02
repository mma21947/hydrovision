from django.contrib import admin
from .models import Categoria, OrdemServico, Anexo, Comentario, ProdutoUtilizado

@admin.register(Categoria)
class CategoriaAdmin(admin.ModelAdmin):
    list_display = ('nome', 'descricao')
    search_fields = ('nome',)
    prepopulated_fields = {"slug": ("nome",)}

# Inline para exibir/adicionar produtos utilizados diretamente na OS
class ProdutoUtilizadoInline(admin.TabularInline):
    model = ProdutoUtilizado
    extra = 1 # Quantos formulários extras mostrar
    autocomplete_fields = ['produto'] # Facilitar seleção
    readonly_fields = ('preco_unitario',) # Preço é pego automaticamente ao salvar
    fields = ('produto', 'quantidade', 'preco_unitario')

class AnexoInline(admin.TabularInline):
    model = Anexo
    extra = 1

class ComentarioInline(admin.TabularInline):
    model = Comentario
    extra = 1
    readonly_fields = ('data_criacao', 'autor')
    fields = ('texto', 'autor', 'data_criacao', 'interno', 'reportando_problema', 'tipo_problema')

@admin.register(OrdemServico)
class OrdemServicoAdmin(admin.ModelAdmin):
    list_display = ('numero', 'cliente', 'tecnico', 'categoria', 'status', 'prioridade', 'data_abertura', 'avaliacao_cliente')
    list_filter = ('status', 'prioridade', 'categoria', 'data_abertura')
    search_fields = ('numero', 'cliente__nome', 'tecnico__nome_completo', 'descricao')
    readonly_fields = ('valor_total', 'slug')
    prepopulated_fields = {"slug": ("numero",)}
    autocomplete_fields = ['cliente', 'tecnico', 'categoria']
    inlines = [ProdutoUtilizadoInline, AnexoInline, ComentarioInline]
    fieldsets = (
        ('Informações Básicas', {
            'fields': ('numero', 'cliente', 'categoria', 'tecnico', 'descricao', 'solucao')
        }),
        ('Datas', {
            'fields': ('data_abertura', 'data_agendamento', 'data_inicio', 'data_conclusao')
        }),
        ('Status e Prioridade', {
            'fields': ('status', 'prioridade')
        }),
        ('Localização do Atendimento', {
            'fields': ('endereco', 'numero_endereco', 'complemento', 'bairro', 'cidade', 'estado', 'cep')
        }),
        ('Localização do Técnico', {
            'fields': (
                'latitude_inicio', 'longitude_inicio', 'precisao_inicio',
                'latitude_fim', 'longitude_fim', 'precisao_fim'
            ),
            'classes': ('collapse',)
        }),
        ('Valores', {
            'fields': ('valor_servico', 'valor_pecas', 'valor_deslocamento', 'desconto', 'valor_total')
        }),
        ('Avaliação do Cliente', {
            'fields': ('avaliacao_cliente', 'comentario_cliente')
        }),
        ('Controle Interno', {
            'fields': ('observacoes_internas', 'link_pagamento', 'preferencia_contato', 'ativa'),
            'classes': ('collapse',)
        }),
        ('Metadados', {
            'fields': ('criado_por', 'atualizado_por', 'slug'),
            'classes': ('collapse',)
        }),
    )

@admin.register(Anexo)
class AnexoAdmin(admin.ModelAdmin):
    list_display = ('titulo', 'ordem', 'data_upload')
    list_filter = ('data_upload',)
    search_fields = ('titulo', 'ordem__numero')

@admin.register(Comentario)
class ComentarioAdmin(admin.ModelAdmin):
    list_display = ('autor', 'ordem', 'texto', 'data_criacao', 'interno')
    list_filter = ('data_criacao', 'interno')
    search_fields = ('autor', 'texto', 'ordem__numero')
