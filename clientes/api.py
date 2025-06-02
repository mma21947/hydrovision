from rest_framework import viewsets, permissions, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from .models import Cliente, Empresa, ContratoCliente, ContratoEmpresa
from .serializers import ClienteSerializer, EmpresaSerializer, ContratoClienteSerializer, ContratoEmpresaSerializer

class ClienteViewSet(viewsets.ModelViewSet):
    queryset = Cliente.objects.all()
    serializer_class = ClienteSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['tipo', 'ativo', 'empresa']
    search_fields = ['nome', 'cpf_cnpj', 'email', 'telefone', 'celular']
    ordering_fields = ['nome', 'data_criacao', 'codigo']
    
    @action(detail=False)
    def ativos(self, request):
        clientes = Cliente.objects.filter(ativo=True)
        serializer = self.get_serializer(clientes, many=True)
        return Response(serializer.data)

class EmpresaViewSet(viewsets.ModelViewSet):
    queryset = Empresa.objects.all()
    serializer_class = EmpresaSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['ativo']
    search_fields = ['nome', 'nome_fantasia', 'cnpj', 'email']
    ordering_fields = ['nome', 'data_criacao']
    
    @action(detail=False)
    def ativas(self, request):
        empresas = Empresa.objects.filter(ativo=True)
        serializer = self.get_serializer(empresas, many=True)
        return Response(serializer.data)

class ContratoClienteViewSet(viewsets.ModelViewSet):
    queryset = ContratoCliente.objects.all()
    serializer_class = ContratoClienteSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['cliente']
    search_fields = ['descricao']
    ordering_fields = ['data_upload']

class ContratoEmpresaViewSet(viewsets.ModelViewSet):
    queryset = ContratoEmpresa.objects.all()
    serializer_class = ContratoEmpresaSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['empresa', 'ativo']
    search_fields = ['descricao']
    ordering_fields = ['data_inicio', 'valor_mensal'] 