from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, session, current_app
from models import Order, OrderItem, Customer, Product, StockMovement, User, CompanySettings, PublicContent, db
from services.whatsapp_service import WhatsAppService
from services.email_service import EmailService
from app import csrf
from decimal import Decimal
import json
import uuid
from datetime import datetime

public_bp = Blueprint('public', __name__)

@public_bp.route('/')
def index():
    """Página inicial pública"""
    try:
        # Fetch company settings
        company_settings = CompanySettings.query.filter_by(active=True).first()

        # Fetch public content for hero section
        hero_content = PublicContent.query.filter_by(section='hero', active=True).order_by(PublicContent.order).first()

        # Fetch features content
        features_content = PublicContent.query.filter_by(section='features', active=True).order_by(PublicContent.order).all()

        # Fetch about content
        about_content = PublicContent.query.filter_by(section='about', active=True).order_by(PublicContent.order).first()

        # Fetch contact content
        contact_content = PublicContent.query.filter_by(section='contact', active=True).order_by(PublicContent.order).first()

        # Fetch footer content
        footer_content = PublicContent.query.filter_by(section='footer', active=True).order_by(PublicContent.order).first()

        return render_template('public/index.html',
                             company_settings=company_settings,
                             hero_content=hero_content,
                             features_content=features_content,
                             about_content=about_content,
                             contact_content=contact_content,
                             footer_content=footer_content)
    except Exception as e:
        print(f"[ERROR] Error loading public content: {str(e)}")
        # Fallback to config values
        return render_template('public/index.html')

@public_bp.route('/menu')
def menu():
    """Menu público de produtos"""
    try:
        products = Product.query.filter_by(active=True).all()
        company_settings = CompanySettings.query.filter_by(active=True).first()
        return render_template('public/menu.html', products=products, company_settings=company_settings)
    except Exception as e:
        print(f"[ERROR] Error loading menu: {str(e)}")
        products = Product.query.filter_by(active=True).all()
        return render_template('public/menu.html', products=products)

@public_bp.route('/order')
def order_form():
    """Formulário público de pedido"""
    try:
        products = Product.query.filter_by(active=True).all()
        company_settings = CompanySettings.query.filter_by(active=True).first()
        return render_template('public/order_form.html', products=products, company_settings=company_settings)
    except Exception as e:
        print(f"[ERROR] Error loading order form: {str(e)}")
        products = Product.query.filter_by(active=True).all()
        return render_template('public/order_form.html', products=products)

