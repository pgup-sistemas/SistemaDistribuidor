from abc import ABC, abstractmethod
from datetime import datetime
import logging
from config import Config

class PaymentGateway(ABC):
    """Interface base para gateways de pagamento"""
    
    @abstractmethod
    def create_preference(self, order):
        """Cria uma preferência/intenção de pagamento"""
        pass
        
    @abstractmethod
    def get_payment_info(self, payment_id):
        """Obtém informações de um pagamento específico"""
        pass
        
    @abstractmethod
    def process_webhook(self, notification_data):
        """Processa notificações do webhook"""
        pass
        
    @abstractmethod
    def create_payment_link(self, order):
        """Cria um link de pagamento"""
        pass

class PaymentGatewayFactory:
    """Fábrica para criar instâncias de gateways de pagamento"""
    
    @staticmethod
    def create():
        """Cria uma instância do gateway configurado"""
        provider = Config.PAYMENT_PROVIDER.lower()
        
        if provider == 'mercadopago':
            from services.mercadopago_service import MercadoPagoService
            return MercadoPagoService()
        elif provider == 'stripe':
            from services.stripe_service import StripeService
            return StripeService()
        else:
            raise ValueError(f"Gateway de pagamento não suportado: {provider}")

# Exemplo de uso:
# payment_gateway = PaymentGatewayFactory.create()
# result = payment_gateway.create_preference(order)