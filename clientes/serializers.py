from rest_framework import serializers
from .models import Cliente, Empresa, ContratoCliente, ContratoEmpresa

class EmpresaSerializer(serializers.ModelSerializer):
    class Meta:
        model = Empresa
        fields = '__all__'

class ClienteSerializer(serializers.ModelSerializer):
    empresa_nome = serializers.SerializerMethodField()
    
    class Meta:
        model = Cliente
        fields = '__all__'
    
    def get_empresa_nome(self, obj):
        return obj.empresa.nome if obj.empresa else None

class ContratoClienteSerializer(serializers.ModelSerializer):
    cliente_nome = serializers.SerializerMethodField()
    
    class Meta:
        model = ContratoCliente
        fields = '__all__'
    
    def get_cliente_nome(self, obj):
        return obj.cliente.nome if obj.cliente else None

class ContratoEmpresaSerializer(serializers.ModelSerializer):
    empresa_nome = serializers.SerializerMethodField()
    
    class Meta:
        model = ContratoEmpresa
        fields = '__all__'
    
    def get_empresa_nome(self, obj):
        return obj.empresa.nome if obj.empresa else None 