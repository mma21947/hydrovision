from rest_framework import serializers
from .models import Tecnico, LocalizacaoAtendimento, RegistroPonto
from django.contrib.auth.models import User

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name']
        read_only_fields = ['id']

class TecnicoSerializer(serializers.ModelSerializer):
    usuario_info = UserSerializer(source='usuario', read_only=True)
    nivel_display = serializers.CharField(source='get_nivel_display', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    ordens_em_andamento = serializers.SerializerMethodField()
    
    class Meta:
        model = Tecnico
        fields = '__all__'
    
    def get_ordens_em_andamento(self, obj):
        # Retorna a contagem de ordens em andamento deste técnico
        from ordens.models import OrdemServico
        return OrdemServico.objects.filter(tecnico=obj, status='em_andamento').count()

class LocalizacaoAtendimentoSerializer(serializers.ModelSerializer):
    tecnico_nome = serializers.CharField(source='tecnico.nome_completo', read_only=True)
    ordem_numero = serializers.CharField(source='ordem_servico.numero', read_only=True)
    tipo_display = serializers.CharField(source='get_tipo_display', read_only=True)
    
    class Meta:
        model = LocalizacaoAtendimento
        fields = '__all__'

class RegistroPontoSerializer(serializers.ModelSerializer):
    tecnico_nome = serializers.CharField(source='tecnico.nome_completo', read_only=True)
    tipo_display = serializers.CharField(source='get_tipo_display', read_only=True)
    
    class Meta:
        model = RegistroPonto
        fields = '__all__'
        read_only_fields = ['ip'] # O IP será preenchido automaticamente pelo backend 