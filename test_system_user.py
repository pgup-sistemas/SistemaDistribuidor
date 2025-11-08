from app import create_app, db
from models import User

app = create_app()

with app.app_context():
    print("Testing system user creation...")
    system_user = User.get_system_user()
    print(f"System user: ID={system_user.id}, active={system_user.active}, role={system_user.role}")
    db.session.commit()
    print("Committed.")