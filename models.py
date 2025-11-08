from datetime import datetime
from flask_login import UserMixin

# Import db from app to avoid multiple instances
try:
    from app import db
except ImportError:
    # Fallback: create db instance if app hasn't been created yet
    from flask_sqlalchemy import SQLAlchemy
    from sqlalchemy.orm import DeclarativeBase
    
    class Base(DeclarativeBase):
        pass
    
    db = SQLAlchemy(model_class=Base)

class User(UserMixin, db.Model):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    role = db.Column(db.String(20), nullable=False, default='attendant')  # admin, attendant, stock_manager, delivery, manager
    active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    audit_logs = db.relationship('AuditLog', backref='user', lazy=True)
    stock_movements = db.relationship('StockMovement', backref='user', lazy=True)
    orders = db.relationship('Order', backref='user', lazy=True)
    deliveries = db.relationship('Delivery', backref='delivery_user', lazy=True)
    
    @classmethod
    def get_system_user(cls):
        """Get or create system user for public orders and automated actions"""
        system_email = 'system@distribuidora.internal'
        system_user = cls.query.filter_by(email=system_email).first()

        if not system_user:
            print(f"[DEBUG] System user not found, creating new one")
            from werkzeug.security import generate_password_hash
            import secrets

            # Create system user with secure random password
            system_user = cls(
                name='Sistema Público',
                email=system_email,
                password_hash=generate_password_hash(secrets.token_urlsafe(32)),
                role='admin',
                active=True
            )
            db.session.add(system_user)
            db.session.flush()  # Get the ID without committing the transaction
            print(f"[DEBUG] System user created with ID: {system_user.id}")
        else:
            print(f"[DEBUG] System user found with ID: {system_user.id}")

        return system_user

class Customer(db.Model):
    __tablename__ = 'customers'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    document = db.Column(db.String(20))
    phone = db.Column(db.String(20))
    email = db.Column(db.String(120))
    
    # Endereço detalhado
    cep = db.Column(db.String(9))
    address = db.Column(db.String(200))
    neighborhood = db.Column(db.String(100))
    city = db.Column(db.String(100))
    state = db.Column(db.String(2))
    
    notes = db.Column(db.Text)
    active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    orders = db.relationship('Order', backref='customer', lazy=True)

class Category(db.Model):
    __tablename__ = 'categories'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False)
    description = db.Column(db.Text)
    active = db.Column(db.Boolean, default=True)
    
    # Relationships
    products = db.relationship('Product', backref='category', lazy=True)

class Supplier(db.Model):
    __tablename__ = 'suppliers'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    contact_name = db.Column(db.String(100))
    phone = db.Column(db.String(20))
    email = db.Column(db.String(120))
    address = db.Column(db.Text)
    active = db.Column(db.Boolean, default=True)
    
    # Relationships
    products = db.relationship('Product', backref='supplier', lazy=True)

class Product(db.Model):
    __tablename__ = 'products'
    
    id = db.Column(db.Integer, primary_key=True)
    sku = db.Column(db.String(50), unique=True, nullable=False)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    sale_price = db.Column(db.Numeric(10, 2), nullable=False)
    cost_price = db.Column(db.Numeric(10, 2))
    current_stock = db.Column(db.Integer, default=0)
    minimum_stock = db.Column(db.Integer, default=0)
    unit = db.Column(db.String(10), default='UN')
    image_url = db.Column(db.String(255))  # URL da imagem do produto
    category_id = db.Column(db.Integer, db.ForeignKey('categories.id'))
    supplier_id = db.Column(db.Integer, db.ForeignKey('suppliers.id'))
    active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    stock_movements = db.relationship('StockMovement', backref='product', lazy=True)
    order_items = db.relationship('OrderItem', backref='product', lazy=True)

