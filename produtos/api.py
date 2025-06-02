from rest_framework import viewsets, permissions, filters, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import F
from .models import Produto, Categoria, UnidadeMedida, MovimentacaoEstoque
from .serializers import ProdutoSerializer, CategoriaSerializer, UnidadeMedidaSerializer, MovimentacaoEstoqueSerializer

class ProdutoViewSet(viewsets.ModelViewSet):
    queryset = Produto.objects.all()
    serializer_class = ProdutoSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['categoria', 'ativo']
    search_fields = ['codigo', 'nome', 'descricao', 'fabricante']
    ordering_fields = ['nome', 'preco_venda', 'estoque_atual']
    
    @action(detail=False)
    def em_estoque(self, request):
        produtos = Produto.objects.filter(ativo=True, estoque_atual__gt=0)
        serializer = self.get_serializer(produtos, many=True)
        return Response(serializer.data)
    
    @action(detail=False)
    def baixo_estoque(self, request):
        """Retorna produtos com estoque abaixo do mínimo"""
        produtos = Produto.objects.filter(
            ativo=True,
            estoque_atual__lt=F('estoque_minimo')
        )
        serializer = self.get_serializer(produtos, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def ajustar_estoque(self, request, pk=None):
        produto = self.get_object()
        
        quantidade = request.data.get('quantidade', None)
        motivo = request.data.get('motivo', 'Ajuste manual')
        
        try:
            quantidade = float(quantidade)
        except (ValueError, TypeError):
            return Response({"error": "Quantidade inválida"}, status=status.HTTP_400_BAD_REQUEST)
        
        # Criar movimentação de estoque
        tipo = 'entrada' if quantidade > 0 else 'saida'
        
        MovimentacaoEstoque.objects.create(
            produto=produto,
            tipo=tipo,
            quantidade=abs(quantidade),
            motivo=motivo,
            usuario=request.user.username
        )
        
        # Atualizar estoque
        produto.estoque_atual += quantidade
        produto.save()
        
        serializer = self.get_serializer(produto)
        return Response(serializer.data) 