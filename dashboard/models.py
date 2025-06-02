from django.db import models
from django.utils import timezone
from tecnicos.models import Tecnico
from ordens.models import OrdemServico
from django.db.models import Avg

class MetricaDiaria(models.Model):
    data = models.DateField('Data', unique=True)
    total_ordens = models.IntegerField('Total de Ordens', default=0)
    ordens_abertas = models.IntegerField('Ordens Abertas', default=0)
    ordens_andamento = models.IntegerField('Ordens em Andamento', default=0)
    ordens_aguardando = models.IntegerField('Ordens Aguardando', default=0)
    ordens_concluidas = models.IntegerField('Ordens Concluídas', default=0)
    ordens_canceladas = models.IntegerField('Ordens Canceladas', default=0)
    satisfacao_media = models.DecimalField('Satisfação Média', max_digits=3, decimal_places=2, default=0)
    tempo_medio_atendimento = models.DurationField('Tempo Médio de Atendimento', default=timezone.timedelta())
    faturamento_dia = models.DecimalField('Faturamento do Dia', max_digits=10, decimal_places=2, default=0)
    
    def __str__(self):
        return f"Métricas de {self.data.strftime('%d/%m/%Y')}"
    
    class Meta:
        verbose_name = 'Métrica Diária'
        verbose_name_plural = 'Métricas Diárias'
        ordering = ['-data']
        
    @classmethod
    def gerar_metrica_hoje(cls):
        """Gera ou atualiza as métricas para o dia atual"""
        hoje = timezone.now().date()
        metrica, created = cls.objects.get_or_create(data=hoje)
        
        # Obter ordens
        ordens = OrdemServico.objects.all()
        total_ordens = ordens.count()
        abertas = ordens.filter(status='aberta').count()
        andamento = ordens.filter(status='em_andamento').count()
        aguardando_peca = ordens.filter(status='aguardando_peca').count()
        aguardando_cliente = ordens.filter(status='aguardando_cliente').count()
        concluidas = ordens.filter(status='concluida', data_conclusao__date=hoje).count()
        canceladas = ordens.filter(status='cancelada', data_conclusao__date=hoje).count()
        
        # Calcular satisfação média
        ordens_concluidas = OrdemServico.objects.filter(
            status='concluida',
            data_conclusao__date=hoje
        )
        
        avaliacao_media = 0
        if ordens_concluidas.filter(avaliacao_cliente__isnull=False).exists():
            avaliacao_media = ordens_concluidas.filter(
                avaliacao_cliente__isnull=False
            ).aggregate(
                media=Avg('avaliacao_cliente')
            )['media'] or 0
        
        # Calcular tempo médio de atendimento
        tempo_total = timezone.timedelta()
        qtd_calculados = 0
        
        for ordem in ordens.filter(status='concluida', data_conclusao__date=hoje, data_inicio__isnull=False):
            tempo_total += ordem.data_conclusao - ordem.data_inicio
            qtd_calculados += 1
            
        tempo_medio = timezone.timedelta()
        if qtd_calculados > 0:
            tempo_medio = tempo_total / qtd_calculados
            
        # Calcular faturamento
        faturamento = sum(o.valor_total for o in ordens.filter(status='concluida', data_conclusao__date=hoje))
        
        # Atualizar a métrica
        metrica.total_ordens = total_ordens
        metrica.ordens_abertas = abertas
        metrica.ordens_andamento = andamento
        metrica.ordens_aguardando = aguardando_peca + aguardando_cliente
        metrica.ordens_concluidas = concluidas
        metrica.ordens_canceladas = canceladas
        metrica.satisfacao_media = avaliacao_media
        metrica.tempo_medio_atendimento = tempo_medio
        metrica.faturamento_dia = faturamento
        metrica.save()
        
        return metrica
