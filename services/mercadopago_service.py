import mercadopago
import json
import logging
from datetime import datetime
from config import Config

class MercadoPagoService:
    def __init__(self):
        """Inicializa o serviço do MercadoPago"""
        self.sdk = mercadopago.SDK(Config.MERCADOPAGO_ACCESS_TOKEN)
        self.public_key = Config.MERCADOPAGO_PUBLIC_KEY
        self.sandbox = Config.MERCADOPAGO_SANDBOX
        self.webhook_secret = Config.MERCADOPAGO_WEBHOOK_SECRET
        
        logging.info(f"MercadoPago Service initialized - Sandbox: {self.sandbox}")
    
    def create_preference(self, order):
        """
        Cria uma preferência de pagamento no MercadoPago
        
        Args:
            order: Objeto Order do sistema
            
        Returns:
            dict: Resposta da API do MercadoPago com preference_id e init_point
        """
        try:
            # Construir itens do pedido
            items = []
            for item in order.order_items:
                items.append({
                    "id": str(item.product.id),
                    "title": item.product.name,
                    "description": item.product.description or f"Produto {item.product.name}",
                    "quantity": item.quantity,
                    "unit_price": float(item.unit_price),
                    "currency_id": "BRL"
                })
            
            # Informações do pagador
            payer_info = {
                "name": order.customer.name,
                "email": order.customer.email or "cliente@exemplo.com",
                "phone": {
                    "number": order.customer.phone or "11999999999"
                }
            }
            
            # Endereço do pagador (se disponível)
            if order.customer.address:
                payer_info["address"] = {
                    "street_name": order.customer.address,
                    "street_number": 123,  # Número padrão se não disponível
                    "zip_code": order.customer.cep or "00000000"
                }
            
            # Configuração da preferência
            preference_data = {
                "items": items,
                "payer": payer_info,
                "back_urls": {
                    "success": f"http://localhost:5000/payments/success",
                    "failure": f"http://localhost:5000/payments/failure",
                    "pending": f"http://localhost:5000/payments/pending"
                },
                "auto_return": "approved",
                "external_reference": str(order.id),
                "notification_url": f"http://localhost:5000/payments/webhook",
                "statement_descriptor": Config.COMPANY_NAME[:22],  # Máximo 22 caracteres
                "metadata": {
                    "order_id": order.id,
                    "customer_id": order.customer.id,
                    "system": "Sistema Distribuidor"
                }
            }
            
            # Configurações específicas para sandbox
            if self.sandbox:
                preference_data["sandbox_mode"] = True
            
            # Criar preferência
            result = self.sdk.preference().create(preference_data)
            
            if result["status"] == 201:
                preference = result["response"]
                logging.info(f"Preference created successfully for order {order.id}: {preference['id']}")
                
                return {
                    "success": True,
                    "preference_id": preference["id"],
                    "init_point": preference["init_point"],
                    "sandbox_init_point": preference.get("sandbox_init_point"),
                    "public_key": self.public_key
                }
            else:
                logging.error(f"Error creating preference: {result}")
                return {
                    "success": False,
                    "error": result.get("message", "Erro desconhecido ao criar preferência")
                }
                
        except Exception as e:
            logging.error(f"Exception creating preference for order {order.id}: {str(e)}")
            return {
                "success": False,
                "error": f"Erro interno: {str(e)}"
            }
    
    def get_payment_info(self, payment_id):
        """
        Obtém informações de um pagamento específico
        
        Args:
            payment_id: ID do pagamento no MercadoPago
            
        Returns:
            dict: Informações do pagamento
        """
        try:
            result = self.sdk.payment().get(payment_id)
            
            if result["status"] == 200:
                return {
                    "success": True,
                    "payment": result["response"]
                }
            else:
                return {
                    "success": False,
                    "error": result.get("message", "Erro ao buscar pagamento")
                }
                
        except Exception as e:
            logging.error(f"Exception getting payment info for {payment_id}: {str(e)}")
            return {
                "success": False,
                "error": f"Erro interno: {str(e)}"
            }
    
    def process_webhook(self, notification_data):
        """
        Processa notificações do webhook do MercadoPago
        
        Args:
            notification_data: Dados da notificação
            
        Returns:
            dict: Resultado do processamento
        """
        try:
            # Obter informações da notificação
            notification_id = notification_data.get("id")
            notification_type = notification_data.get("type")
            
            if notification_type == "payment":
                # Buscar informações do pagamento
                payment_id = notification_data.get("data", {}).get("id")
                
                if payment_id:
                    payment_info = self.get_payment_info(payment_id)
                    
                    if payment_info["success"]:
                        payment = payment_info["payment"]
                        external_reference = payment.get("external_reference")
                        
                        if external_reference:
                            # Importar aqui para evitar circular import
                            from models import Order, db
                            
                            # Buscar pedido no sistema
                            order = Order.query.get(int(external_reference))
                            
                            if order:
                                # Atualizar status do pedido baseado no status do pagamento
                                payment_status = payment.get("status")
                                
                                if payment_status == "approved":
                                    order.status = "confirmed"
                                    order.payment_status = "paid"
                                elif payment_status == "pending":
                                    order.status = "pending"
                                    order.payment_status = "pending"
                                elif payment_status in ["rejected", "cancelled"]:
                                    order.status = "cancelled"
                                    order.payment_status = "failed"
                                
                                # Salvar informações do pagamento
                                order.payment_id = payment_id
                                order.payment_method = payment.get("payment_method_id", "mercadopago")
                                order.payment_date = datetime.utcnow()
                                
                                db.session.commit()
                                
                                logging.info(f"Order {order.id} updated with payment status: {payment_status}")
                                
                                return {
                                    "success": True,
                                    "order_id": order.id,
                                    "payment_status": payment_status
                                }
                            else:
                                logging.warning(f"Order not found for external_reference: {external_reference}")
                                return {
                                    "success": False,
                                    "error": "Pedido não encontrado"
                                }
                        else:
                            logging.warning("No external_reference found in payment")
                            return {
                                "success": False,
                                "error": "Referência externa não encontrada"
                            }
                    else:
                        logging.error(f"Error getting payment info: {payment_info['error']}")
                        return {
                            "success": False,
                            "error": payment_info["error"]
                        }
                else:
                    logging.warning("No payment ID in notification data")
                    return {
                        "success": False,
                        "error": "ID do pagamento não encontrado"
                    }
            else:
                logging.info(f"Notification type {notification_type} not processed")
                return {
                    "success": True,
                    "message": f"Tipo de notificação {notification_type} não processado"
                }
                
        except Exception as e:
            logging.error(f"Exception processing webhook: {str(e)}")
            return {
                "success": False,
                "error": f"Erro interno: {str(e)}"
            }
    
    def create_payment_link(self, order):
        """
        Cria um link de pagamento simples (PIX, Boleto, etc.)
        
        Args:
            order: Objeto Order do sistema
            
        Returns:
            dict: Link de pagamento
        """
        try:
            # Criar preferência
            preference_result = self.create_preference(order)
            
            if preference_result["success"]:
                # Para sandbox, usar sandbox_init_point se disponível
                init_point = preference_result.get("sandbox_init_point") or preference_result["init_point"]
                
                return {
                    "success": True,
                    "payment_url": init_point,
                    "preference_id": preference_result["preference_id"]
                }
            else:
                return preference_result
                
        except Exception as e:
            logging.error(f"Exception creating payment link for order {order.id}: {str(e)}")
            return {
                "success": False,
                "error": f"Erro interno: {str(e)}"
            }
