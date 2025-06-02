# CyberOS - Sistema de Gestão de Ordens de Serviço

Um sistema moderno e completo para gestão de ordens de serviço, clientes e técnicos, com dashboard de métricas e mapa de técnicos em campo.

## Principais Funcionalidades

- **Dashboard Completo**: Métricas de performance, satisfação do cliente, status das ordens e mapa de técnicos em campo.
- **Gestão de Ordens de Serviço**: Criação, edição, acompanhamento e finalização de ordens de serviço.
- **Gestão de Clientes**: Cadastro completo de clientes pessoas físicas e jurídicas.
- **Gestão de Técnicos**: Cadastro de técnicos, controle de disponibilidade e localização em tempo real.
- **Relatórios e Métricas**: Gráficos e indicadores para acompanhamento da operação.

## Tecnologias Utilizadas

- **Backend**: Python 3.10+ e Django 5.2
- **Banco de Dados**: PostgreSQL
- **Frontend**: HTML5, CSS3, JavaScript, Bootstrap 5
- **Mapeamento**: Leaflet para visualização de mapas
- **Gráficos**: Chart.js para visualizações de dados

## Requisitos

- Python 3.10 ou superior
- PostgreSQL 13 ou superior
- pip (gerenciador de pacotes do Python)
- Ambiente virtual Python (venv)

## Instalação

1. Clone o repositório:
```
git clone https://github.com/seu-usuario/cyberos.git
cd cyberos
```

2. Crie e ative o ambiente virtual:
```
python -m venv venv
# No Windows:
venv\Scripts\Activate
# No Linux/Mac:
source venv/bin/activate
```

3. Instale as dependências:
```
pip install -r requirements.txt
```

4. Configure o banco de dados PostgreSQL:
   - Crie um banco de dados chamado `cyberos_db`
   - Usuário: `postgres`
   - Senha: `postgres`
   - (Ou altere as configurações em `cyberOS/settings.py`)

5. Execute as migrações:
```
python manage.py migrate
```

6. Crie um superusuário:
```
python manage.py createsuperuser
```

7. Inicie o servidor de desenvolvimento:
```
python manage.py runserver
```

8. Acesse o sistema em: http://localhost:8000

## Estrutura do Projeto

- `dashboard/`: Aplicativo para o dashboard principal
- `ordens/`: Aplicativo para gestão de ordens de serviço
- `clientes/`: Aplicativo para gestão de clientes
- `tecnicos/`: Aplicativo para gestão de técnicos
- `templates/`: Templates HTML do sistema
- `static/`: Arquivos estáticos (CSS, JS, imagens)
- `media/`: Arquivos enviados pelos usuários

## Contribuindo

1. Faça um fork do projeto
2. Crie uma branch para sua feature (`git checkout -b feature/nova-feature`)
3. Commit suas mudanças (`git commit -am 'Adiciona nova feature'`)
4. Push para a branch (`git push origin feature/nova-feature`)
5. Crie um Pull Request

## Licença

Este projeto está licenciado sob a licença MIT - veja o arquivo LICENSE para detalhes.

## Contato

Para dúvidas ou sugestões, entre em contato pelo email: exemplo@email.com 