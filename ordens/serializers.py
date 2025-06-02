from rest_framework import serializers
from .models import OrdemServico, Categoria, ProdutoUtilizado, Anexo, Comentario
from clientes.serializers import ClienteSerializer
from tecnicos.models import Tecnico

class CategoriaSerializer(serializers.ModelSerializer):
    class Meta:
        model = Categoria
        fields = '__all__'

class ProdutoUtilizadoSerializer(serializers.ModelSerializer):
    produto_nome = serializers.CharField(source='produto.nome', read_only=True)
    
    class Meta:
        model = ProdutoUtilizado
        fields = ['id', 'ordem_servico', 'produto', 'produto_nome', 'quantidade', 'preco_unitario']

class AnexoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Anexo
        fields = '__all__'

class ComentarioSerializer(serializers.ModelSerializer):
    class Meta:
        model = Comentario
        fields = '__all__'

class OrdemServicoSerializer(serializers.ModelSerializer):
    cliente_nome = serializers.CharField(source='cliente.nome', read_only=True)
    tecnico_nome = serializers.CharField(source='tecnico.nome', read_only=True)
    categoria_nome = serializers.CharField(source='categoria.nome', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    prioridade_display = serializers.CharField(source='get_prioridade_display', read_only=True)
    produtos_utilizados = ProdutoUtilizadoSerializer(source='produtos_utilizados.all', many=True, read_only=True)
    anexos = AnexoSerializer(many=True, read_only=True)
    comentarios = serializers.SerializerMethodField()
    dias_aberto = serializers.IntegerField(read_only=True)
    
    class Meta:
        model = OrdemServico
        fields = '__all__'
    
    def get_comentarios(self, obj):
        # Retorna apenas comentários não internos por padrão
        comentarios = obj.comentarios.filter(interno=False)
        return ComentarioSerializer(comentarios, many=True).data
    
    def create(self, validated_data):
        # Se tecnico_id está nos dados, use-o para obter nome e id
        tecnico_id = validated_data.get('tecnico', None)
        if tecnico_id:
            try:
                tecnico = Tecnico.objects.get(id=tecnico_id.id)
                validated_data['id_tecnico'] = tecnico.id
                validated_data['nome_tecnico'] = tecnico.nome
            except Tecnico.DoesNotExist:
                pass
        
        return super().create(validated_data)
    
    def update(self, instance, validated_data):
        # Se tecnico_id está nos dados, use-o para obter nome e id
        tecnico = validated_data.get('tecnico', None)
        if tecnico:
            try:
                tecnico_obj = Tecnico.objects.get(id=tecnico.id)
                validated_data['id_tecnico'] = tecnico_obj.id
                validated_data['nome_tecnico'] = tecnico_obj.nome
            except Tecnico.DoesNotExist:
                pass
        
        return super().update(instance, validated_data) 