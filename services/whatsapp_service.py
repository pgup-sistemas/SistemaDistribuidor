import urllib.parse
from config import Config

class WhatsAppService:
    def __init__(self):
        self.base_url = "https://web.whatsapp.com/send"
        self.company_phone = Config.COMPANY_PHONE or "(11) 99999-9999"
    
    def generate_order_link(self, order):
        """Generate WhatsApp Web link with order details"""
        
        # Build order message
        message_lines = [
            f"🛒 *Pedido #{order.id}*",
            f"📅 Data: {order.created_at.strftime('%d/%m/%Y %H:%M')}",
            f"👤 Cliente: {order.customer.name}",
            "",
            "📦 *Itens do Pedido:*"
        ]
        
        for item in order.order_items:
            line = f"• {item.quantity}x {item.product.name} - R$ {item.unit_price:.2f}"
            if item.discount > 0:
                line += f" (Desc: R$ {item.discount:.2f})"
            message_lines.append(line)
        
        message_lines.extend([
            "",
            f"💰 *Total: R$ {order.total:.2f}*",
            f"💳 Pagamento: {self._format_payment_method(order.payment_method)}",
            f"📋 Status: {self._format_status(order.status)}"
        ])
        
        if order.notes:
            message_lines.extend([
                "",
                f"📝 Observações: {order.notes}"
            ])
        
        message_lines.extend([
            "",
            f"🏪 {Config.COMPANY_NAME}",
            f"📞 {Config.COMPANY_PHONE}",
            f"📍 {Config.COMPANY_ADDRESS}"
        ])
        
        message = "\n".join(message_lines)
        
        # Build WhatsApp URL
        phone = order.customer.phone
        if phone:
            # Clean phone number (remove spaces, dashes, parentheses)
            phone = ''.join(filter(str.isdigit, phone))
            # Add country code if not present
            if not phone.startswith('55'):
                phone = '55' + phone
        
        params = {
            'text': message
        }
        
        if phone:
            params['phone'] = phone
        
        query_string = urllib.parse.urlencode(params)
        return f"{self.base_url}?{query_string}"
    
    def _format_payment_method(self, method):
        methods = {
            'cash': 'Dinheiro',
            'card': 'Cartão',
            'pix': 'PIX',
            'bank_slip': 'Boleto'
        }
        return methods.get(method, method)
    
    def _format_status(self, status):
        statuses = {
            'pending': 'Pendente',
            'confirmed': 'Confirmado',
            'preparing': 'Preparando',
            'delivered': 'Entregue',
            'cancelled': 'Cancelado'
        }
        return statuses.get(status, status)
    
    def send_order_confirmation(self, order, customer_phone):
        """
        Envia confirmação de pedido via WhatsApp Web
        
        Args:
            order: Objeto Order
            customer_phone (str): Telefone do cliente
        """
        try:
            # Formatar número do cliente
            phone = self._format_phone_number(customer_phone)
            
            # Criar mensagem de confirmação
            message = self._create_order_confirmation_message(order)
            
            # Criar link do WhatsApp Web
            whatsapp_url = f"https://wa.me/{phone}?text={urllib.parse.quote(message)}"
            
            # Log da ação
            print(f"📱 WhatsApp Link gerado para {phone}:")
            print(f"🔗 {whatsapp_url}")
            print(f"📝 Mensagem: {message}")
            
            return {
                'success': True,
                'whatsapp_url': whatsapp_url,
                'message': message,
                'phone': phone
            }
            
        except Exception as e:
            print(f"Erro no WhatsAppService: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def send_order_status_update(self, order, customer_phone, new_status):
        """
        Envia atualização de status do pedido
        
        Args:
            order: Objeto Order
            customer_phone (str): Telefone do cliente
            new_status (str): Novo status do pedido
        """
        try:
            phone = self._format_phone_number(customer_phone)
            
            # Criar mensagem de atualização
            message = self._create_status_update_message(order, new_status)
            
            # Criar link do WhatsApp Web
            whatsapp_url = f"https://wa.me/{phone}?text={urllib.parse.quote(message)}"
            
            print(f"📱 Atualização de status enviada para {phone}:")
            print(f"🔗 {whatsapp_url}")
            
            return {
                'success': True,
                'whatsapp_url': whatsapp_url,
                'message': message,
                'phone': phone
            }
            
        except Exception as e:
            print(f"Erro ao enviar atualização: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def _create_order_confirmation_message(self, order):
        """Cria mensagem de confirmação do pedido"""
        company_name = Config.COMPANY_NAME or "Sistema Distribuidor"
        
        message = f"""🛒 *PEDIDO CONFIRMADO* - {company_name}

📋 *Pedido #{order.id}*
👤 Cliente: {order.customer.name}
📞 Telefone: {order.customer.phone}
📅 Data: {order.created_at.strftime('%d/%m/%Y %H:%M')}

🛍️ *Itens do Pedido:*
"""
        
        for item in order.order_items:
            total_item = (item.unit_price * item.quantity) - item.discount
            message += f"• {item.product.name}\n"
            message += f"  Qtd: {item.quantity} x R$ {item.unit_price:.2f}\n"
            if item.discount > 0:
                message += f"  Desconto: R$ {item.discount:.2f}\n"
            message += f"  Total: R$ {total_item:.2f}\n\n"
        
        message += f"💰 *Total do Pedido: R$ {order.total:.2f}*\n\n"
        
        # Status do pagamento
        if order.payment_method == 'mercadopago':
            if order.payment_status == 'paid':
                message += "✅ *Pagamento Confirmado* (MercadoPago)\n"
            elif order.payment_status == 'pending':
                message += "⏳ *Pagamento Pendente* (MercadoPago)\n"
            else:
                message += f"💳 *Método:* MercadoPago\n"
        else:
            payment_methods = {
                'cash': '💵 Dinheiro',
                'card': '💳 Cartão',
                'pix': '📱 PIX',
                'bank_slip': '📄 Boleto'
            }
            message += f"💳 *Método:* {payment_methods.get(order.payment_method, order.payment_method)}\n"
        
        message += f"\n📊 *Status:* {order.status.upper()}\n"
        
        if order.notes:
            message += f"\n📝 *Observações:*\n{order.notes}\n"
        
        message += f"\n📞 *Contato:* {self.company_phone}\n"
        message += f"🏠 *Endereço:* {Config.COMPANY_ADDRESS or 'Consulte conosco'}\n"
        
        message += "\n✅ *Obrigado por escolher nossos serviços!*"
        
        return message
    
    def _create_status_update_message(self, order, new_status):
        """Cria mensagem de atualização de status"""
        company_name = Config.COMPANY_NAME or "Sistema Distribuidor"
        
        status_messages = {
            'confirmed': '✅ *PEDIDO CONFIRMADO*',
            'preparing': '👨‍🍳 *PREPARANDO SEU PEDIDO*',
            'in_transit': '🚚 *SAINDO PARA ENTREGA*',
            'delivered': '🎉 *PEDIDO ENTREGUE*',
            'cancelled': '❌ *PEDIDO CANCELADO*'
        }
        
        message = f"{status_messages.get(new_status, f'📊 *STATUS ATUALIZADO*')}\n\n"
        message += f"📋 *Pedido #{order.id}*\n"
        message += f"👤 Cliente: {order.customer.name}\n"
        message += f"💰 Total: R$ {order.total:.2f}\n\n"
        
        if new_status == 'preparing':
            message += "👨‍🍳 Seu pedido está sendo preparado com carinho!\n"
            message += "⏰ Tempo estimado: 30-45 minutos\n"
        elif new_status == 'in_transit':
            message += "🚚 Seu pedido saiu para entrega!\n"
            message += "📱 Em breve você receberá uma ligação\n"
        elif new_status == 'delivered':
            message += "🎉 Seu pedido foi entregue!\n"
            message += "😊 Esperamos que tenha gostado!\n"
        elif new_status == 'cancelled':
            message += "❌ Seu pedido foi cancelado\n"
            message += "📞 Entre em contato para mais informações\n"
        
        message += f"\n📞 *Contato:* {self.company_phone}\n"
        message += f"🏠 *Endereço:* {Config.COMPANY_ADDRESS or 'Consulte conosco'}\n"
        
        return message
    
    def _format_phone_number(self, phone):
        """
        Formata número de telefone para o padrão internacional
        
        Args:
            phone (str): Número de telefone
            
        Returns:
            str: Número formatado
        """
        # Remover caracteres especiais
        phone = ''.join(filter(str.isdigit, phone))
        
        # Adicionar código do país se não tiver
        if not phone.startswith('55'):
            phone = '55' + phone
            
        return phone
