#!/usr/bin/env python3
"""
WSGI entry point para produção
"""

import os
from app import create_app

# Configurar ambiente de produção
os.environ.setdefault('FLASK_ENV', 'production')

# Criar aplicação
application = create_app()

if __name__ == "__main__":
    application.run()
