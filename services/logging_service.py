import logging
import os
from datetime import datetime
from logging.handlers import RotatingFileHandler
from flask import request
from flask_login import current_user
from functools import wraps

class LoggingService:
    def __init__(self, app=None):
        self.app = app
        if app is not None:
            self.init_app(app)
    
    def init_app(self, app):
        """Inicializa o sistema de logging"""
        
        # Criar diretório de logs se não existir
        if not os.path.exists('logs'):
            os.makedirs('logs')
        
        # Configurar logging para diferentes níveis
        self._setup_application_logging(app)
        self._setup_security_logging(app)
        self._setup_payment_logging(app)
        self._setup_error_logging(app)
    
    def _setup_application_logging(self, app):
        """Configura logging geral da aplicação"""
        if not app.debug and not app.testing:
            file_handler = RotatingFileHandler(
                'logs/app.log', 
                maxBytes=10240000,  # 10MB
                backupCount=10
            )
            file_handler.setFormatter(logging.Formatter(
                '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
            ))
            file_handler.setLevel(logging.INFO)
            app.logger.addHandler(file_handler)
            app.logger.setLevel(logging.INFO)
            app.logger.info('Sistema Distribuidor iniciado')
    
    def _setup_security_logging(self, app):
        """Configura logging de segurança"""
        security_handler = RotatingFileHandler(
            'logs/security.log',
            maxBytes=10240000,  # 10MB
            backupCount=5
        )
        security_handler.setFormatter(logging.Formatter(
            '%(asctime)s SECURITY: %(message)s'
        ))
        security_handler.setLevel(logging.WARNING)
        
        security_logger = logging.getLogger('security')
        security_logger.addHandler(security_handler)
        security_logger.setLevel(logging.WARNING)
    
    def _setup_payment_logging(self, app):
        """Configura logging de pagamentos"""
        payment_handler = RotatingFileHandler(
            'logs/payments.log',
            maxBytes=10240000,  # 10MB
            backupCount=10
        )
        payment_handler.setFormatter(logging.Formatter(
            '%(asctime)s PAYMENT: %(message)s'
        ))
        payment_handler.setLevel(logging.INFO)
        
        payment_logger = logging.getLogger('payment')
        payment_logger.addHandler(payment_handler)
        payment_logger.setLevel(logging.INFO)
    
    def _setup_error_logging(self, app):
        """Configura logging de erros"""
        error_handler = RotatingFileHandler(
            'logs/errors.log',
            maxBytes=10240000,  # 10MB
            backupCount=5
        )
        error_handler.setFormatter(logging.Formatter(
            '%(asctime)s ERROR: %(message)s [in %(pathname)s:%(lineno)d]'
        ))
        error_handler.setLevel(logging.ERROR)
        
        error_logger = logging.getLogger('error')
        error_logger.addHandler(error_handler)
        error_logger.setLevel(logging.ERROR)

# Instância global do serviço de logging
logging_service = LoggingService()

def log_user_action(action, details=None):
    """Decorator para logar ações do usuário"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            try:
                result = f(*args, **kwargs)
                
                # Log da ação
                user_info = "Anonymous"
                if current_user.is_authenticated:
                    user_info = f"User {current_user.id} ({current_user.email})"
                
                ip_address = request.remote_addr
                user_agent = request.headers.get('User-Agent', 'Unknown')
                
                log_message = f"{action} - {user_info} - IP: {ip_address} - {details or ''}"
                
                # Log no arquivo de segurança
                security_logger = logging.getLogger('security')
                security_logger.info(log_message)
                
                return result
                
            except Exception as e:
                # Log de erro
                error_logger = logging.getLogger('error')
                error_logger.error(f"Error in {action}: {str(e)}")
                raise
                
        return decorated_function
    return decorator

def log_payment_action(action, order_id=None, details=None):
    """Log específico para ações de pagamento"""
    user_info = "Anonymous"
    if current_user.is_authenticated:
        user_info = f"User {current_user.id} ({current_user.email})"
    
    ip_address = request.remote_addr
    
    log_message = f"{action} - {user_info} - Order: {order_id} - IP: {ip_address} - {details or ''}"
    
    payment_logger = logging.getLogger('payment')
    payment_logger.info(log_message)

def log_security_event(event_type, details=None):
    """Log específico para eventos de segurança"""
    user_info = "Anonymous"
    if current_user.is_authenticated:
        user_info = f"User {current_user.id} ({current_user.email})"
    
    ip_address = request.remote_addr
    user_agent = request.headers.get('User-Agent', 'Unknown')
    
    log_message = f"{event_type} - {user_info} - IP: {ip_address} - UA: {user_agent} - {details or ''}"
    
    security_logger = logging.getLogger('security')
    security_logger.warning(log_message)

def log_error(error, context=None):
    """Log específico para erros"""
    user_info = "Anonymous"
    if current_user.is_authenticated:
        user_info = f"User {current_user.id} ({current_user.email})"
    
    ip_address = request.remote_addr
    
    log_message = f"ERROR - {user_info} - IP: {ip_address} - {context or ''} - {str(error)}"
    
    error_logger = logging.getLogger('error')
    error_logger.error(log_message)
