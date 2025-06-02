from django.contrib import admin
from .models import MetricaDiaria

@admin.register(MetricaDiaria)
class MetricaDiariaAdmin(admin.ModelAdmin):
    list_display = ('data', 'total_ordens', 'ordens_abertas', 'ordens_andamento', 
                    'ordens_aguardando', 'ordens_concluidas', 'ordens_canceladas', 
                    'satisfacao_media', 'faturamento_dia')
    list_filter = ('data',)
    search_fields = ('data',)
    date_hierarchy = 'data'
    readonly_fields = ('data', 'total_ordens', 'ordens_abertas', 'ordens_andamento', 
                      'ordens_aguardando', 'ordens_concluidas', 'ordens_canceladas', 
                      'satisfacao_media', 'tempo_medio_atendimento', 'faturamento_dia')
