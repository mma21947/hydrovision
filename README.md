# CyberOS - Sistema de Gestão de Ordens de Serviço

Um sistema moderno e completo para gestão de ordens de serviço, clientes e técnicos, com dashboard de métricas e mapa de técnicos em campo.

## Principais Funcionalidades

- **Dashboard Completo**: Métricas de performance, satisfação do cliente, status das ordens e mapa de técnicos em campo.
- **Gestão de Ordens de Serviço**: Criação, edição, acompanhamento e finalização de ordens de serviço.
- **Gestão de Clientes**: Cadastro completo de clientes pessoas físicas e jurídicas.
- **Gestão de Técnicos**: Cadastro de técnicos, controle de disponibilidade e localização em tempo real.
- **Relatórios e Métricas**: Gráficos e indicadores para acompanhamento da operação.
- **Sistema de Permissões**: Controle de acesso baseado em perfis de usuário (administrador, técnico).
- **Interface Responsiva**: Design moderno e adaptável para dispositivos móveis e desktop.

## Tecnologias Utilizadas

- **Backend**: Python 3.10+ e Django 5.2
- **Banco de Dados**: PostgreSQL / SQLite
- **Frontend**: HTML5, CSS3, JavaScript, Bootstrap 5
- **Mapeamento**: Leaflet para visualização de mapas
- **Gráficos**: Chart.js para visualizações de dados
- **Assinatura Digital**: SignaturePad para captura de assinaturas

## Requisitos

- Python 3.10 ou superior
- PostgreSQL 13 ou superior (ou SQLite para desenvolvimento)
- pip (gerenciador de pacotes do Python)
- Ambiente virtual Python (venv)

## Instalação

1. Clone o repositório:
```bash
git clone https://github.com/mma21947/hydrovision.git
cd hydrovision
```

2. Crie e ative o ambiente virtual:
```bash
python -m venv venv
# No Windows:
venv\Scripts\activate
# No Linux/Mac:
source venv/bin/activate
```

3. Instale as dependências:
```bash
pip install -r requirements.txt
```

4. Configure o banco de dados:
   - **Para desenvolvimento (SQLite)**: O banco será criado automaticamente
   - **Para produção (PostgreSQL)**:
     - Crie um banco de dados chamado `cyberos_db`
     - Usuário: `postgres`
     - Senha: `postgres`
     - (Ou altere as configurações em `cyberOS/settings.py`)

5. Execute as migrações:
```bash
python manage.py migrate
```

6. Crie um superusuário:
```bash
python manage.py createsuperuser
```

7. Inicie o servidor de desenvolvimento:
```bash
python manage.py runserver
```

8. Acesse o sistema em: http://localhost:8000

## Estrutura do Projeto

- `dashboard/`: Aplicativo para o dashboard principal
- `ordens/`: Aplicativo para gestão de ordens de serviço
- `clientes/`: Aplicativo para gestão de clientes
- `tecnicos/`: Aplicativo para gestão de técnicos
- `produtos/`: Aplicativo para gestão de produtos e estoque
- `equipamentos/`: Aplicativo para gestão de equipamentos
- `usuarios/`: Aplicativo para gestão de usuários e permissões
- `relatorios/`: Aplicativo para geração de relatórios
- `templates/`: Templates HTML do sistema
- `static/`: Arquivos estáticos (CSS, JS, imagens)
- `media/`: Arquivos enviados pelos usuários

## Funcionalidades Principais

### Dashboard
- Métricas em tempo real
- Gráficos de performance
- Mapa de técnicos em campo
- Indicadores de satisfação do cliente

### Ordens de Serviço
- Criação e edição de ordens
- Controle de status e prioridade
- Sistema de comentários
- Anexos e documentos
- Assinatura digital do cliente
- Controle de produtos utilizados

### Gestão de Clientes
- Cadastro completo (PF/PJ)
- Histórico de atendimentos
- Contratos e equipamentos

### Gestão de Técnicos
- Cadastro e controle de disponibilidade
- Localização em tempo real
- Relatórios de ponto
- Histórico de atendimentos

### Sistema de Permissões
- Perfis de usuário (administrador, técnico)
- Controle de acesso por funcionalidade
- Interface adaptada por perfil

## Contribuindo

1. Faça um fork do projeto
2. Crie uma branch para sua feature (`git checkout -b feature/nova-feature`)
3. Commit suas mudanças (`git commit -am 'Adiciona nova feature'`)
4. Push para a branch (`git push origin feature/nova-feature`)
5. Crie um Pull Request

## Versão

**CyberOS v1.1.8** - Sistema de Gestão de Ordens de Serviço

## Licença

Este projeto está licenciado sob a licença MIT - veja o arquivo LICENSE para detalhes.

## Contato

Para dúvidas ou sugestões sobre o projeto CyberOS, entre em contato através do GitHub. 