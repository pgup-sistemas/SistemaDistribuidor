import os
import logging
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from sqlalchemy.orm import DeclarativeBase
from werkzeug.middleware.proxy_fix import ProxyFix
import re

# Configure logging
logging.basicConfig(level=logging.DEBUG)

class Base(DeclarativeBase):
    pass

db = SQLAlchemy(model_class=Base)
login_manager = LoginManager()

def create_app():
    app = Flask(__name__)

    # Configuration
    app.secret_key = os.environ.get("SESSION_SECRET", "dev-secret-key-change-in-production")
    app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get("DATABASE_URL", "postgresql://localhost/distributor_system")
    app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
        "pool_recycle": 300,
        "pool_pre_ping": True,
    }
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

    # Middleware
    app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)

    # Initialize extensions
    db.init_app(app)
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'
    login_manager.login_message = 'Por favor, faça login para acessar esta página.'
    login_manager.login_message_category = 'info'

    # Add custom template filters
    @app.template_filter('nl2br')
    def nl2br_filter(text):
        """Convert newlines to HTML <br> tags"""
        if not text:
            return ''
        from markupsafe import Markup
        # Replace \r\n, \r, and \n with <br>
        result = re.sub(r'\r\n|\r|\n', '<br>', str(text))
        return Markup(result)

    @login_manager.user_loader
    def load_user(user_id):
        from models import User
        return User.query.get(int(user_id))

    # Register blueprints
    from routes.auth import auth_bp
    from routes.dashboard import dashboard_bp
    from routes.customers import customers_bp
    from routes.products import products_bp
    from routes.categories import categories_bp
    from routes.suppliers import suppliers_bp
    from routes.orders import orders_bp
    from routes.stock import stock_bp
    from routes.reports import reports_bp
    from routes.users import users_bp
    from routes.backup import backup_bp
    from routes.company import company_bp
    from routes.validation import validation_bp

    app.register_blueprint(auth_bp, url_prefix='/auth')
    app.register_blueprint(dashboard_bp, url_prefix='/')
    app.register_blueprint(customers_bp, url_prefix='/customers')
    app.register_blueprint(products_bp, url_prefix='/products')
    app.register_blueprint(categories_bp, url_prefix='/categories')
    app.register_blueprint(suppliers_bp, url_prefix='/suppliers')
    app.register_blueprint(orders_bp, url_prefix='/orders')
    app.register_blueprint(stock_bp, url_prefix='/stock')
    app.register_blueprint(reports_bp, url_prefix='/reports')
    app.register_blueprint(users_bp, url_prefix='/users')
    app.register_blueprint(backup_bp, url_prefix='/backup')
    app.register_blueprint(company_bp, url_prefix='/company')
    app.register_blueprint(validation_bp, url_prefix='/api/validation')

    # Create tables
    with app.app_context():
        import models
        db.create_all()

        # Create default admin user if not exists
        from models import User
        from werkzeug.security import generate_password_hash

        admin = User.query.filter_by(email='admin@distribuidor.com').first()
        if not admin:
            admin_user = User(
                name='Administrador',
                email='admin@distribuidor.com',
                password_hash=generate_password_hash('admin123'),
                role='admin',
                active=True
            )
            db.session.add(admin_user)
            db.session.commit()
            logging.info("Default admin user created: admin@distribuidor.com / admin123")

    return app

app = create_app()