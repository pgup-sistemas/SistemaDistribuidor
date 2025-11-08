#!/usr/bin/env python3
"""
Test script to demonstrate the new professional WhatsApp message format
"""

from datetime import datetime
import sys
import os

# Add the app directory to Python path for imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Mock order class for testing
class MockOrder:
    def __init__(self, order_id, customer_name, customer_phone, total, payment_method, status, notes=None):
        self.id = order_id
        self.customer = MockCustomer(customer_name, customer_phone)
        self.created_at = datetime(2025, 11, 6, 15, 55)
        self.total = total
        self.payment_method = payment_method
        self.status = status
        self.payment_status = 'pending'
        self.notes = notes
        self.order_items = [
            MockOrderItem("Fanta Laranja 2L", 1, 7.50, 0),
            MockOrderItem("Coca-Cola 2L", 1, 8.50, 0),
            MockOrderItem("Água Mineral 500ml", 1, 2.50, 0)
        ]

class MockCustomer:
    def __init__(self, name, phone):
        self.name = name
        self.phone = phone

class MockOrderItem:
    def __init__(self, name, quantity, unit_price, discount):
        self.product = MockProduct(name)
        self.quantity = quantity
        self.unit_price = unit_price
        self.discount = discount

class MockProduct:
    def __init__(self, name):
        self.name = name

# Mock config
class MockConfig:
    COMPANY_NAME = "Distribuidora Premium"
    COMPANY_PHONE = "(11) 99999-9999"
    COMPANY_ADDRESS = "Rua das Distribuidoras, 123 - São Paulo/SP"

# Mock WhatsApp Service (simplified)
class WhatsAppService:
    def __init__(self):
        self.company_phone = MockConfig.COMPANY_PHONE

    def _create_order_confirmation_message(self, order):
        """Cria mensagem de confirmação do pedido com layout profissional"""
        company_name = MockConfig.COMPANY_NAME or "Sistema Distribuidor"
        
        # Header Profissional
        message = f"""🌟 *PEDIDO CONFIRMADO* - {company_name}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📋 *DETALHES DO PEDIDO*
• Número: #{order.id}
• Cliente: {order.customer.name}
• Telefone: {order.customer.phone}
• Data: {order.created_at.strftime('%d/%m/%Y %H:%M')}

📦 *ITENS SOLICITADOS*
━━━━━━━━━━━━━━━━━━━━━━━━
"""
        
        # Itens do Pedido
        for item in order.order_items:
            total_item = (item.unit_price * item.quantity) - item.discount
            message += f"• {item.product.name}\n"
            message += f"  Qtd: {item.quantity} x R$ {item.unit_price:.2f}\n"
            if item.discount > 0:
                message += f"  Desconto: R$ {item.discount:.2f}\n"
            message += f"  Subtotal: R$ {total_item:.2f}\n\n"
        
        # Total e Status
        message += "━━━━━━━━━━━━━━━━━━━━━━━━\n"
        message += f"💰 *VALOR TOTAL: R$ {order.total:.2f}*\n\n"
        
        message += "💳 *PAGAMENTO & STATUS*\n"
        message += "━━━━━━━━━━━━━━━━━━━━━━━━\n"
        
        # Status do pagamento
        if order.payment_method == 'mercadopago':
            if order.payment_status == 'paid':
                message += "• Método: MercadoPago\n"
                message += "• Status: ✅ PAGAMENTO CONFIRMADO\n"
            elif order.payment_status == 'pending':
                message += "• Método: MercadoPago\n"
                message += "• Status: ⏳ PAGAMENTO PENDENTE\n"
            else:
                message += f"• Método: MercadoPago\n"
                message += f"• Status: {order.status.upper()}\n"
        else:
            payment_methods = {
                'cash': '💵 Dinheiro',
                'card': '💳 Cartão',
                'pix': '📱 PIX',
                'bank_slip': '📄 Boleto'
            }
            status_translations = {
                'pending': '⏳ PENDENTE',
                'confirmed': '✅ CONFIRMADO',
                'preparing': '👨‍🍳 PREPARANDO',
                'in_transit': '🚚 A CAMINHO',
                'delivered': '🎉 ENTREGUE',
                'cancelled': '❌ CANCELADO'
            }
            
            message += f"• Método: {payment_methods.get(order.payment_method, order.payment_method)}\n"
            message += f"• Status: {status_translations.get(order.status, order.status.upper())}\n"
        
        # Observações
        if order.notes:
            message += "\n📝 *OBSERVAÇÕES*\n"
            message += "━━━━━━━━━━━━━━━━━━━━━━━━\n"
            message += f"{order.notes}\n"
        
        # Contato e Localização
        message += "\n📞 *CONTATO & LOCALIZAÇÃO*\n"
        message += "━━━━━━━━━━━━━━━━━━━━━━━━\n"
        message += f"🏪 {company_name}\n"
        message += f"📱 {self.company_phone}\n"
        message += f"📍 {MockConfig.COMPANY_ADDRESS or 'Consulte conosco'}\n"
        
        # Footer Profissional
        message += "\n✨ Obrigado por escolher nossos serviços! ✨"
        
        return message

def test_professional_format():
    """Test the new professional WhatsApp format"""
    
    print("=" * 60)
    print("TESTANDO NOVO FORMATO PROFISSIONAL DO WHATSAPP")
    print("=" * 60)
    print()
    
    # Create sample order matching the user's example
    order = MockOrder(
        order_id=102,
        customer_name="oezios",
        customer_phone="(69) 99388-2222",
        total=18.50,
        payment_method="cash",
        status="pending",
        notes="teste"
    )
    
    # Generate professional message
    whatsapp_service = WhatsAppService()
    professional_message = whatsapp_service._create_order_confirmation_message(order)
    
    print("📱 NOVO FORMATO PROFISSIONAL:")
    print("-" * 40)
    print(professional_message)
    print("-" * 40)
    print()
    
    # Show comparison
    print("📊 COMPARAÇÃO COM FORMATO ANTERIOR:")
    print("-" * 40)
    
    old_format = """🛒 *PEDIDO CONFIRMADO* - Sistema Distribuidor

📋 *Pedido #102*
👤 Cliente: oezios
📞 Telefone: (69) 99388-2222
📅 Data: 06/11/2025 15:55

🛍️ *Itens do Pedido:*
• Fanta Laranja 2L
  Qtd: 1 x R$ 7.50
  Total: R$ 7.50

• Coca-Cola 2L
  Qtd: 1 x R$ 8.50
  Total: R$ 8.50

• Água Mineral 500ml
  Qtd: 1 x R$ 2.50
  Total: R$ 2.50

💰 *Total do Pedido: R$ 18.50*

💳 *Método:* 💵 Dinheiro

📊 *Status:* PENDING

📝 *Observações:*
teste

📞 *Contato:* (11) 99999-9999
🏠 *Endereço:* Rua das Distribuidoras, 123 - São Paulo/SP

✅ *Obrigado por escolher nossos serviços!*"""
    
    print("❌ FORMATO ANTERIOR:")
    print(old_format)
    print()
    
    print("🎯 MELHORIAS IMPLEMENTADAS:")
    print("• ✅ Header profissional com divider visual")
    print("• ✅ Seções bem organizadas com divisores")
    print("• ✅ Layout de itens mais limpo e organizado")
    print("• ✅ Status e pagamento em seção dedicada")
    print("• ✅ Observações com separador visual")
    print("• ✅ Contato e localização destacados")
    print("• ✅ Emojis consistentes e bem posicionados")
    print("• ✅ Hierarquia visual clara")

if __name__ == "__main__":
    test_professional_format()