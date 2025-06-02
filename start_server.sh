#!/bin/bash

# Ativar ambiente virtual
source venv_new/bin/activate

# Iniciar servidor Django na porta 8080 e IP 192.168.15.69
python manage.py runserver 192.168.15.69:8080 