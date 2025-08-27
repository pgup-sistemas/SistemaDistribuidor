
from app import app, db
from models import Customer

def migrate_database():
    with app.app_context():
        # Add missing columns to customers table
        try:
            db.engine.execute('ALTER TABLE customers ADD COLUMN IF NOT EXISTS cep VARCHAR(9)')
            db.engine.execute('ALTER TABLE customers ADD COLUMN IF NOT EXISTS address VARCHAR(200)')
            db.engine.execute('ALTER TABLE customers ADD COLUMN IF NOT EXISTS neighborhood VARCHAR(100)')
            db.engine.execute('ALTER TABLE customers ADD COLUMN IF NOT EXISTS city VARCHAR(100)')
            db.engine.execute('ALTER TABLE customers ADD COLUMN IF NOT EXISTS state VARCHAR(2)')
            print("Database migration completed successfully!")
        except Exception as e:
            print(f"Migration error: {e}")

if __name__ == '__main__':
    migrate_database()
