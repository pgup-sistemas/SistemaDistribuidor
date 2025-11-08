#!/usr/bin/env python3
"""
Test script to demonstrate the new professional WhatsApp message format
"""

from datetime import datetime

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

# Professional WhatsApp Message Generator
def create_professional_whatsapp_message(order):
    """Cria mensagem de confirmação do pedido com layout profissional"""
    company_name = "Sistema Distribuidor"
    
    # Header Profissional
    message = f"""*** PEDIDO CONFIRMADO *** - {company_name}
================================================

** DETALHES DO PEDIDO **
• Numero: #{order.id}
• Cliente: {order.customer.name}
• Telefone: {order.customer.phone}
• Data: {order.created_at.strftime('%d/%m/%Y %H:%M')}

** ITENS SOLICITADOS **
------------------------
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
    message += "------------------------\n"
    message += f"*** VALOR TOTAL: R$ {order.total:.2f} ***\n\n"
    
    message += "** PAGAMENTO & STATUS **\n"
    message += "------------------------\n"
    
    # Status do pagamento
    if order.payment_method == 'cash':
        message += "• Metodo: Dinheiro\n"
        message += "• Status: PENDENTE\n"
    
    # Observacoes
    if order.notes:
        message += "\n** OBSERVACOES **\n"
        message += "------------------------\n"
        message += f"{order.notes}\n"
    
    # Contato e Localizacao
    message += "\n** CONTATO & LOCALIZACAO **\n"
    message += "------------------------\n"
    message += f"Loja: {company_name}\n"
    message += f"Contato: (11) 99999-9999\n"
    message += f"Endereco: Rua das Distribuidoras, 123 - Sao Paulo/SP\n"
    
    # Footer Profissional
    message += "\n*** Obrigado por escolher nossos servicos! ***"
    
    return message

def test_new_format():
    """Test the new professional WhatsApp format"""
    
    print("=" * 60)
    print("NOVO FORMATO PROFISSIONAL DO WHATSAPP")
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
    new_message = create_professional_whatsapp_message(order)
    
    print("NOVO FORMATO PROFISSIONAL:")
    print("-" * 50)
    print(new_message)
    print("-" * 50)
    print()
    
    print("MELHORIAS IMPLEMENTADAS:")
    print("• Header profissional com divisores visuais")
    print("• Secoes bem organizadas com separadores")
    print("• Layout de itens mais limpo e organizado")
    print("• Status e pagamento em secao dedicada")
    print("• Observacoes com separador visual")
    print("• Contato e localizacao destacados")
    print("• Hierarquia visual clara")

if __name__ == "__main__":
    test_new_format()