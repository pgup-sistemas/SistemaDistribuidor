import sqlite3

def fix_negative_stock():
    conn = sqlite3.connect('instance/distributor_system.db')
    cursor = conn.cursor()

    # Update products with negative stock to 0
    cursor.execute("""
        UPDATE products
        SET current_stock = 0
        WHERE current_stock < 0
    """)

    updated_count = cursor.rowcount
    print(f"Updated {updated_count} products with negative stock to 0.")

    # Check for duplicates (same name, different SKU)
    cursor.execute("""
        SELECT name, COUNT(*) as count
        FROM products
        WHERE active = 1
        GROUP BY name
        HAVING count > 1
        ORDER BY count DESC
    """)

    duplicates = cursor.fetchall()
    print(f"\nFound {len(duplicates)} product names with duplicates:")

    for name, count in duplicates:
        print(f"  - {name}: {count} variants")

        # Show the variants
        cursor.execute("""
            SELECT id, sku, current_stock, minimum_stock
            FROM products
            WHERE name = ? AND active = 1
            ORDER BY current_stock DESC
        """, (name,))

        variants = cursor.fetchall()
        for variant in variants:
            vid, vsku, vstock, vmin = variant
            print(f"    ID {vid} (SKU: {vsku}): stock {vstock}, min {vmin}")

    conn.commit()
    conn.close()

    print("\nStock fix completed.")

if __name__ == "__main__":
    fix_negative_stock()