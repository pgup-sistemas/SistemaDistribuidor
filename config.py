import os

class Config:
    SECRET_KEY = os.environ.get('SESSION_SECRET') or 'dev-secret-key'
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or 'postgresql://localhost/distributor_system'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # App specific settings
    ITEMS_PER_PAGE = 20
    COMPANY_NAME = "Sistema Distribuidor"
    COMPANY_PHONE = "(11) 99999-9999"
    COMPANY_ADDRESS = "Rua das Distribuidoras, 123 - São Paulo/SP"
