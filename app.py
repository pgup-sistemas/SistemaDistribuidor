import os
import logging
import re
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_wtf.csrf import CSRFProtect
from flask_mail import Mail
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from sqlalchemy.orm import DeclarativeBase
from werkzeug.middleware.proxy_fix import ProxyFix
from markupsafe import Markup
from services.logging_service import logging_service

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
    default_limits=["200 per day", "50 per hour"],
    storage_uri="memory://"
)

def create_app():
    app = Flask(__name__)

    # Configuration
    app.secret_key = os.environ.get("SESSION_SECRET") or "MFKlGunyCTcnwoCPrTO83-VOSgLBBF2OdN2WI4KTOTaim4dcG0qp1x6MflntEEzDRvU"
    app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get("DATABASE_URL") or "sqlite:///distributor_system.db"
    app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
        "pool_recycle": 300,
        "pool_pre_ping": True,
    }
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

    # Secure session cookie configuration
    app.config["SESSION_COOKIE_SECURE"] = os.environ.get("FLASK_ENV") == "production"  # HTTPS only in production
    app.config["SESSION_COOKIE_HTTPONLY"] = True  # Prevent XSS access to session cookie
    app.config["SESSION_COOKIE_SAMESITE"] = "Lax"  # CSRF protection
    app.config["PERMANENT_SESSION_LIFETIME"] = 3600  # 1 hour session timeout

    # Middleware
    app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)

    # HTTPS enforcement em produção
    if os.environ.get('FLASK_ENV') == 'production':
        try:
            from werkzeug.middleware.https_fix import HTTPSRedirectMiddleware
            app.wsgi_app = HTTPSRedirectMiddleware(app.wsgi_app)
        except ImportError:
            # Fallback for older werkzeug versions
            pass

    # Initialize extensions
    db.init_app(app)
    login_manager.init_app(app)
    csrf.init_app(app)
    # Mail configuration (read from environment)
    app.config['MAIL_SERVER'] = os.environ.get('MAIL_SERVER') or 'smtp.gmail.com'
    app.config['MAIL_PORT'] = int(os.environ.get('MAIL_PORT') or 587)
    app.config['MAIL_USE_TLS'] = os.environ.get('MAIL_USE_TLS', 'true').lower() in ['true', 'on', '1']
    app.config['MAIL_USE_SSL'] = os.environ.get('MAIL_USE_SSL', 'false').lower() in ['true', 'on', '1']
    app.config['MAIL_USERNAME'] = os.environ.get('MAIL_USERNAME')
    app.config['MAIL_PASSWORD'] = os.environ.get('MAIL_PASSWORD')
    app.config['MAIL_DEFAULT_SENDER'] = os.environ.get('MAIL_DEFAULT_SENDER') or 'noreply@distribuidor.com'
    app.config['MAIL_SUPPRESS_SEND'] = os.environ.get('MAIL_SUPPRESS_SEND', 'false').lower() in ['true', 'on', '1']

    mail.init_app(app)
    limiter.init_app(app)
    logging_service.init_app(app)
    login_manager.login_view = 'auth.login'  # type: ignore
    login_manager.login_message = 'Por favor, faça login para acessar esta página.'
    login_manager.login_message_category = 'info'

    # Add custom template filters
    @app.template_filter('nl2br')
    def nl2br_filter(text):
        """Convert newlines to HTML <br> tags"""
        if not text:
            return ''
        # Replace \r\n, \r, and \n with <br>
        result = re.sub(r'\r\n|\r|\n', '<br>', str(text))
        return Markup(result)
    
    @app.template_global()
    def current_year():
        """Get current year"""
        from datetime import datetime
        return datetime.now().year
    
    @app.template_global()
    def csrf_token():
        """Generate CSRF token for templates"""
        from flask_wtf.csrf import generate_csrf
        return generate_csrf()

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
    from routes.quick_sale import quick_sale_bp
    from routes.nfe_integration import nfe_bp
    from routes.admin_public import admin_public_bp

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
    app.register_blueprint(admin_public_bp, url_prefix='/admin-public')
    app.register_blueprint(validation_bp, url_prefix='/api/validation')
    app.register_blueprint(payments_bp, url_prefix='/payments')
    app.register_blueprint(delivery_bp, url_prefix='/delivery')
    app.register_blueprint(quick_sale_bp, url_prefix='/quick-sale')
    app.register_blueprint(nfe_bp, url_prefix='/nfe-integration')

    # Serve uploaded files
    @app.route('/uploads/<path:filename>')
    def uploaded_file(filename):
        from flask import send_from_directory
        return send_from_directory('uploads', filename)

    # Error handlers
    @app.errorhandler(404)
    def not_found_error(error):
        from flask import render_template
        return render_template('errors/404.html'), 404

    @app.errorhandler(500)
    def internal_error(error):
        from flask import render_template
        db.session.rollback()
        return render_template('errors/500.html'), 500

    @app.errorhandler(403)
    def forbidden_error(error):
        from flask import render_template
        return render_template('errors/403.html'), 403

    # Create tables
    with app.app_context():
        import models
        db.create_all()


    return app

app = create_app()