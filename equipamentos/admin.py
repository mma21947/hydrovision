from django.contrib import admin
from .models import Equipamento, CategoriaEquipamento, ManutencaoEquipamento

class ManutencaoEquipamentoInline(admin.TabularInline):
    model = ManutencaoEquipamento
    extra = 0
    fields = ('tipo', 'data', 'descricao', 'responsavel', 'ordem_servico')
    
@admin.register(Equipamento)
class EquipamentoAdmin(admin.ModelAdmin):
    list_display = ('codigo', 'nome', 'cliente', 'marca', 'modelo', 'status', 'data_cadastro')
    list_filter = ('status', 'categoria', 'cliente')
    search_fields = ('codigo', 'nome', 'numero_serie', 'cliente__nome')
    readonly_fields = ('codigo', 'data_cadastro', 'ultima_atualizacao')
    fieldsets = (
        ('Identificação', {
            'fields': ('codigo', 'nome', 'categoria', 'cliente', 'slug')
        }),
        ('Informações do Equipamento', {
            'fields': ('marca', 'modelo', 'numero_serie', 'especificacoes_tecnicas', 'foto', 'manual')
        }),
        ('Datas', {
            'fields': ('data_aquisicao', 'data_instalacao', 'data_garantia_fim', 'data_cadastro', 'ultima_atualizacao')
        }),
        ('Status e Localização', {
            'fields': ('status', 'local_instalacao', 'descricao', 'observacoes')
        }),
    )
    inlines = [ManutencaoEquipamentoInline]
    
@admin.register(CategoriaEquipamento)
class CategoriaEquipamentoAdmin(admin.ModelAdmin):
    list_display = ('nome', 'count_equipamentos')
    search_fields = ('nome',)
    prepopulated_fields = {'slug': ('nome',)}
    
    def count_equipamentos(self, obj):
        return obj.equipamentos.count()
    count_equipamentos.short_description = 'Qtd. Equipamentos'
    
@admin.register(ManutencaoEquipamento)
class ManutencaoEquipamentoAdmin(admin.ModelAdmin):
    list_display = ('equipamento', 'tipo', 'data', 'responsavel', 'ordem_servico')
    list_filter = ('tipo', 'data')
    search_fields = ('equipamento__nome', 'descricao', 'responsavel')
    date_hierarchy = 'data'
