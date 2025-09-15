from flask import render_template
from flask_mail import Message
from app import mail
from config import Config
import logging

class EmailService:
    def __init__(self):
        self.from_email = Config.MAIL_DEFAULT_SENDER
        self.company_name = Config.COMPANY_NAME
        
    def send_order_confirmation(self, order, customer_email):
        """
        Envia email de confirmação de pedido
        
        Args:
            order: Objeto Order
            customer_email: Email do cliente
        """
        try:
            subject = f"Confirmação de Pedido #{order.id} - {self.company_name}"
            
            msg = Message(
                subject=subject,
                recipients=[customer_email],
                sender=self.from_email
            )
            
            # Renderizar template HTML do email
            msg.html = render_template('emails/order_confirmation.html', order=order)
            msg.body = render_template('emails/order_confirmation.txt', order=order)
            
            # Enviar email
            mail.send(msg)
            logging.info(f"Email de confirmação enviado para {customer_email} - Pedido #{order.id}")
            
            return True
            
        except Exception as e:
            logging.error(f"Erro ao enviar email de confirmação: {str(e)}")
            return False
    
    def send_payment_confirmation(self, order, customer_email):
        """
        Envia email de confirmação de pagamento
        
        Args:
            order: Objeto Order
            customer_email: Email do cliente
        """
        try:
            subject = f"Pagamento Confirmado - Pedido #{order.id} - {self.company_name}"
            
            msg = Message(
                subject=subject,
                recipients=[customer_email],
                sender=self.from_email
            )
            
            # Renderizar template HTML do email
            msg.html = render_template('emails/payment_confirmation.html', order=order)
            msg.body = render_template('emails/payment_confirmation.txt', order=order)
            
            # Enviar email
            mail.send(msg)
            logging.info(f"Email de confirmação de pagamento enviado para {customer_email} - Pedido #{order.id}")
            
            return True
            
        except Exception as e:
            logging.error(f"Erro ao enviar email de confirmação de pagamento: {str(e)}")
            return False
    
    def send_order_status_update(self, order, customer_email, old_status, new_status):
        """
        Envia email de atualização de status do pedido
        
        Args:
            order: Objeto Order
            customer_email: Email do cliente
            old_status: Status anterior
            new_status: Novo status
        """
        try:
            subject = f"Atualização do Pedido #{order.id} - {self.company_name}"
            
            msg = Message(
                subject=subject,
                recipients=[customer_email],
                sender=self.from_email
            )
            
            # Renderizar template HTML do email
            msg.html = render_template('emails/order_status_update.html', 
                                     order=order, 
                                     old_status=old_status, 
                                     new_status=new_status)
            msg.body = render_template('emails/order_status_update.txt', 
                                     order=order, 
                                     old_status=old_status, 
                                     new_status=new_status)
            
            # Enviar email
            mail.send(msg)
            logging.info(f"Email de atualização de status enviado para {customer_email} - Pedido #{order.id}")
            
            return True
            
        except Exception as e:
            logging.error(f"Erro ao enviar email de atualização de status: {str(e)}")
            return False
    
    def send_low_stock_alert(self, products, admin_emails):
        """
        Envia alerta de estoque baixo para administradores
        
        Args:
            products: Lista de produtos com estoque baixo
            admin_emails: Lista de emails dos administradores
        """
        try:
            if not products or not admin_emails:
                return False
                
            subject = f"Alerta de Estoque Baixo - {self.company_name}"
            
            msg = Message(
                subject=subject,
                recipients=admin_emails,
                sender=self.from_email
            )
            
            # Renderizar template HTML do email
            msg.html = render_template('emails/low_stock_alert.html', products=products)
            msg.body = render_template('emails/low_stock_alert.txt', products=products)
            
            # Enviar email
            mail.send(msg)
            logging.info(f"Alerta de estoque baixo enviado para {len(admin_emails)} administradores")
            
            return True
            
        except Exception as e:
            logging.error(f"Erro ao enviar alerta de estoque baixo: {str(e)}")
            return False
    
    def send_test_email(self, recipient_email):
        """
        Envia email de teste para verificar configuração
        
        Args:
            recipient_email: Email para enviar o teste
        """
        try:
            subject = f"Email de Teste - {self.company_name}"
            
            msg = Message(
                subject=subject,
                recipients=[recipient_email],
                sender=self.from_email
            )
            
            msg.body = f"""
            Este é um email de teste do Sistema Distribuidor.
            
            Se você recebeu este email, a configuração de email está funcionando corretamente.
            
            Data/Hora: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}
            
            Sistema Distribuidor
            """
            
            # Enviar email
            mail.send(msg)
            logging.info(f"Email de teste enviado para {recipient_email}")
            
            return True
            
        except Exception as e:
            logging.error(f"Erro ao enviar email de teste: {str(e)}")
            return False
