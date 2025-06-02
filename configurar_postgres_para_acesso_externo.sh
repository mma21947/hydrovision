#!/bin/bash

# Este script configura o PostgreSQL para permitir conexões externas

echo "Configurando PostgreSQL para aceitar conexões externas..."

# 1. Editar postgresql.conf para permitir conexões em todos os endereços IP
sudo sed -i "s/#listen_addresses = 'localhost'/listen_addresses = '*'/" /etc/postgresql/16/main/postgresql.conf

# 2. Verificar se pg_hba.conf já tem uma entrada para 0.0.0.0/0 (todas as redes)
# Se não tiver, adicionar
if ! sudo grep -q "host    all             all             0.0.0.0/0               scram-sha-256" /etc/postgresql/16/main/pg_hba.conf; then
  echo "Adicionando regra para permitir conexões de qualquer rede..."
  echo "host    all             all             0.0.0.0/0               scram-sha-256" | sudo tee -a /etc/postgresql/16/main/pg_hba.conf > /dev/null
fi

# 3. Criar um usuário específico para conexões externas (mais seguro)
echo "Criando usuário específico para aplicativo móvel..."
sudo -u postgres psql -c "CREATE USER app_mobile WITH PASSWORD 'senha_segura';"
sudo -u postgres psql -c "GRANT ALL PRIVILEGES ON DATABASE cyberos_db TO app_mobile;"
sudo -u postgres psql -d cyberos_db -c "GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO app_mobile;"
sudo -u postgres psql -d cyberos_db -c "GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO app_mobile;"

# 4. Reiniciar o PostgreSQL para aplicar as configurações
echo "Reiniciando PostgreSQL..."
sudo systemctl restart postgresql

echo "Configuração concluída!"
echo ""
echo "Informações para conexão externa:"
echo "--------------------------------"
echo "Endereço IP do servidor: $(hostname -I | awk '{print $1}')"
echo "Porta: 5432"
echo "Nome do banco de dados: cyberos_db"
echo "Usuário: app_mobile"
echo "Senha: senha_segura"
echo ""
echo "IMPORTANTE: No seu aplicativo móvel, use estas informações para configurar a conexão."
echo "Lembre-se de alterar a senha 'senha_segura' para uma senha forte e única!"
echo ""
echo "Para acessar o PostgreSQL localmente a partir do app Django, edite o settings.py:"
echo ""
cat << EOF
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'cyberos_db',
        'USER': 'app_mobile',  # Novo usuário criado para conexões externas
        'PASSWORD': 'senha_segura',  # Substitua pela senha definida acima
        'HOST': 'localhost',  # Use localhost para conexões locais do Django
        'PORT': '5432',
    }
}
EOF 