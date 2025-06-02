# Guia para Criar uma API para o Aplicativo Móvel do CyberOS

Este guia explica como criar uma API REST para que seu aplicativo móvel possa se conectar ao banco de dados PostgreSQL do CyberOS.

## 1. Instalação das Dependências

Primeiro, instale o Django REST Framework no ambiente virtual:

```bash
source venv_new/bin/activate
pip install djangorestframework
pip install django-cors-headers
```

## 2. Configuração do Django

Adicione as seguintes aplicações ao arquivo `cyberOS/settings.py`:

```python
INSTALLED_APPS = [
    # ... suas aplicações atuais ...
    'rest_framework',
    'corsheaders',
]

MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware',  # Adicione esta linha no início da lista
    # ... seus middleware atuais ...
]

# Configurações do REST Framework
REST_FRAMEWORK = {
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated',
    ],
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework.authentication.TokenAuthentication',
        'rest_framework.authentication.SessionAuthentication',
    ],
}

# Permitir CORS para o aplicativo móvel
CORS_ALLOW_ALL_ORIGINS = True  # Em produção, defina apenas as origens específicas
```

## 3. Criando APIs para suas Aplicações

Para cada aplicação do Django que você deseja expor para o aplicativo móvel, crie um arquivo `api.py`:

### Exemplo para Clientes

Crie o arquivo `clientes/api.py`:

```python
from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from .models import Cliente
from .serializers import ClienteSerializer

class ClienteViewSet(viewsets.ModelViewSet):
    queryset = Cliente.objects.all()
    serializer_class = ClienteSerializer
    permission_classes = [IsAuthenticated]
```

### Criando Serializadores

Crie o arquivo `clientes/serializers.py`:

```python
from rest_framework import serializers
from .models import Cliente

class ClienteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Cliente
        fields = '__all__'
```

### Configurando URLs da API

Crie um arquivo `cyberOS/api_urls.py`:

```python
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from clientes.api import ClienteViewSet
# Importe outros ViewSets conforme necessário

router = DefaultRouter()
router.register('clientes', ClienteViewSet)
# Registre outros ViewSets conforme necessário

urlpatterns = [
    path('', include(router.urls)),
    path('auth/', include('rest_framework.urls')),
]
```

Adicione a URL da API ao arquivo `cyberOS/urls.py`:

```python
urlpatterns = [
    # ... suas URLs atuais ...
    path('api/', include('cyberOS.api_urls')),
]
```

## 4. Autenticação para o Aplicativo Móvel

Adicione autenticação por token:

```bash
pip install djangorestframework-simplejwt
```

Atualize as configurações em `settings.py`:

```python
INSTALLED_APPS = [
    # ... suas aplicações atuais ...
    'rest_framework_simplejwt',
]

REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework_simplejwt.authentication.JWTAuthentication',
        'rest_framework.authentication.SessionAuthentication',
    ],
}

# Configurações JWT
from datetime import timedelta
SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(hours=1),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=1),
}
```

Adicione URLs para obter tokens:

```python
# Em cyberOS/api_urls.py
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

urlpatterns = [
    # ... suas URLs da API ...
    path('token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
]
```

## 5. Implementação no Aplicativo Móvel

No seu aplicativo móvel, configure a conexão à API:

### Para Android (Kotlin):

```kotlin
// Exemplo usando Retrofit
val retrofit = Retrofit.Builder()
    .baseUrl("http://192.168.15.69:8080/api/")
    .addConverterFactory(GsonConverterFactory.create())
    .build()

val api = retrofit.create(ApiService::class.java)

// Interface de serviço
interface ApiService {
    @POST("token/")
    fun login(@Body loginRequest: LoginRequest): Call<TokenResponse>
    
    @GET("clientes/")
    fun getClientes(@Header("Authorization") token: String): Call<List<Cliente>>
}
```

### Para iOS (Swift):

```swift
// Configuração da URL base
let baseURL = "http://192.168.15.69:8080/api/"

// Exemplo de login
func login(username: String, password: String, completion: @escaping (Result<String, Error>) -> Void) {
    let url = URL(string: baseURL + "token/")!
    var request = URLRequest(url: url)
    request.httpMethod = "POST"
    request.addValue("application/json", forHTTPHeaderField: "Content-Type")
    
    let body: [String: Any] = ["username": username, "password": password]
    request.httpBody = try? JSONSerialization.data(withJSONObject: body)
    
    URLSession.shared.dataTask(with: request) { data, response, error in
        // Processa os dados de resposta
    }.resume()
}
```

## 6. Segurança

Para ambiente de produção, certifique-se de:

1. Usar HTTPS para todas as conexões API
2. Limitar origens CORS específicas
3. Implementar limitação de taxa
4. Usar senhas fortes para o banco de dados
5. Configurar firewalls para limitar o acesso ao banco de dados

## 7. Testando sua API

Use o Postman ou qualquer cliente REST para testar sua API antes de integrá-la ao aplicativo móvel:

1. Obtenha um token: POST http://192.168.15.69:8080/api/token/
2. Use o token para acessar recursos: GET http://192.168.15.69:8080/api/clientes/ 