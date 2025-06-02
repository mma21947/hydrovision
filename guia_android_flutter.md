# Guia para Desenvolvimento do Aplicativo Flutter para o CyberOS

Este guia explica como criar um aplicativo móvel usando Flutter para se comunicar com a API REST do CyberOS.

## 1. Instalação do Flutter

Siga as instruções oficiais para instalar o Flutter em seu sistema:
[https://flutter.dev/docs/get-started/install](https://flutter.dev/docs/get-started/install)

## 2. Criação do Projeto

```bash
flutter create cyberos_app
cd cyberos_app
```

## 3. Pacotes Necessários

Adicione as dependências no arquivo `pubspec.yaml`:

```yaml
dependencies:
  flutter:
    sdk: flutter
  http: ^1.2.0
  provider: ^6.1.1
  flutter_secure_storage: ^9.0.0
  intl: ^0.19.0
  geolocator: ^10.1.0
  url_launcher: ^6.2.4
  image_picker: ^1.0.7
  file_picker: ^6.1.1
  flutter_map: ^6.1.0
  latlong2: ^0.9.0
```

Execute o comando para obter as dependências:

```bash
flutter pub get
```

## 4. Configuração da API

Crie um arquivo `lib/config/api_config.dart`:

```dart
class ApiConfig {
  static const String baseUrl = 'http://192.168.15.69:8080/api/';
  static const String loginUrl = '${baseUrl}token/';
  static const String refreshUrl = '${baseUrl}token/refresh/';
  
  // Endpoints
  static const String clientes = '${baseUrl}clientes/';
  static const String ordens = '${baseUrl}ordens/';
  static const String tecnicos = '${baseUrl}tecnicos/';
  static const String equipamentos = '${baseUrl}equipamentos/';
  static const String produtos = '${baseUrl}produtos/';
}
```

## 5. Serviço de Autenticação

Crie um arquivo `lib/services/auth_service.dart`:

```dart
import 'dart:convert';
import 'package:flutter_secure_storage/flutter_secure_storage.dart';
import 'package:http/http.dart' as http;
import '../config/api_config.dart';

class AuthService {
  final storage = FlutterSecureStorage();
  
  Future<bool> login(String username, String password) async {
    try {
      final response = await http.post(
        Uri.parse(ApiConfig.loginUrl),
        headers: {'Content-Type': 'application/json'},
        body: jsonEncode({
          'username': username,
          'password': password
        }),
      );
      
      if (response.statusCode == 200) {
        final data = jsonDecode(response.body);
        await storage.write(key: 'access_token', value: data['access']);
        await storage.write(key: 'refresh_token', value: data['refresh']);
        return true;
      } else {
        return false;
      }
    } catch (e) {
      print('Erro ao fazer login: $e');
      return false;
    }
  }
  
  Future<void> logout() async {
    await storage.delete(key: 'access_token');
    await storage.delete(key: 'refresh_token');
  }
  
  Future<String?> getToken() async {
    return await storage.read(key: 'access_token');
  }
  
  Future<bool> isLoggedIn() async {
    final token = await getToken();
    return token != null && token.isNotEmpty;
  }
  
  Future<String?> refreshToken() async {
    final refreshToken = await storage.read(key: 'refresh_token');
    if (refreshToken == null) return null;
    
    try {
      final response = await http.post(
        Uri.parse(ApiConfig.refreshUrl),
        headers: {'Content-Type': 'application/json'},
        body: jsonEncode({'refresh': refreshToken}),
      );
      
      if (response.statusCode == 200) {
        final data = jsonDecode(response.body);
        await storage.write(key: 'access_token', value: data['access']);
        return data['access'];
      } else {
        return null;
      }
    } catch (e) {
      print('Erro ao atualizar token: $e');
      return null;
    }
  }
}
```

## 6. Cliente HTTP com Interceptor

Crie um arquivo `lib/services/api_client.dart`:

```dart
import 'dart:convert';
import 'package:http/http.dart' as http;
import 'auth_service.dart';

class ApiClient {
  final AuthService authService = AuthService();
  
  Future<http.Response> get(String url) async {
    final token = await authService.getToken();
    final response = await http.get(
      Uri.parse(url),
      headers: {
        'Content-Type': 'application/json',
        'Authorization': 'Bearer $token',
      },
    );
    
    if (response.statusCode == 401) {
      // Token expirado, tentar atualizar
      final newToken = await authService.refreshToken();
      if (newToken != null) {
        // Repetir a requisição com o novo token
        return await http.get(
          Uri.parse(url),
          headers: {
            'Content-Type': 'application/json',
            'Authorization': 'Bearer $newToken',
          },
        );
      }
    }
    
    return response;
  }
  
  Future<http.Response> post(String url, {Map<String, dynamic>? body}) async {
    final token = await authService.getToken();
    final response = await http.post(
      Uri.parse(url),
      headers: {
        'Content-Type': 'application/json',
        'Authorization': 'Bearer $token',
      },
      body: jsonEncode(body),
    );
    
    if (response.statusCode == 401) {
      // Token expirado, tentar atualizar
      final newToken = await authService.refreshToken();
      if (newToken != null) {
        // Repetir a requisição com o novo token
        return await http.post(
          Uri.parse(url),
          headers: {
            'Content-Type': 'application/json',
            'Authorization': 'Bearer $newToken',
          },
          body: jsonEncode(body),
        );
      }
    }
    
    return response;
  }
  
  Future<http.Response> patch(String url, {Map<String, dynamic>? body}) async {
    final token = await authService.getToken();
    final response = await http.patch(
      Uri.parse(url),
      headers: {
        'Content-Type': 'application/json',
        'Authorization': 'Bearer $token',
      },
      body: jsonEncode(body),
    );
    
    if (response.statusCode == 401) {
      final newToken = await authService.refreshToken();
      if (newToken != null) {
        return await http.patch(
          Uri.parse(url),
          headers: {
            'Content-Type': 'application/json',
            'Authorization': 'Bearer $newToken',
          },
          body: jsonEncode(body),
        );
      }
    }
    
    return response;
  }
}
```

## 7. Serviços para Acesso aos Endpoints

### Service de Ordens de Serviço

Crie um arquivo `lib/services/ordem_service.dart`:

```dart
import 'dart:convert';
import '../config/api_config.dart';
import '../models/ordem.dart';
import 'api_client.dart';

class OrdemService {
  final ApiClient _apiClient = ApiClient();
  
  Future<List<Ordem>> getOrdensPorTecnico(int tecnicoId) async {
    final response = await _apiClient.get('${ApiConfig.ordens}por_tecnico/?tecnico_id=$tecnicoId');
    
    if (response.statusCode == 200) {
      final List<dynamic> data = jsonDecode(response.body);
      return data.map((item) => Ordem.fromJson(item)).toList();
    } else {
      throw Exception('Falha ao carregar ordens');
    }
  }
  
  Future<Ordem> getOrdem(int id) async {
    final response = await _apiClient.get('${ApiConfig.ordens}$id/');
    
    if (response.statusCode == 200) {
      return Ordem.fromJson(jsonDecode(response.body));
    } else {
      throw Exception('Falha ao carregar ordem');
    }
  }
  
  Future<bool> iniciarAtendimento(int ordemId, double latitude, double longitude) async {
    final response = await _apiClient.patch(
      '${ApiConfig.ordens}$ordemId/iniciar_atendimento/',
      body: {
        'latitude': latitude,
        'longitude': longitude,
      },
    );
    
    return response.statusCode == 200;
  }
  
  Future<bool> finalizarAtendimento(int ordemId, double latitude, double longitude, String solucao) async {
    final response = await _apiClient.patch(
      '${ApiConfig.ordens}$ordemId/finalizar_atendimento/',
      body: {
        'latitude': latitude,
        'longitude': longitude,
        'solucao': solucao,
      },
    );
    
    return response.statusCode == 200;
  }
  
  Future<bool> adicionarComentario(int ordemId, String texto) async {
    final response = await _apiClient.post(
      '${ApiConfig.ordens}$ordemId/adicionar_comentario/',
      body: {
        'texto': texto,
        'tipo_autor': 'tecnico',
      },
    );
    
    return response.statusCode == 201;
  }
}
```

### Service de Técnicos

Crie um arquivo `lib/services/tecnico_service.dart`:

```dart
import 'dart:convert';
import '../config/api_config.dart';
import '../models/tecnico.dart';
import 'api_client.dart';

class TecnicoService {
  final ApiClient _apiClient = ApiClient();
  
  Future<Tecnico> getTecnico(int id) async {
    final response = await _apiClient.get('${ApiConfig.tecnicos}$id/');
    
    if (response.statusCode == 200) {
      return Tecnico.fromJson(jsonDecode(response.body));
    } else {
      throw Exception('Falha ao carregar técnico');
    }
  }
  
  Future<bool> atualizarLocalizacao(int tecnicoId, double latitude, double longitude) async {
    final response = await _apiClient.post(
      '${ApiConfig.tecnicos}$tecnicoId/atualizar_localizacao/',
      body: {
        'latitude': latitude,
        'longitude': longitude,
      },
    );
    
    return response.statusCode == 200;
  }
  
  Future<bool> registrarPonto(int tecnicoId, String tipo, double latitude, double longitude) async {
    final response = await _apiClient.post(
      '${ApiConfig.tecnicos}$tecnicoId/registrar_ponto/',
      body: {
        'tipo': tipo,
        'latitude': latitude,
        'longitude': longitude,
      },
    );
    
    return response.statusCode == 201;
  }
}
```

## 8. Modelos de Dados

### Modelo de Ordem de Serviço

```dart
class Ordem {
  final int id;
  final String numero;
  final String clienteNome;
  final String descricao;
  final String status;
  final String statusDisplay;
  final String prioridade;
  final String prioridadeDisplay;
  final String dataAbertura;
  final String? dataAgendamento;
  final String? dataInicio;
  final String? dataConclusao;
  final String? solucao;
  final double valorTotal;
  
  Ordem({
    required this.id,
    required this.numero,
    required this.clienteNome,
    required this.descricao,
    required this.status,
    required this.statusDisplay,
    required this.prioridade,
    required this.prioridadeDisplay,
    required this.dataAbertura,
    this.dataAgendamento,
    this.dataInicio,
    this.dataConclusao,
    this.solucao,
    required this.valorTotal,
  });
  
  factory Ordem.fromJson(Map<String, dynamic> json) {
    return Ordem(
      id: json['id'],
      numero: json['numero'],
      clienteNome: json['cliente_nome'],
      descricao: json['descricao'],
      status: json['status'],
      statusDisplay: json['status_display'],
      prioridade: json['prioridade'],
      prioridadeDisplay: json['prioridade_display'],
      dataAbertura: json['data_abertura'],
      dataAgendamento: json['data_agendamento'],
      dataInicio: json['data_inicio'],
      dataConclusao: json['data_conclusao'],
      solucao: json['solucao'],
      valorTotal: json['valor_total'].toDouble(),
    );
  }
}
```

### Modelo de Técnico

```dart
class Tecnico {
  final int id;
  final String codigo;
  final String nomeCompleto;
  final String email;
  final String celular;
  final String status;
  final String statusDisplay;
  final String nivel;
  final String nivelDisplay;
  final double? latitude;
  final double? longitude;
  
  Tecnico({
    required this.id,
    required this.codigo,
    required this.nomeCompleto,
    required this.email,
    required this.celular,
    required this.status,
    required this.statusDisplay,
    required this.nivel,
    required this.nivelDisplay,
    this.latitude,
    this.longitude,
  });
  
  factory Tecnico.fromJson(Map<String, dynamic> json) {
    return Tecnico(
      id: json['id'],
      codigo: json['codigo'],
      nomeCompleto: json['nome_completo'],
      email: json['email'],
      celular: json['celular'],
      status: json['status'],
      statusDisplay: json['status_display'],
      nivel: json['nivel'],
      nivelDisplay: json['nivel_display'],
      latitude: json['latitude']?.toDouble(),
      longitude: json['longitude']?.toDouble(),
    );
  }
}
```

## 9. Exemplos de Telas

### Tela de Login

```dart
import 'package:flutter/material.dart';
import '../services/auth_service.dart';

class LoginScreen extends StatefulWidget {
  @override
  _LoginScreenState createState() => _LoginScreenState();
}

class _LoginScreenState extends State<LoginScreen> {
  final _formKey = GlobalKey<FormState>();
  final _usernameController = TextEditingController();
  final _passwordController = TextEditingController();
  final _authService = AuthService();
  bool _isLoading = false;
  
  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: Text('CyberOS - Login')),
      body: Padding(
        padding: const EdgeInsets.all(16.0),
        child: Form(
          key: _formKey,
          child: Column(
            mainAxisAlignment: MainAxisAlignment.center,
            children: [
              Image.asset('assets/logo.png', height: 100),
              SizedBox(height: 20),
              TextFormField(
                controller: _usernameController,
                decoration: InputDecoration(
                  labelText: 'Usuário',
                  border: OutlineInputBorder(),
                ),
                validator: (value) {
                  if (value == null || value.isEmpty) {
                    return 'Por favor, informe o usuário';
                  }
                  return null;
                },
              ),
              SizedBox(height: 16),
              TextFormField(
                controller: _passwordController,
                decoration: InputDecoration(
                  labelText: 'Senha',
                  border: OutlineInputBorder(),
                ),
                obscureText: true,
                validator: (value) {
                  if (value == null || value.isEmpty) {
                    return 'Por favor, informe a senha';
                  }
                  return null;
                },
              ),
              SizedBox(height: 24),
              ElevatedButton(
                onPressed: _isLoading ? null : _login,
                child: _isLoading
                    ? CircularProgressIndicator(color: Colors.white)
                    : Text('Entrar'),
                style: ElevatedButton.styleFrom(
                  minimumSize: Size(double.infinity, 50),
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }
  
  Future<void> _login() async {
    if (_formKey.currentState!.validate()) {
      setState(() => _isLoading = true);
      
      try {
        final success = await _authService.login(
          _usernameController.text.trim(),
          _passwordController.text,
        );
        
        if (success) {
          Navigator.of(context).pushReplacementNamed('/home');
        } else {
          ScaffoldMessenger.of(context).showSnackBar(
            SnackBar(content: Text('Usuário ou senha inválidos')),
          );
        }
      } catch (e) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text('Erro ao fazer login: $e')),
        );
      } finally {
        setState(() => _isLoading = false);
      }
    }
  }
}
```

## 10. Geolocalização e Mapas

Para implementar a atualização de localização dos técnicos e o registro de pontos:

```dart
import 'package:geolocator/geolocator.dart';
import '../services/tecnico_service.dart';

class LocationManager {
  final TecnicoService _tecnicoService = TecnicoService();
  
  Future<Position> _getCurrentPosition() async {
    bool serviceEnabled = await Geolocator.isLocationServiceEnabled();
    if (!serviceEnabled) {
      throw Exception('Serviços de localização desabilitados');
    }
    
    LocationPermission permission = await Geolocator.checkPermission();
    if (permission == LocationPermission.denied) {
      permission = await Geolocator.requestPermission();
      if (permission == LocationPermission.denied) {
        throw Exception('Permissão de localização negada');
      }
    }
    
    if (permission == LocationPermission.deniedForever) {
      throw Exception('Permissão de localização negada permanentemente');
    }
    
    return await Geolocator.getCurrentPosition();
  }
  
  Future<bool> atualizarLocalizacaoTecnico(int tecnicoId) async {
    try {
      final position = await _getCurrentPosition();
      return await _tecnicoService.atualizarLocalizacao(
        tecnicoId,
        position.latitude,
        position.longitude,
      );
    } catch (e) {
      print('Erro ao atualizar localização: $e');
      return false;
    }
  }
  
  Future<bool> registrarPonto(int tecnicoId, String tipo) async {
    try {
      final position = await _getCurrentPosition();
      return await _tecnicoService.registrarPonto(
        tecnicoId,
        tipo,
        position.latitude,
        position.longitude,
      );
    } catch (e) {
      print('Erro ao registrar ponto: $e');
      return false;
    }
  }
}
```

## 11. Estrutura do Projeto

Organize seu código com a seguinte estrutura:

```
lib/
├── config/
│   └── api_config.dart
├── models/
│   ├── ordem.dart
│   ├── tecnico.dart
│   ├── cliente.dart
│   └── produto.dart
├── services/
│   ├── api_client.dart
│   ├── auth_service.dart
│   ├── ordem_service.dart
│   ├── tecnico_service.dart
│   └── cliente_service.dart
├── screens/
│   ├── login_screen.dart
│   ├── home_screen.dart
│   ├── ordens_screen.dart
│   ├── ordem_detalhes_screen.dart
│   └── perfil_screen.dart
├── widgets/
│   ├── ordem_card.dart
│   ├── mapa_widget.dart
│   └── comentario_widget.dart
├── utils/
│   ├── location_manager.dart
│   └── formatters.dart
└── main.dart
```

## 12. Considerações de Segurança

1. Sempre use HTTPS em ambiente de produção
2. Armazene tokens de forma segura com o flutter_secure_storage
3. Implemente timeout para sessões inativas
4. Não armazene dados sensíveis localmente sem criptografia
5. Implemente a atualização de tokens com o refresh token
6. Sanitize todos os dados de entrada do usuário antes de enviar para a API

## 13. Testes e Publicação

1. Teste offline/online handling
2. Implemente suporte para vários tamanhos de tela
3. Otimize o uso de bateria, especialmente para GPS
4. Garanta compatibilidade com versões mais antigas do Android (mínimo API 21)
5. Para publicação na Play Store, prepare privacidade e termos de uso 