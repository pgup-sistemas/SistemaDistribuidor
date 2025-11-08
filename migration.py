
from app import app, db
from models import Customer, User
from datetime import datetime

def migrate_database():
    with app.app_context():
        # Add missing columns to customers table
        try:
            # Use text() for raw SQL execution in newer SQLAlchemy versions
            from sqlalchemy import text
            from sqlalchemy.engine import reflection
            from sqlalchemy import inspect

            # Get database engine and inspector
            engine = db.engine
            inspector = inspect(engine)

            # Check if columns exist and add them for SQLite
            existing_columns = [col['name'] for col in inspector.get_columns('customers')]

            if 'cep' not in existing_columns:
                db.session.execute(text('ALTER TABLE customers ADD COLUMN cep VARCHAR(9)'))
            if 'address' not in existing_columns:
                db.session.execute(text('ALTER TABLE customers ADD COLUMN address VARCHAR(200)'))
            if 'neighborhood' not in existing_columns:
                db.session.execute(text('ALTER TABLE customers ADD COLUMN neighborhood VARCHAR(100)'))
            if 'city' not in existing_columns:
                db.session.execute(text('ALTER TABLE customers ADD COLUMN city VARCHAR(100)'))
            if 'state' not in existing_columns:
                db.session.execute(text('ALTER TABLE customers ADD COLUMN state VARCHAR(2)'))

            # Fix users with null created_at
            users_without_date = User.query.filter(User.created_at.is_(None)).all()
            if users_without_date:
                print(f"Fixing {len(users_without_date)} users with null created_at...")
                for user in users_without_date:
                    user.created_at = datetime.utcnow()
                db.session.commit()
                print("Fixed users with null created_at.")

            # Adicionar índices para performance
            print("Adding performance indexes...")

            # Índices para usuários
            db.session.execute(text('CREATE INDEX IF NOT EXISTS idx_users_email ON users(email)'))
            db.session.execute(text('CREATE INDEX IF NOT EXISTS idx_users_active ON users(active)'))
            db.session.execute(text('CREATE INDEX IF NOT EXISTS idx_users_role ON users(role)'))

            # Índices para produtos
            db.session.execute(text('CREATE INDEX IF NOT EXISTS idx_products_sku ON products(sku)'))
            db.session.execute(text('CREATE INDEX IF NOT EXISTS idx_products_active ON products(active)'))
            db.session.execute(text('CREATE INDEX IF NOT EXISTS idx_products_category ON products(category_id)'))
            db.session.execute(text('CREATE INDEX IF NOT EXISTS idx_products_supplier ON products(supplier_id)'))

            # Índices para pedidos
            db.session.execute(text('CREATE INDEX IF NOT EXISTS idx_orders_customer ON orders(customer_id)'))
            db.session.execute(text('CREATE INDEX IF NOT EXISTS idx_orders_user ON orders(user_id)'))
            db.session.execute(text('CREATE INDEX IF NOT EXISTS idx_orders_status ON orders(status)'))
            db.session.execute(text('CREATE INDEX IF NOT EXISTS idx_orders_created_at ON orders(created_at)'))

            # Índices para itens de pedido
            db.session.execute(text('CREATE INDEX IF NOT EXISTS idx_order_items_order ON order_items(order_id)'))
            db.session.execute(text('CREATE INDEX IF NOT EXISTS idx_order_items_product ON order_items(product_id)'))

            # Índices para movimentações de estoque
            db.session.execute(text('CREATE INDEX IF NOT EXISTS idx_stock_movements_product ON stock_movements(product_id)'))
            db.session.execute(text('CREATE INDEX IF NOT EXISTS idx_stock_movements_user ON stock_movements(user_id)'))
            db.session.execute(text('CREATE INDEX IF NOT EXISTS idx_stock_movements_created_at ON stock_movements(created_at)'))

            db.session.commit()
            print("Performance indexes added successfully!")

            db.session.commit()
            print("Database migration completed successfully!")
        except Exception as e:
            db.session.rollback()
            print(f"Migration error: {e}")

if __name__ == '__main__':
    migrate_database()
