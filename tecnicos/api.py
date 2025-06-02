from rest_framework import viewsets, permissions, filters, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from django.utils import timezone
from django.db.models import Count, Q
from .models import Tecnico, LocalizacaoAtendimento, RegistroPonto
from .serializers import (
    TecnicoSerializer, LocalizacaoAtendimentoSerializer, RegistroPontoSerializer
)

class TecnicoViewSet(viewsets.ModelViewSet):
    queryset = Tecnico.objects.all()
    serializer_class = TecnicoSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['status', 'nivel', 'ativo']
    search_fields = ['nome_completo', 'codigo', 'cpf', 'email', 'celular']
    ordering_fields = ['nome_completo', 'data_admissao', 'nivel']
    
    @action(detail=False)
    def disponiveis(self, request):
        tecnicos = Tecnico.objects.filter(status='disponivel', ativo=True)
        serializer = self.get_serializer(tecnicos, many=True)
        return Response(serializer.data)
    
    @action(detail=False)
    def em_atendimento(self, request):
        tecnicos = Tecnico.objects.filter(status='em_atendimento', ativo=True)
        serializer = self.get_serializer(tecnicos, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def atualizar_localizacao(self, request, pk=None):
        tecnico = self.get_object()
        
        latitude = request.data.get('latitude', None)
        longitude = request.data.get('longitude', None)
        
        if not latitude or not longitude:
            return Response({"error": "Latitude e longitude são obrigatórios"}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            ordens_atualizadas = tecnico.atualizar_localizacao(latitude, longitude)
            return Response({
                "success": True, 
                "ordens_atualizadas": ordens_atualizadas,
                "tecnico": TecnicoSerializer(tecnico).data
            })
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=True, methods=['get'])
    def ordens(self, request, pk=None):
        tecnico = self.get_object()
        
        from ordens.models import OrdemServico
        from ordens.serializers import OrdemServicoSerializer
        
        # Por padrão retorna ordens em andamento, mas pode ser filtrado
        status_filter = request.query_params.get('status', 'em_andamento')
        
        if status_filter == 'todas':
            ordens = OrdemServico.objects.filter(tecnico=tecnico)
        elif status_filter == 'pendentes':
            ordens = OrdemServico.objects.filter(
                tecnico=tecnico, 
                status__in=['aberta', 'em_andamento', 'aguardando_peca', 'aguardando_cliente']
            )
        else:
            ordens = OrdemServico.objects.filter(tecnico=tecnico, status=status_filter)
            
        serializer = OrdemServicoSerializer(ordens, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def registrar_ponto(self, request, pk=None):
        tecnico = self.get_object()
        
        tipo = request.data.get('tipo', None)
        latitude = request.data.get('latitude', None)
        longitude = request.data.get('longitude', None)
        precisao = request.data.get('precisao', None)
        observacao = request.data.get('observacao', None)
        
        if not tipo:
            return Response({"error": "Tipo de ponto é obrigatório"}, status=status.HTTP_400_BAD_REQUEST)
        
        # Obter o IP do cliente
        ip = request.META.get('REMOTE_ADDR', None)
        
        try:
            registro = RegistroPonto.objects.create(
                tecnico=tecnico,
                tipo=tipo,
                latitude=latitude,
                longitude=longitude,
                precisao=precisao,
                observacao=observacao,
                ip=ip
            )
            
            # Atualizar status do técnico com base no tipo de ponto
            if tipo == 'entrada':
                tecnico.status = 'disponivel'
                tecnico.save()
            elif tipo == 'saida':
                tecnico.status = 'ausente'
                tecnico.save()
                
            serializer = RegistroPontoSerializer(registro)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

class LocalizacaoAtendimentoViewSet(viewsets.ModelViewSet):
    queryset = LocalizacaoAtendimento.objects.all()
    serializer_class = LocalizacaoAtendimentoSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['tecnico', 'ordem_servico', 'tipo']
    ordering_fields = ['-data_hora']
    
    @action(detail=False)
    def por_tecnico(self, request):
        tecnico_id = request.query_params.get('tecnico_id', None)
        if not tecnico_id:
            return Response({"error": "Parâmetro tecnico_id é obrigatório"}, status=status.HTTP_400_BAD_REQUEST)
        
        localizacoes = LocalizacaoAtendimento.objects.filter(tecnico_id=tecnico_id)
        serializer = self.get_serializer(localizacoes, many=True)
        return Response(serializer.data)
    
    @action(detail=False)
    def por_ordem(self, request):
        ordem_id = request.query_params.get('ordem_id', None)
        if not ordem_id:
            return Response({"error": "Parâmetro ordem_id é obrigatório"}, status=status.HTTP_400_BAD_REQUEST)
        
        localizacoes = LocalizacaoAtendimento.objects.filter(ordem_servico_id=ordem_id)
        serializer = self.get_serializer(localizacoes, many=True)
        return Response(serializer.data)

class RegistroPontoViewSet(viewsets.ModelViewSet):
    queryset = RegistroPonto.objects.all()
    serializer_class = RegistroPontoSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['tecnico', 'tipo']
    ordering_fields = ['-data_hora']
    
    @action(detail=False)
    def por_tecnico(self, request):
        tecnico_id = request.query_params.get('tecnico_id', None)
        if not tecnico_id:
            return Response({"error": "Parâmetro tecnico_id é obrigatório"}, status=status.HTTP_400_BAD_REQUEST)
        
        # Opcionalmente filtrar por data
        data_inicio = request.query_params.get('data_inicio', None)
        data_fim = request.query_params.get('data_fim', None)
        
        registros = RegistroPonto.objects.filter(tecnico_id=tecnico_id)
        
        if data_inicio:
            registros = registros.filter(data_hora__gte=data_inicio)
        if data_fim:
            registros = registros.filter(data_hora__lte=data_fim)
            
        serializer = self.get_serializer(registros, many=True)
        return Response(serializer.data)
    
    @action(detail=False)
    def hoje(self, request):
        tecnico_id = request.query_params.get('tecnico_id', None)
        
        hoje = timezone.now().date()
        registros = RegistroPonto.objects.filter(
            data_hora__date=hoje
        )
        
        if tecnico_id:
            registros = registros.filter(tecnico_id=tecnico_id)
            
        serializer = self.get_serializer(registros, many=True)
        return Response(serializer.data) 