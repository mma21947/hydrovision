from rest_framework import viewsets, permissions, filters, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from django.utils import timezone
from .models import OrdemServico, Categoria, ProdutoUtilizado, Anexo, Comentario
from .serializers import (
    OrdemServicoSerializer, CategoriaSerializer, 
    ProdutoUtilizadoSerializer, AnexoSerializer, ComentarioSerializer
)

class OrdemServicoViewSet(viewsets.ModelViewSet):
    queryset = OrdemServico.objects.all()
    serializer_class = OrdemServicoSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['status', 'prioridade', 'cliente', 'tecnico', 'categoria', 'ativa']
    search_fields = ['numero', 'descricao', 'cliente__nome', 'tecnico__nome']
    ordering_fields = ['data_abertura', 'data_agendamento', 'prioridade', 'status']
    
    @action(detail=False)
    def abertas(self, request):
        ordens = OrdemServico.objects.filter(ativa=True).exclude(status='concluida').exclude(status='cancelada')
        serializer = self.get_serializer(ordens, many=True)
        return Response(serializer.data)
    
    @action(detail=False)
    def em_andamento(self, request):
        ordens = OrdemServico.objects.filter(status='em_andamento')
        serializer = self.get_serializer(ordens, many=True)
        return Response(serializer.data)
    
    @action(detail=False)
    def urgentes(self, request):
        ordens = OrdemServico.objects.filter(prioridade='urgente', ativa=True).exclude(status='concluida').exclude(status='cancelada')
        serializer = self.get_serializer(ordens, many=True)
        return Response(serializer.data)
    
    @action(detail=False)
    def por_tecnico(self, request):
        tecnico_id = request.query_params.get('tecnico_id', None)
        if not tecnico_id:
            return Response({"error": "Parâmetro tecnico_id é obrigatório"}, status=status.HTTP_400_BAD_REQUEST)
        
        ordens = OrdemServico.objects.filter(tecnico_id=tecnico_id, ativa=True)
        serializer = self.get_serializer(ordens, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['patch'])
    def iniciar_atendimento(self, request, pk=None):
        ordem = self.get_object()
        
        latitude = request.data.get('latitude', None)
        longitude = request.data.get('longitude', None)
        precisao = request.data.get('precisao', None)
        
        try:
            ordem.iniciar_atendimento(latitude, longitude, precisao)
            serializer = self.get_serializer(ordem)
            return Response(serializer.data)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=True, methods=['patch'])
    def finalizar_atendimento(self, request, pk=None):
        ordem = self.get_object()
        
        latitude = request.data.get('latitude', None)
        longitude = request.data.get('longitude', None)
        precisao = request.data.get('precisao', None)
        solucao = request.data.get('solucao', None)
        
        try:
            ordem.finalizar_atendimento(latitude, longitude, precisao, solucao)
            serializer = self.get_serializer(ordem)
            return Response(serializer.data)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=True, methods=['post'])
    def adicionar_comentario(self, request, pk=None):
        ordem = self.get_object()
        
        autor = request.data.get('autor', request.user.username)
        tipo_autor = request.data.get('tipo_autor', 'tecnico')
        texto = request.data.get('texto')
        interno = request.data.get('interno', False)
        
        if not texto:
            return Response({"error": "O texto do comentário é obrigatório"}, status=status.HTTP_400_BAD_REQUEST)
        
        comentario = Comentario.objects.create(
            ordem=ordem,
            autor=autor,
            tipo_autor=tipo_autor,
            texto=texto,
            interno=interno
        )
        
        serializer = ComentarioSerializer(comentario)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

class CategoriaViewSet(viewsets.ModelViewSet):
    queryset = Categoria.objects.all()
    serializer_class = CategoriaSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['nome']
    ordering_fields = ['nome']

class ProdutoUtilizadoViewSet(viewsets.ModelViewSet):
    queryset = ProdutoUtilizado.objects.all()
    serializer_class = ProdutoUtilizadoSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['ordem_servico', 'produto']
    
    @action(detail=False)
    def por_ordem(self, request):
        ordem_id = request.query_params.get('ordem_id', None)
        if not ordem_id:
            return Response({"error": "Parâmetro ordem_id é obrigatório"}, status=status.HTTP_400_BAD_REQUEST)
        
        produtos = ProdutoUtilizado.objects.filter(ordem_servico_id=ordem_id)
        serializer = self.get_serializer(produtos, many=True)
        return Response(serializer.data)

class AnexoViewSet(viewsets.ModelViewSet):
    queryset = Anexo.objects.all()
    serializer_class = AnexoSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['ordem']
    
    @action(detail=False)
    def por_ordem(self, request):
        ordem_id = request.query_params.get('ordem_id', None)
        if not ordem_id:
            return Response({"error": "Parâmetro ordem_id é obrigatório"}, status=status.HTTP_400_BAD_REQUEST)
        
        anexos = Anexo.objects.filter(ordem_id=ordem_id)
        serializer = self.get_serializer(anexos, many=True)
        return Response(serializer.data)

class ComentarioViewSet(viewsets.ModelViewSet):
    queryset = Comentario.objects.all()
    serializer_class = ComentarioSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['ordem', 'autor', 'tipo_autor', 'interno']
    ordering_fields = ['-data_criacao']
    
    @action(detail=False)
    def por_ordem(self, request):
        ordem_id = request.query_params.get('ordem_id', None)
        if not ordem_id:
            return Response({"error": "Parâmetro ordem_id é obrigatório"}, status=status.HTTP_400_BAD_REQUEST)
        
        # Por padrão não retorna comentários internos a menos que especificado
        include_internos = request.query_params.get('include_internos', 'false').lower() == 'true'
        
        if include_internos:
            comentarios = Comentario.objects.filter(ordem_id=ordem_id)
        else:
            comentarios = Comentario.objects.filter(ordem_id=ordem_id, interno=False)
            
        serializer = self.get_serializer(comentarios, many=True)
        return Response(serializer.data) 