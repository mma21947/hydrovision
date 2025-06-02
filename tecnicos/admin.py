from django.contrib import admin
from .models import Tecnico, LocalizacaoAtendimento, RegistroPonto

@admin.register(Tecnico)
class TecnicoAdmin(admin.ModelAdmin):
    list_display = ('nome_completo', 'codigo', 'nivel', 'status', 'celular', 'especialidade', 'ativo')
    list_filter = ('nivel', 'status', 'cidade', 'especialidade', 'ativo')
    search_fields = ('nome_completo', 'codigo', 'cpf', 'email', 'celular')
    readonly_fields = ('data_criacao', 'data_atualizacao', 'ultima_atualizacao_local', 'slug')
    fieldsets = (
        ('Informações de Usuário', {
            'fields': ('usuario',)
        }),
        ('Informações Básicas', {
            'fields': ('codigo', 'nome_completo', 'cpf', 'rg', 'data_nascimento', 'email', 'telefone', 'celular', 'foto')
        }),
        ('Endereço', {
            'fields': ('endereco', 'numero', 'complemento', 'bairro', 'cidade', 'estado', 'cep')
        }),
        ('Localização', {
            'fields': ('latitude', 'longitude', 'ultima_atualizacao_local')
        }),
        ('Informações Profissionais', {
            'fields': ('nivel', 'especialidade', 'status', 'data_admissao', 'data_demissao', 'certificacoes', 'habilidades', 'ativo')
        }),
        ('Metadados', {
            'fields': ('observacoes', 'data_criacao', 'data_atualizacao', 'slug'),
            'classes': ('collapse',)
        }),
    )

@admin.register(LocalizacaoAtendimento)
class LocalizacaoAtendimentoAdmin(admin.ModelAdmin):
    list_display = ('tecnico', 'tipo', 'data_hora')
    list_filter = ('tipo', 'data_hora', 'tecnico')
    search_fields = ('tecnico__nome_completo', 'tecnico__codigo')
    date_hierarchy = 'data_hora'

@admin.register(RegistroPonto)
class RegistroPontoAdmin(admin.ModelAdmin):
    list_display = ('tecnico', 'tipo', 'data_hora', 'localizacao_formatada', 'ip')
    list_filter = ('tipo', 'data_hora', 'tecnico')
    search_fields = ('tecnico__nome_completo', 'tecnico__codigo', 'observacao')
    date_hierarchy = 'data_hora'
