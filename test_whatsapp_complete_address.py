#!/usr/bin/env python3
"""
Test script to demonstrate the complete delivery address format with CEP and house number
"""

from datetime import datetime

# Mock order class for testing
class MockOrder:
    def __init__(self, order_id, customer_name, customer_phone, total, payment_method, status, notes=None):
        self.id = order_id
        self.customer = MockCustomer(
            customer_name,
            customer_phone,
            address="Rua das Flores, 123",
            neighborhood="Centro",
            city="Cuiabá",
            state="MT",
            cep="78005-100"
        )
        self.created_at = datetime(2025, 11, 7, 10, 46)
        self.total = total
        self.payment_method = payment_method
        self.status = status
        self.payment_status = 'pending'
        self.notes = notes
        self.order_items = [
            MockOrderItem("Creme Dental 90g", 3, 5.50, 0),
            MockOrderItem("Água Mineral 500ml", 4, 2.50, 0),
            MockOrderItem("Óleo de Soja 900ml", 3, 8.00, 0),
            MockOrderItem("Presunto 500g", 4, 28.00, 0),
            MockOrderItem("Detergente 500ml", 4, 3.50, 0)
        ]

class MockCustomer:
    def __init__(self, name, phone, address=None, neighborhood=None, city=None, state=None, cep=None):
        self.name = name
        self.phone = phone
        self.address = address
        self.neighborhood = neighborhood
        self.city = city
        self.state = state
        self.cep = cep

class MockOrderItem:
    def __init__(self, name, quantity, unit_price, discount):
        self.product = MockProduct(name)
        self.quantity = quantity
        self.unit_price = unit_price
        self.discount = discount

class MockProduct:
    def __init__(self, name):
        self.name = name

class MockConfig:
    COMPANY_NAME = "Sistema Distribuidor"
    COMPANY_PHONE = "(11) 99999-9999"
    COMPANY_ADDRESS = "Rua das Distribuidoras, 123 - São Paulo/SP"

# Complete WhatsApp Message Generator with full delivery address
def create_complete_delivery_message(order):
    """Cria mensagem de confirmação do pedido com endereço completo para entrega"""
    company_name = MockConfig.COMPANY_NAME or "Sistema Distribuidor"

    # Montar endereço completo do cliente para entrega
    customer_address_parts = []

    # Rua e número (se estiver no campo address)
    if order.customer.address:
        customer_address_parts.append(order.customer.address)

    # Bairro
    if order.customer.neighborhood:
        customer_address_parts.append(order.customer.neighborhood)

    # Cidade/Estado
    if order.customer.city and order.customer.state:
        customer_address_parts.append(f"{order.customer.city}/{order.customer.state}")

    # CEP
    if order.customer.cep:
        customer_address_parts.append(f"CEP: {order.customer.cep}")

    customer_address = ", ".join(customer_address_parts) if customer_address_parts else "Endereço não informado"

    # Header Profissional
    message = f"""* PEDIDO CONFIRMADO * - {company_name}
================================================

* DETALHES DO PEDIDO *
• Número: #{order.id}
• Cliente: {order.customer.name}
• Telefone: {order.customer.phone}
• Data: {order.created_at.strftime('%d/%m/%Y %H:%M')}

* ENDEREÇO DE ENTREGA *
{'-' * 50}
{customer_address}

* ITENS SOLICITADOS *
{'-' * 50}
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
    message += f"{'-' * 50}\n"
    message += f"* VALOR TOTAL: R$ {order.total:.2f} *\n\n"

    message += "* PAGAMENTO & STATUS *\n"
    message += f"{'-' * 50}\n"

    # Status do pagamento
    if order.payment_method == 'cash':
        message += "• Método: Dinheiro\n"
        message += "• Status: CONFIRMADO\n"

    # Observações
    if order.notes:
        message += "\n* OBSERVAÇÕES *\n"
        message += f"{'-' * 50}\n"
        message += f"{order.notes}\n"

    # Contato e Localização
    message += "\n* CONTATO & LOCALIZAÇÃO *\n"
    message += f"{'-' * 50}\n"
    message += f"Loja: {company_name}\n"
    message += f"Contato: {MockConfig.COMPANY_PHONE}\n"
    message += f"Endereço: {MockConfig.COMPANY_ADDRESS}\n"

    # Footer Profissional
    message += "\n* Obrigado por escolher nossos serviços! *"

    return message

def test_complete_address_format():
    """Test the complete delivery address format"""
    print("=" * 70)
    print("WHATSAPP FORMATO COMPLETO - ENDEREÇO DE ENTREGA PARA ENTREGADORES")
    print("=" * 70)
    print()

    # Create sample order with complete address
    order = MockOrder(
        order_id=103,
        customer_name="oezios",
        customer_phone="(69) 99388-2222",
        total=176.50,
        payment_method="cash",
        status="confirmed",
        notes="Entregar no período da tarde. Casa com portão branco. Tocar campainha 3 vezes."
    )

    # Generate complete delivery message
    complete_message = create_complete_delivery_message(order)

    print("FORMATO COMPLETO COM ENDEREÇO PARA ENTREGA:")
    print("-" * 60)
    print(complete_message)
    print("-" * 60)
    print()

    print("INFORMAÇÕES ESSENCIAIS PARA ENTREGADORES:")
    print("• ✅ Endereço completo: Rua das Flores, 123")
    print("• ✅ Bairro: Centro")
    print("• ✅ Cidade/Estado: Cuiabá/MT")
    print("• ✅ CEP: 78005-100")
    print("• ✅ Observações detalhadas para entrega")
    print("• ✅ Telefone do cliente para contato")
    print("• ✅ Valor total e método de pagamento")

if __name__ == "__main__":
    test_complete_address_format()