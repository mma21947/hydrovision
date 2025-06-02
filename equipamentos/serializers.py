from rest_framework import serializers
from .models import Equipamento, CategoriaEquipamento, ManutencaoEquipamento

class CategoriaEquipamentoSerializer(serializers.ModelSerializer):
    class Meta:
        model = CategoriaEquipamento
        fields = '__all__'

class ManutencaoEquipamentoSerializer(serializers.ModelSerializer):
    class Meta:
        model = ManutencaoEquipamento
        fields = '__all__'

class EquipamentoSerializer(serializers.ModelSerializer):
    cliente_nome = serializers.CharField(source='cliente.nome', read_only=True)
    categoria_nome = serializers.CharField(source='categoria.nome', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    proxima_manutencao_formatada = serializers.DateField(source='proxima_manutencao', format='%d/%m/%Y', read_only=True)
    
    class Meta:
        model = Equipamento
        fields = '__all__' 