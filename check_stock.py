import sqlite3

def check_stock_levels():
    conn = sqlite3.connect('instance/distributor_system.db')
    cursor = conn.cursor()

    # Query products with low stock
    cursor.execute("""
        SELECT id, sku, name, current_stock, minimum_stock, active
        FROM products
        WHERE active = 1
        ORDER BY current_stock ASC
    """)

    products = cursor.fetchall()

    print("Product Stock Levels:")
    print("=" * 60)

    low_stock_products = []
    zero_stock_products = []

    for product in products:
        product_id, sku, name, current_stock, minimum_stock, active = product

        if current_stock == 0:
            zero_stock_products.append((sku, name, current_stock))
        elif current_stock <= minimum_stock:
            low_stock_products.append((sku, name, current_stock, minimum_stock))

        print(f"ID: {product_id}, SKU: {sku}, Name: {name}")
        print(f"  Stock: {current_stock}, Min: {minimum_stock}, Active: {active}")
        print("-" * 40)

    print(f"\nSummary:")
    print(f"Total products: {len(products)}")
    print(f"Products with zero stock: {len(zero_stock_products)}")
    print(f"Products with low stock (<= minimum): {len(low_stock_products)}")

    if zero_stock_products:
        print("\nProducts with ZERO stock:")
        for sku, name, stock in zero_stock_products:
            print(f"  - {name} (SKU: {sku}): {stock}")

    if low_stock_products:
        print("\nProducts with LOW stock:")
        for sku, name, stock, min_stock in low_stock_products:
            print(f"  - {name} (SKU: {sku}): {stock} (min: {min_stock})")

    # Check system user
    print("\n" + "=" * 60)
    print("System User Check:")
    cursor.execute("""
        SELECT id, name, email, role, active
        FROM users
        WHERE email = 'system@distribuidora.internal'
    """)

    system_user = cursor.fetchone()
    if system_user:
        user_id, name, email, role, active = system_user
        print(f"System user found:")
        print(f"  ID: {user_id}, Name: {name}, Email: {email}")
        print(f"  Role: {role}, Active: {active}")
        if not active:
            print("  WARNING: System user is NOT active!")
    else:
        print("System user NOT found!")

    conn.close()

if __name__ == "__main__":
    check_stock_levels()