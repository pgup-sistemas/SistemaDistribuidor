from app import create_app, db
from models import Order, OrderItem, Customer, Product, StockMovement, User
from decimal import Decimal
import json

app = create_app()

def test_order_creation():
    with app.app_context():
        print("Testing order creation with current stock levels...")

        # Get a product with negative stock
        product = Product.query.filter(Product.current_stock < 0).first()
        if not product:
            print("No products with negative stock found.")
            return

        print(f"Testing with product: {product.name}, stock: {product.current_stock}")

        # Get system user
        system_user = User.get_system_user()
        print(f"System user: {system_user.id}")

        # Create a test customer
        customer = Customer(
            name='Test Customer',
            phone='123456789',
            email='test@example.com',
            address='Test Address',
            active=True
        )
        db.session.add(customer)
        db.session.flush()

        # Try to create order with quantity 1
        items_data = json.dumps([{
            'product_id': product.id,
            'quantity': 1,
            'unit_price': str(product.sale_price),
            'discount': '0'
        }])

        print(f"Attempting to create order with 1 unit of {product.name}")

        # Simulate the stock check
        quantity = 1
        if product.current_stock < quantity:
            print(f"Stock check FAILED: requested {quantity}, available {product.current_stock}")
            print("This should prevent order creation.")
        else:
            print(f"Stock check PASSED: requested {quantity}, available {product.current_stock}")
            print("This would allow order creation.")

        # Clean up
        db.session.rollback()
        print("Test completed, rolled back changes.")

if __name__ == "__main__":
    test_order_creation()