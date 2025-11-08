import sqlite3
import json

def query_public_orders():
    conn = sqlite3.connect('instance/distributor_system.db')
    cursor = conn.cursor()

    # Query public orders (orders with order_token or created by system user)
    cursor.execute("""
        SELECT o.id, o.customer_id, o.user_id, o.total, o.payment_method, o.status,
               o.created_at, o.order_token, o.payment_status,
               c.name as customer_name, c.phone, c.email, c.address, c.city, c.state,
               u.email as user_email
        FROM orders o
        JOIN customers c ON o.customer_id = c.id
        JOIN users u ON o.user_id = u.id
        WHERE o.order_token IS NOT NULL OR u.email = 'system@distribuidora.internal'
        ORDER BY o.created_at DESC
    """)

    orders = cursor.fetchall()

    print(f"Found {len(orders)} public orders (with token or system user):")
    print("=" * 50)

    for order in orders:
        order_id, customer_id, user_id, total, payment_method, status, created_at, order_token, payment_status, customer_name, phone, email, address, city, state = order

        print(f"Order ID: {order_id}")
        print(f"Order Token: {order_token}")
        print(f"Customer: {customer_name} (ID: {customer_id})")
        print(f"Contact: {phone}, {email}")
        print(f"Address: {address}, {city}, {state}")
        print(f"Total: R$ {total}")
        print(f"Payment: {payment_method} ({payment_status})")
        print(f"Status: {status}")
        print(f"Created: {created_at}")
        print(f"User ID: {user_id}")

        # Get order items
        cursor.execute("""
            SELECT oi.quantity, oi.unit_price, oi.discount,
                   p.name as product_name, p.sku
            FROM order_items oi
            JOIN products p ON oi.product_id = p.id
            WHERE oi.order_id = ?
        """, (order_id,))

        items = cursor.fetchall()
        print(f"Items ({len(items)}):")
        for item in items:
            qty, unit_price, discount, product_name, sku = item
            print(f"  - {product_name} (SKU: {sku}): {qty} x R$ {unit_price} - R$ {discount} discount")

        print("-" * 30)

    # Check for any orders without order_token but might be public
    cursor.execute("""
        SELECT COUNT(*) FROM orders WHERE order_token IS NULL
    """)
    non_public_count = cursor.fetchone()[0]
    print(f"\nNon-public orders: {non_public_count}")

    # Check data integrity: orders with missing customers
    cursor.execute("""
        SELECT COUNT(*) FROM orders o
        LEFT JOIN customers c ON o.customer_id = c.id
        WHERE c.id IS NULL
    """)
    orphaned_orders = cursor.fetchone()[0]
    print(f"Orders with missing customers: {orphaned_orders}")

    # Check order items with missing products
    cursor.execute("""
        SELECT COUNT(*) FROM order_items oi
        LEFT JOIN products p ON oi.product_id = p.id
        WHERE p.id IS NULL
    """)
    orphaned_items = cursor.fetchone()[0]
    print(f"Order items with missing products: {orphaned_items}")

    conn.close()

if __name__ == "__main__":
    query_public_orders()