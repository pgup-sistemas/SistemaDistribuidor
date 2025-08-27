
from app import app, db
from models import Customer

def migrate_database():
    with app.app_context():
        # Add missing columns to customers table
        try:
            # Use text() for raw SQL execution in newer SQLAlchemy versions
            from sqlalchemy import text
            
            db.session.execute(text('ALTER TABLE customers ADD COLUMN IF NOT EXISTS cep VARCHAR(9)'))
            db.session.execute(text('ALTER TABLE customers ADD COLUMN IF NOT EXISTS address VARCHAR(200)'))
            db.session.execute(text('ALTER TABLE customers ADD COLUMN IF NOT EXISTS neighborhood VARCHAR(100)'))
            db.session.execute(text('ALTER TABLE customers ADD COLUMN IF NOT EXISTS city VARCHAR(100)'))
            db.session.execute(text('ALTER TABLE customers ADD COLUMN IF NOT EXISTS state VARCHAR(2)'))
            
            db.session.commit()
            print("Database migration completed successfully!")
        except Exception as e:
            db.session.rollback()
            print(f"Migration error: {e}")

if __name__ == '__main__':
    migrate_database()
