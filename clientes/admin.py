from django.contrib import admin
from .models import Cliente, Empresa, ContratoEmpresa, ContratoCliente

@admin.register(Cliente)
class ClienteAdmin(admin.ModelAdmin):
    list_display = ('nome', 'tipo', 'cpf_cnpj', 'email', 'telefone', 'ativo')
    list_filter = ('tipo', 'ativo', 'cidade', 'estado')
    search_fields = ('nome', 'cpf_cnpj', 'email')
    readonly_fields = ('data_criacao', 'ultima_atualizacao', 'slug')
    fieldsets = (
        ('Informações Básicas', {
            'fields': (
                'tipo', 'nome', 'cpf_cnpj', 'rg_ie', 'data_nascimento',
                'email', 'telefone', 'celular'
            )
        }),
        ('Endereço', {
            'fields': (
                'endereco', 'numero', 'complemento', 'bairro',
                'cidade', 'estado', 'cep'
            )
        }),
        ('Empresa', {
            'fields': ('empresa',)
        }),
        ('Informações Adicionais', {
            'fields': ('observacoes', 'ativo')
        }),
        ('Metadados', {
            'fields': ('data_criacao', 'ultima_atualizacao', 'slug'),
            'classes': ('collapse',)
        })
    )

@admin.register(Empresa)
class EmpresaAdmin(admin.ModelAdmin):
    list_display = ('nome', 'cnpj', 'email', 'telefone', 'ativo')
    list_filter = ('ativo', 'cidade', 'estado')
    search_fields = ('nome', 'nome_fantasia', 'cnpj', 'email')
    readonly_fields = ('data_criacao', 'ultima_atualizacao', 'slug')
    fieldsets = (
        ('Informações Básicas', {
            'fields': (
                'nome', 'nome_fantasia', 'cnpj',
                'inscricao_estadual', 'inscricao_municipal'
            )
        }),
        ('Contato', {
            'fields': ('email', 'telefone', 'site')
        }),
        ('Endereço', {
            'fields': (
                'endereco', 'numero', 'complemento', 'bairro',
                'cidade', 'estado', 'cep'
            )
        }),
        ('Visual', {
            'fields': ('logo',)
        }),
        ('Status', {
            'fields': ('ativo',)
        }),
        ('Metadados', {
            'fields': ('data_criacao', 'ultima_atualizacao', 'slug'),
            'classes': ('collapse',)
        })
    )

@admin.register(ContratoEmpresa)
class ContratoEmpresaAdmin(admin.ModelAdmin):
    list_display = ('empresa', 'descricao', 'data_inicio', 'data_fim', 'valor_mensal', 'ativo')
    list_filter = ('ativo', 'data_inicio', 'data_fim')
    search_fields = ('empresa__nome', 'descricao')
    readonly_fields = ('data_criacao', 'ultima_atualizacao')
    fieldsets = (
        ('Informações do Contrato', {
            'fields': (
                'empresa', 'descricao', 'data_inicio', 'data_fim',
                'valor_mensal', 'observacoes', 'ativo'
            )
        }),
        ('Metadados', {
            'fields': ('data_criacao', 'ultima_atualizacao'),
            'classes': ('collapse',)
        })
    )

@admin.register(ContratoCliente)
class ContratoClienteAdmin(admin.ModelAdmin):
    list_display = ('cliente', 'descricao', 'data_upload')
    list_filter = ('data_upload',)
    search_fields = ('cliente__nome', 'descricao')
    readonly_fields = ('data_upload',)
