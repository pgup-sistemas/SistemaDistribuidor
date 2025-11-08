import os
from dotenv import load_dotenv

# Carregar variáveis do arquivo .env
load_dotenv()

class Config:
    # Carregar variáveis de ambiente com fallbacks seguros
    SECRET_KEY = os.environ.get('SESSION_SECRET') or 'MFKlGunyCTcnwoCPrTO83-VOSgLBBF2OdN2WI4KTOTaim4dcG0qp1x6MflntEEzDRvU'
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or 'postgresql://oezios:oezios9@localhost:5432/distributor_system'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # URL Base para callbacks
    BASE_URL = os.environ.get('BASE_URL') or 'http://localhost:5000'
    
    # Gateway de Pagamento
    PAYMENT_PROVIDER = os.environ.get('PAYMENT_PROVIDER', 'mercadopago')
    
    # App specific settings
    ITEMS_PER_PAGE = 20
    COMPANY_NAME = "Sistema Distribuidor"
    COMPANY_PHONE = "(11) 99999-9999"
    COMPANY_ADDRESS = "Rua das Distribuidoras, 123 - São Paulo/SP"
    
    # MercadoPago Configuration
    MERCADOPAGO_ACCESS_TOKEN = os.environ.get('MERCADOPAGO_ACCESS_TOKEN')
    MERCADOPAGO_PUBLIC_KEY = os.environ.get('MERCADOPAGO_PUBLIC_KEY')
    MERCADOPAGO_WEBHOOK_SECRET = os.environ.get('MERCADOPAGO_WEBHOOK_SECRET')
    MERCADOPAGO_SANDBOX = os.environ.get('MERCADOPAGO_SANDBOX', 'true').lower() == 'true'
    
    # Email Configuration
    MAIL_SERVER = os.environ.get('MAIL_SERVER') or 'smtp.gmail.com'
    MAIL_PORT = int(os.environ.get('MAIL_PORT') or 587)
    MAIL_USE_TLS = os.environ.get('MAIL_USE_TLS', 'true').lower() in ['true', 'on', '1']
    MAIL_USE_SSL = os.environ.get('MAIL_USE_SSL', 'false').lower() in ['true', 'on', '1']
    MAIL_USERNAME = os.environ.get('MAIL_USERNAME')
    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD')
    MAIL_DEFAULT_SENDER = os.environ.get('MAIL_DEFAULT_SENDER') or 'noreply@distribuidor.com'
    MAIL_SUPPRESS_SEND = os.environ.get('MAIL_SUPPRESS_SEND', 'false').lower() in ['true', 'on', '1']

