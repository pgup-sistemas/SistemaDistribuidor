#!/usr/bin/env python3
"""
Test script to submit a public order programmatically.
Fetches available products, selects one with sufficient stock,
and POSTs an order to /public/order with valid customer data.
Includes error handling and logging to verify order creation.
"""

import requests
import json
import logging
import sys
import os

# Add current directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app
from models import Order, Product, db

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

BASE_URL = 'http://localhost:5000'

def fetch_products():
    """Fetch available products from the API."""
    try:
        response = requests.get(f'{BASE_URL}/public/api/products')
        response.raise_for_status()
        products = response.json()
        logger.info(f"Fetched {len(products)} products")
        return products
    except requests.RequestException as e:
        logger.error(f"Failed to fetch products: {e}")
        return []

def select_product_with_stock(products):
    """Select a product with sufficient stock."""
    for product in products:
        if product.get('stock_quantity', 0) > 0:
            logger.info(f"Selected product: {product['name']} (ID: {product['id']}, Stock: {product['stock_quantity']}, Price: {product['price']})")
            return product
    logger.error("No products with sufficient stock found")
    return None

def submit_order(product):
    """Submit a public order."""
    customer_data = {
        'customer_name': 'Test Customer',
        'customer_phone': '(11) 99999-9999',
        'customer_email': 'test@example.com',
        'customer_address': 'Rua Teste, 123',
        'customer_neighborhood': 'Centro',
        'customer_city': 'São Paulo',
        'customer_state': 'SP',
        'customer_cep': '01234-567',
        'payment_method': 'cash',
        'notes': 'Test order from automated script'
    }

    items = [{
        'product_id': product['id'],
        'quantity': 1,
        'unit_price': product['price'],
        'discount': 0.0
    }]

    order_data = {
        **customer_data,
        'items': json.dumps(items)
    }

    try:
        response = requests.post(f'{BASE_URL}/public/order', data=order_data, allow_redirects=False)
        logger.info(f"Order submission response status: {response.status_code}")

        if response.status_code == 302:  # Redirect to success page
            location = response.headers.get('Location', '')
            if 'order/success/' in location:
                token = location.split('order/success/')[-1]
                logger.info(f"Order created successfully with token: {token}")
                return token
            else:
                logger.error(f"Unexpected redirect location: {location}")
                return None
        else:
            logger.error(f"Order creation failed with status {response.status_code}")
            logger.error(f"Response text: {response.text}")
            return None

    except requests.RequestException as e:
        logger.error(f"Failed to submit order: {e}")
        return None

def verify_order_in_admin(token):
    """Verify that the order appears in the admin system."""
    try:
        app = create_app()
        with app.app_context():
            order = Order.query.filter_by(order_token=token).first()
            if order:
                logger.info(f"Order verified in admin system:")
                logger.info(f"  Order ID: {order.id}")
                logger.info(f"  Customer: {order.customer.name}")
                logger.info(f"  Total: R$ {order.total}")
                logger.info(f"  Status: {order.status}")
                logger.info(f"  Items: {len(order.order_items)}")
                for item in order.order_items:
                    logger.info(f"    - {item.product.name} x{item.quantity} @ R$ {item.unit_price}")
                return True
            else:
                logger.error("Order not found in admin system")
                return False
    except Exception as e:
        logger.error(f"Failed to verify order in admin: {e}")
        return False

def main():
    logger.info("Starting public order test script")

    # Fetch products
    products = fetch_products()
    if not products:
        logger.error("No products available, exiting")
        return False

    # Select product with stock
    product = select_product_with_stock(products)
    if not product:
        logger.error("No suitable product found, exiting")
        return False

    # Submit order
    token = submit_order(product)
    if not token:
        logger.error("Order submission failed, exiting")
        return False

    # Verify in admin system
    verified = verify_order_in_admin(token)
    if verified:
        logger.info("✅ Test completed successfully - Order created and verified in admin system")
        return True
    else:
        logger.error("❌ Test failed - Order not verified in admin system")
        return False

if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)