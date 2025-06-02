from rest_framework import viewsets, permissions, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from .models import Equipamento, CategoriaEquipamento, ManutencaoEquipamento
from .serializers import EquipamentoSerializer, CategoriaEquipamentoSerializer, ManutencaoEquipamentoSerializer

class EquipamentoViewSet(viewsets.ModelViewSet):
    queryset = Equipamento.objects.all()
    serializer_class = EquipamentoSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['cliente', 'categoria', 'status', 'ativo']
    search_fields = ['numero_serie', 'modelo', 'fabricante', 'descricao']
    ordering_fields = ['cliente__nome', 'data_aquisicao', 'proxima_manutencao']
    
    @action(detail=False)
    def por_cliente(self, request):
        cliente_id = request.query_params.get('cliente_id', None)
        if not cliente_id:
            return Response({"error": "Parâmetro cliente_id é obrigatório"})
        
        equipamentos = Equipamento.objects.filter(cliente_id=cliente_id, ativo=True)
        serializer = self.get_serializer(equipamentos, many=True)
        return Response(serializer.data) 