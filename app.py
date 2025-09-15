import os
import logging
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_wtf.csrf import CSRFProtect
from flask_mail import Mail
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from sqlalchemy.orm import DeclarativeBase
from werkzeug.middleware.proxy_fix import ProxyFix
from services.logging_service import logging_service
import re

# Configure logging
logging.basicConfig(level=logging.DEBUG)

class Base(DeclarativeBase):
    pass

db = SQLAlchemy(model_class=Base)
login_manager = LoginManager()
csrf = CSRFProtect()
mail = Mail()
limiter = Limiter(
    key_func=get_remote_address,
    default_limits=["200 per day", "50 per hour"]
)

def create_app():
    app = Flask(__name__)

    # Configuration
    app.secret_key = os.environ.get("SESSION_SECRET", "dev-secret-key-change-in-production")
    app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get("DATABASE_URL", "postgresql://oezios:oezios9@localhost:5432/distributor_system")
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
    csrf.init_app(app)
    mail.init_app(app)
    limiter.init_app(app)
    logging_service.init_app(app)
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
    
    @app.template_global()
    def current_year():
        """Get current year"""
        from datetime import datetime
        return datetime.now().year

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
    from routes.payments import payments_bp
    from routes.delivery import delivery_bp
    from routes.public import public_bp

    app.register_blueprint(public_bp, url_prefix='/public')
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
    app.register_blueprint(payments_bp, url_prefix='/payments')
    app.register_blueprint(delivery_bp, url_prefix='/delivery')

    # Serve uploaded files
    @app.route('/uploads/<path:filename>')
    def uploaded_file(filename):
        from flask import send_from_directory
        return send_from_directory('uploads', filename)

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