class StockMovement(db.Model):
    __tablename__ = 'stock_movements'
    
    id = db.Column(db.Integer, primary_key=True)
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'), nullable=False)
    movement_type = db.Column(db.String(10), nullable=False)  # entry, exit, adjustment
    quantity = db.Column(db.Integer, nullable=False)
    reason = db.Column(db.String(200), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Order(db.Model):
    __tablename__ = 'orders'
    
    id = db.Column(db.Integer, primary_key=True)
    customer_id = db.Column(db.Integer, db.ForeignKey('customers.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    total = db.Column(db.Numeric(10, 2), nullable=False)
    payment_method = db.Column(db.String(20), nullable=False)  # cash, card, pix, bank_slip, mercadopago
    status = db.Column(db.String(20), default='pending')  # pending, confirmed, preparing, delivered, cancelled
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # MercadoPago fields
    payment_id = db.Column(db.String(100))  # ID do pagamento no MercadoPago
    payment_status = db.Column(db.String(20), default='pending')  # pending, paid, failed, refunded
    payment_date = db.Column(db.DateTime)
    preference_id = db.Column(db.String(100))  # ID da preferência no MercadoPago
    order_token = db.Column(db.String(100), unique=True)  # Token único para pedidos públicos
    
    # Relationships
    order_items = db.relationship('OrderItem', backref='order', lazy=True, cascade='all, delete-orphan')
    delivery = db.relationship('Delivery', backref='order', uselist=False, lazy=True)

class OrderItem(db.Model):
    __tablename__ = 'order_items'
    
    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey('orders.id'), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    unit_price = db.Column(db.Numeric(10, 2), nullable=False)
    discount = db.Column(db.Numeric(10, 2), default=0)

class Delivery(db.Model):
    __tablename__ = 'deliveries'
    
    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey('orders.id'), nullable=False)
    delivery_user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    status = db.Column(db.String(20), default='pending')  # pending, in_transit, delivered, failed
    delivery_proof = db.Column(db.Text)  # can store photo path or signature data
    notes = db.Column(db.Text)
    delivered_at = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class AuditLog(db.Model):
    __tablename__ = 'audit_logs'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    action = db.Column(db.String(50), nullable=False)
    entity = db.Column(db.String(50), nullable=False)
    entity_id = db.Column(db.Integer, nullable=False)
    old_data = db.Column(db.Text)
    new_data = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class QuickSale(db.Model):
    __tablename__ = 'quick_sales'

    id = db.Column(db.Integer, primary_key=True)
    sale_number = db.Column(db.String(20), unique=True, nullable=False)  # Número único da venda
    total = db.Column(db.Numeric(10, 2), nullable=False)
    payment_method = db.Column(db.String(20), nullable=False)  # cash, card, pix, bank_slip
    status = db.Column(db.String(20), default='completed')  # completed, cancelled
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)

    # Relationships
    items = db.relationship('QuickSaleItem', backref='sale', lazy=True, cascade='all, delete-orphan')
    user = db.relationship('User', backref='quick_sales')

    def generate_sale_number(self):
        """Generate unique sale number"""
        timestamp = self.created_at.strftime('%Y%m%d%H%M%S') if self.created_at else datetime.utcnow().strftime('%Y%m%d%H%M%S')
        return f"QV{timestamp}{self.id:04d}"

class QuickSaleItem(db.Model):
    __tablename__ = 'quick_sale_items'

    id = db.Column(db.Integer, primary_key=True)
    quick_sale_id = db.Column(db.Integer, db.ForeignKey('quick_sales.id'), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'), nullable=False)
    product_name = db.Column(db.String(100), nullable=False)  # Cache do nome para histórico
    product_sku = db.Column(db.String(50), nullable=False)   # Cache do SKU
    quantity = db.Column(db.Integer, nullable=False)
    unit_price = db.Column(db.Numeric(10, 2), nullable=False)
    discount = db.Column(db.Numeric(10, 2), default=0)
    total = db.Column(db.Numeric(10, 2), nullable=False)

    # Relationships
    product = db.relationship('Product', backref='quick_sale_items')

class Company(db.Model):
    __tablename__ = 'company'

    id = db.Column(db.Integer, primary_key=True)
    company_name = db.Column(db.String(200), nullable=False)  # Razão Social
    trade_name = db.Column(db.String(200))  # Nome Fantasia
    cnpj = db.Column(db.String(18), unique=True, nullable=False)
    ie = db.Column(db.String(20))  # Inscrição Estadual
    im = db.Column(db.String(20))  # Inscrição Municipal

    # Endereço
    address = db.Column(db.String(200))
    address_number = db.Column(db.String(10))
    complement = db.Column(db.String(100))
    neighborhood = db.Column(db.String(100))
    city = db.Column(db.String(100))
    state = db.Column(db.String(2))
    zip_code = db.Column(db.String(9))

    # Contatos
    phone = db.Column(db.String(20))
    mobile = db.Column(db.String(20))
    whatsapp = db.Column(db.String(20))
    email = db.Column(db.String(120))
    website = db.Column(db.String(200))

    # Configurações de documentos
    receipt_header = db.Column(db.Text)  # Cabeçalho personalizado para recibos
    receipt_footer = db.Column(db.Text)  # Rodapé personalizado para recibos
    order_notes = db.Column(db.Text)  # Observações padrão para pedidos

    # Dados bancários
    bank_name = db.Column(db.String(100))
    bank_agency = db.Column(db.String(10))
    bank_account = db.Column(db.String(20))
    pix_key = db.Column(db.String(100))

    # Sistema
    active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class PublicContent(db.Model):
    __tablename__ = 'public_content'

    id = db.Column(db.Integer, primary_key=True)
    section = db.Column(db.String(20), nullable=False)  # hero, features, about, contact, footer
    title = db.Column(db.String(200))
    content = db.Column(db.Text)
    image_url = db.Column(db.String(500))
    order = db.Column(db.Integer, default=0)
    active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    versions = db.relationship('ContentVersion',
                              primaryjoin="and_(ContentVersion.content_type=='public_content', ContentVersion.content_id==PublicContent.id)",
                              foreign_keys="[ContentVersion.content_id]",
                              backref='public_content', lazy=True, cascade='all, delete-orphan')

    __table_args__ = (
        db.Index('idx_public_content_section_active', 'section', 'active'),
        db.Index('idx_public_content_order', 'order'),
    )

class CompanySettings(db.Model):
    __tablename__ = 'company_settings'

    id = db.Column(db.Integer, primary_key=True)
    company_name = db.Column(db.String(200), nullable=False)
    tagline = db.Column(db.String(300))
    description = db.Column(db.Text)

    # Contact Information
    phone = db.Column(db.String(20))
    whatsapp = db.Column(db.String(20))
    email = db.Column(db.String(120))
    website = db.Column(db.String(200))

    # Address
    address = db.Column(db.String(200))
    city = db.Column(db.String(100))
    state = db.Column(db.String(2))
    zip_code = db.Column(db.String(9))

    # Social Media (stored as JSON)
    social_media = db.Column(db.Text)  # JSON string with social media links

    # Business Hours (stored as JSON)
    business_hours = db.Column(db.Text)  # JSON string with business hours

    # Branding
    logo_url = db.Column(db.String(500))
    favicon_url = db.Column(db.String(500))
    primary_color = db.Column(db.String(7))  # Hex color code
    secondary_color = db.Column(db.String(7))  # Hex color code

    # Settings
    maintenance_mode = db.Column(db.Boolean, default=False)
    allow_public_orders = db.Column(db.Boolean, default=True)
    timezone = db.Column(db.String(50), default='America/Cuiaba')

    active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    versions = db.relationship('ContentVersion',
                              primaryjoin="and_(ContentVersion.content_type=='company_settings', ContentVersion.content_id==CompanySettings.id)",
                              foreign_keys="[ContentVersion.content_id]",
                              backref='company_settings', lazy=True, cascade='all, delete-orphan')

    __table_args__ = (
        db.Index('idx_company_settings_active', 'active'),
    )

class MediaFile(db.Model):
    __tablename__ = 'media_files'

    id = db.Column(db.Integer, primary_key=True)
    filename = db.Column(db.String(255), nullable=False)
    original_filename = db.Column(db.String(255), nullable=False)
    file_path = db.Column(db.String(500), nullable=False)
    file_type = db.Column(db.String(50), nullable=False)  # image, document, video, audio
    mime_type = db.Column(db.String(100))
    file_size = db.Column(db.Integer, nullable=False)  # Size in bytes
    alt_text = db.Column(db.String(255))
    description = db.Column(db.Text)
    uploaded_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    uploaded_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships
    uploader = db.relationship('User', backref='uploaded_media')

    __table_args__ = (
        db.Index('idx_media_files_type', 'file_type'),
        db.Index('idx_media_files_uploaded_by', 'uploaded_by'),
        db.Index('idx_media_files_uploaded_at', 'uploaded_at'),
    )

class ContentVersion(db.Model):
    __tablename__ = 'content_versions'

    id = db.Column(db.Integer, primary_key=True)
    content_type = db.Column(db.String(30), nullable=False)  # public_content, company_settings
    content_id = db.Column(db.Integer, nullable=False)  # ID of the content being versioned
    version_number = db.Column(db.Integer, nullable=False)
    data = db.Column(db.Text, nullable=False)  # JSON string with full content data
    change_reason = db.Column(db.String(500))
    changed_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships
    changer = db.relationship('User', backref='content_versions')

    __table_args__ = (
        db.Index('idx_content_versions_type_id', 'content_type', 'content_id'),
        db.Index('idx_content_versions_changed_by', 'changed_by'),
        db.Index('idx_content_versions_created_at', 'created_at'),
        db.UniqueConstraint('content_type', 'content_id', 'version_number', name='unique_content_version'),
    )
