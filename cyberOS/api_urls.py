from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView, TokenVerifyView

# Viewsets dos clientes
from clientes.api import ClienteViewSet, EmpresaViewSet, ContratoClienteViewSet, ContratoEmpresaViewSet

# Viewsets das ordens
from ordens.api import (
    OrdemServicoViewSet, CategoriaViewSet, ProdutoUtilizadoViewSet, 
    AnexoViewSet, ComentarioViewSet
)

# Viewsets dos técnicos
from tecnicos.api import (
    TecnicoViewSet, LocalizacaoAtendimentoViewSet, RegistroPontoViewSet
)

# Viewsets dos equipamentos
from equipamentos.api import EquipamentoViewSet

# Viewsets dos produtos
from produtos.api import ProdutoViewSet

# Configuração do router
router = DefaultRouter()

# Clientes
router.register('clientes', ClienteViewSet)
router.register('empresas', EmpresaViewSet)
router.register('contratos-clientes', ContratoClienteViewSet)
router.register('contratos-empresas', ContratoEmpresaViewSet)

# Ordens
router.register('ordens', OrdemServicoViewSet)
router.register('categorias-os', CategoriaViewSet)
router.register('produtos-utilizados', ProdutoUtilizadoViewSet)
router.register('anexos', AnexoViewSet)
router.register('comentarios', ComentarioViewSet)

# Técnicos
router.register('tecnicos', TecnicoViewSet)
router.register('localizacoes', LocalizacaoAtendimentoViewSet)
router.register('registros-ponto', RegistroPontoViewSet)

# Equipamentos
router.register('equipamentos', EquipamentoViewSet)

# Produtos
router.register('produtos', ProdutoViewSet)

# URLs da API
urlpatterns = [
    path('', include(router.urls)),
    path('auth/', include('rest_framework.urls')),
    
    # Autenticação JWT
    path('token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('token/verify/', TokenVerifyView.as_view(), name='token_verify'),
] 