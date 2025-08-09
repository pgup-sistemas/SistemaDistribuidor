import urllib.parse
from config import Config

class WhatsAppService:
    def __init__(self):
        self.base_url = "https://web.whatsapp.com/send"
    
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
