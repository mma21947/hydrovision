from rest_framework import serializers
from .models import Produto, Categoria, UnidadeMedida, MovimentacaoEstoque

class CategoriaSerializer(serializers.ModelSerializer):
    class Meta:
        model = Categoria
        fields = '__all__'

class UnidadeMedidaSerializer(serializers.ModelSerializer):
    class Meta:
        model = UnidadeMedida
        fields = '__all__'

class MovimentacaoEstoqueSerializer(serializers.ModelSerializer):
    produto_nome = serializers.CharField(source='produto.nome', read_only=True)
    tipo_display = serializers.CharField(source='get_tipo_display', read_only=True)
    
    class Meta:
        model = MovimentacaoEstoque
        fields = '__all__'

class ProdutoSerializer(serializers.ModelSerializer):
    categoria_nome = serializers.CharField(source='categoria.nome', read_only=True)
    unidade_nome = serializers.SerializerMethodField()
    ultimas_movimentacoes = MovimentacaoEstoqueSerializer(source='movimentacoes.all', many=True, read_only=True)
    
    class Meta:
        model = Produto
        fields = '__all__'
    
    def get_unidade_nome(self, obj):
        return obj.unidade.nome if obj.unidade else "" 