@public_bp.route('/order', methods=['POST'])
@csrf.exempt
def create_order():
    """Criar pedido público"""
    try:
        # Dados do cliente
        customer_name = request.form.get('customer_name', '').strip()
        customer_phone = request.form.get('customer_phone', '').strip()
        customer_email = request.form.get('customer_email', '').strip()
        customer_address = request.form.get('customer_address', '').strip()
        customer_neighborhood = request.form.get('customer_neighborhood', '').strip()
        customer_city = request.form.get('customer_city', '').strip()
        customer_state = request.form.get('customer_state', '').strip()
        customer_cep = request.form.get('customer_cep', '').strip()
        
        # Dados do pedido
        payment_method = request.form.get('payment_method', 'cash')
        notes = request.form.get('notes', '').strip()
        items_data = request.form.get('items', '[]')
        
        # Validações básicas
        if not customer_name or not customer_phone:
            flash('Nome e telefone são obrigatórios.', 'error')
            return redirect(url_for('public.order_form'))
        
        # Parse dos itens
        try:
            items = json.loads(items_data)
        except json.JSONDecodeError:
            flash('Dados do pedido inválidos.', 'error')
            return redirect(url_for('public.order_form'))
        
        if not items:
            flash('Adicione pelo menos um item ao pedido.', 'error')
            return redirect(url_for('public.order_form'))
        
        # Buscar ou criar cliente
        customer = Customer.query.filter_by(phone=customer_phone).first()
        if not customer:
            customer = Customer(
                name=customer_name,
                phone=customer_phone,
                email=customer_email,
                address=customer_address,
                neighborhood=customer_neighborhood,
                city=customer_city,
                state=customer_state,
                cep=customer_cep,
                active=True
            )
            db.session.add(customer)
            db.session.flush()  # Para obter o ID
        
        # Get system user for public orders
        print(f"[DEBUG] Attempting to get system user for public order")
        system_user = User.get_system_user()
        print(f"[DEBUG] System user obtained: ID={system_user.id}, active={system_user.active}, role={system_user.role}")
        if not system_user.active:
            print(f"[ERROR] System user is not active! Cannot create order.")
            flash('Erro interno do sistema. Tente novamente mais tarde.', 'error')
            return redirect(url_for('public.order_form'))

        # Criar pedido
        order = Order(
            customer_id=customer.id,
            user_id=system_user.id,
            total=Decimal('0.00'),  # Initialize with 0, will be updated after calculating items
            payment_method=payment_method,
            status='pending',
            notes=notes,
            order_token=str(uuid.uuid4())  # Token único para o pedido
        )

        db.session.add(order)
        db.session.flush()  # Para obter o ID
        print(f"[DEBUG] Order created with ID: {order.id}, token: {order.order_token}")
        
        # Calcular total e adicionar itens
        total = Decimal('0.00')
        print(f"[DEBUG] Processing {len(items)} items for order")
        for item_data in items:
            product_id = item_data.get('product_id')
            quantity = int(item_data.get('quantity', 1))
            unit_price = Decimal(str(item_data.get('unit_price', 0)))
            discount = Decimal(str(item_data.get('discount', 0)))

            print(f"[DEBUG] Processing item: product_id={product_id}, quantity={quantity}")

            product = Product.query.get(product_id)
            if not product:
                print(f"[DEBUG] Product {product_id} not found")
                continue

            print(f"[DEBUG] Product {product.name} has stock {product.current_stock}, active={product.active}")

            # Verificar estoque
            if product.current_stock < quantity:
                print(f"[ERROR] Insufficient stock for {product.name}: requested {quantity}, available {product.current_stock}")
                flash(f'Estoque insuficiente para {product.name}. Disponível: {product.current_stock}', 'error')
                db.session.rollback()
                return redirect(url_for('public.order_form'))
            else:
                print(f"[DEBUG] Stock check passed for {product.name}: requested {quantity}, available {product.current_stock}")
            
            # Criar item do pedido
            order_item = OrderItem(
                order_id=order.id,
                product_id=product_id,
                quantity=quantity,
                unit_price=unit_price,
                discount=discount
            )
            db.session.add(order_item)
            
            # Atualizar estoque
            product.current_stock -= quantity
            # Prevent negative stock
            if product.current_stock < 0:
                product.current_stock = 0
            
            # Criar movimento de estoque
            stock_movement = StockMovement(
                product_id=product_id,
                quantity=-quantity,
                movement_type='sale',
                reason=f'Venda - Pedido #{order.id}',
                user_id=system_user.id
            )
            db.session.add(stock_movement)
            
            # Calcular total
            item_total = (unit_price * quantity) - discount
            total += item_total
        
        order.total = total
        db.session.commit()
        print(f"[DEBUG] Order {order.id} committed successfully with total {order.total}")

        # Enviar confirmação via WhatsApp
        whatsapp_service = WhatsAppService()
        whatsapp_service.send_order_confirmation(order, customer_phone)
        
        # Enviar email se tiver
        if customer_email:
            email_service = EmailService()
            email_service.send_order_confirmation(order, customer_email)
        
        # Redirecionar para página de sucesso
        return redirect(url_for('public.order_success', token=order.order_token))
        
    except Exception as e:
        db.session.rollback()
        print(f"[ERROR] Exception creating public order: {str(e)}")
        import traceback
        print(f"[ERROR] Traceback: {traceback.format_exc()}")
        flash(f'Erro ao criar pedido: {str(e)}', 'error')
        return redirect(url_for('public.order_form'))

@public_bp.route('/order/success/<token>')
def order_success(token):
    """Página de sucesso do pedido"""
    try:
        order = Order.query.filter_by(order_token=token).first_or_404()
        company_settings = CompanySettings.query.filter_by(active=True).first()
        return render_template('public/order_success.html', order=order, company_settings=company_settings)
    except Exception as e:
        print(f"[ERROR] Error loading order success: {str(e)}")
        order = Order.query.filter_by(order_token=token).first_or_404()
        return render_template('public/order_success.html', order=order)

@public_bp.route('/order/status/<token>')
def order_status(token):
    """Verificar status do pedido"""
    try:
        order = Order.query.filter_by(order_token=token).first_or_404()
        company_settings = CompanySettings.query.filter_by(active=True).first()
        return render_template('public/order_status.html', order=order, company_settings=company_settings)
    except Exception as e:
        print(f"[ERROR] Error loading order status: {str(e)}")
        order = Order.query.filter_by(order_token=token).first_or_404()
        return render_template('public/order_status.html', order=order)

@public_bp.route('/api/products')
@csrf.exempt
def api_products():
    """API para buscar produtos"""
    products = Product.query.filter_by(active=True).all()
    return jsonify([{
        'id': p.id,
        'name': p.name,
        'price': float(p.sale_price),
        'stock_quantity': p.current_stock,
        'description': p.description,
        'image_url': f"/uploads/{p.image_url}" if p.image_url else None,
        'category_name': p.category.name if p.category else 'Sem categoria'
    } for p in products])

@public_bp.route('/api/order/<token>')
@csrf.exempt
def api_order_status(token):
    """API para status do pedido"""
    order = Order.query.filter_by(order_token=token).first_or_404()
    return jsonify({
        'id': order.id,
        'status': order.status,
        'total': float(order.total),
        'created_at': order.created_at.isoformat(),
        'payment_method': order.payment_method,
        'customer_name': order.customer.name,
        'items': [{
            'product_name': item.product.name,
            'quantity': item.quantity,
            'unit_price': float(item.unit_price),
            'total': float((item.unit_price * item.quantity) - item.discount)
        } for item in order.order_items]
    })
