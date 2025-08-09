from flask import Blueprint, render_template, request, redirect, url_for, flash, make_response
from flask_login import login_required, current_user
from models import Order, OrderItem, Customer, Product, StockMovement, db
from services.whatsapp_service import WhatsAppService
from services.print_service import PrintService
from decimal import Decimal
import json

orders_bp = Blueprint('orders', __name__)

@orders_bp.route('/')
@login_required
def index():
    page = request.args.get('page', 1, type=int)
    status = request.args.get('status', '')
    
    query = Order.query
    
    if status:
        query = query.filter_by(status=status)
    
    orders = query.order_by(Order.created_at.desc()).paginate(
        page=page, per_page=20, error_out=False)
    
    return render_template('orders/index.html', orders=orders, selected_status=status)

@orders_bp.route('/new', methods=['GET', 'POST'])
@login_required
def new():
    # Get pre-selected customer from URL
    selected_customer_id = request.args.get('customer_id', type=int)
    
    if request.method == 'POST':
        customer_id = request.form.get('customer_id', type=int)
        payment_method = request.form.get('payment_method')
        notes = request.form.get('notes')
        items_data = request.form.get('items_data')
        
        if not customer_id or not payment_method:
            flash('Cliente e método de pagamento são obrigatórios.', 'error')
            return render_template('orders/form.html',
                                 customers=Customer.query.filter_by(active=True).all(),
                                 products=Product.query.filter_by(active=True).all())
        
        try:
            items = json.loads(items_data) if items_data else []
            
            if not items:
                flash('É necessário adicionar pelo menos um item ao pedido.', 'error')
                return render_template('orders/form.html',
                                     customers=Customer.query.filter_by(active=True).all(),
                                     products=Product.query.filter_by(active=True).all())
            
            # Calculate total
            total = Decimal('0.00')
            order_items = []
            
            for item in items:
                product = Product.query.get(item['product_id'])
                if not product:
                    flash(f'Produto ID {item["product_id"]} não encontrado.', 'error')
                    return render_template('orders/form.html',
                                         customers=Customer.query.filter_by(active=True).all(),
                                         products=Product.query.filter_by(active=True).all())
                
                quantity = int(item['quantity'])
                unit_price = Decimal(str(item['unit_price']))
                discount = Decimal(str(item.get('discount', 0)))
                
                # Check stock
                if product.current_stock < quantity:
                    flash(f'Estoque insuficiente para {product.name}. Disponível: {product.current_stock}', 'error')
                    return render_template('orders/form.html',
                                         customers=Customer.query.filter_by(active=True).all(),
                                         products=Product.query.filter_by(active=True).all())
                
                item_total = (unit_price * quantity) - discount
                total += item_total
                
                order_items.append({
                    'product': product,
                    'quantity': quantity,
                    'unit_price': unit_price,
                    'discount': discount
                })
            
            # Create order
            order = Order(
                customer_id=customer_id,
                user_id=current_user.id,
                total=total,
                payment_method=payment_method,
                notes=notes,
                status='confirmed'
            )
            
            db.session.add(order)
            db.session.flush()  # To get the order ID
            
            # Add order items and update stock
            for item in order_items:
                order_item = OrderItem(
                    order_id=order.id,
                    product_id=item['product'].id,
                    quantity=item['quantity'],
                    unit_price=item['unit_price'],
                    discount=item['discount']
                )
                db.session.add(order_item)
                
                # Update stock
                item['product'].current_stock -= item['quantity']
                
                # Create stock movement
                stock_movement = StockMovement(
                    product_id=item['product'].id,
                    movement_type='exit',
                    quantity=item['quantity'],
                    reason=f'Venda - Pedido #{order.id}',
                    user_id=current_user.id
                )
                db.session.add(stock_movement)
            
            db.session.commit()
            
            flash('Pedido criado com sucesso!', 'success')
            return redirect(url_for('orders.view', id=order.id))
            
        except (ValueError, json.JSONDecodeError) as e:
            flash('Dados do pedido inválidos.', 'error')
            return render_template('orders/form.html',
                                 customers=Customer.query.filter_by(active=True).all(),
                                 products=Product.query.filter_by(active=True).all())
    
    customers = Customer.query.filter_by(active=True).all()
    products = Product.query.filter_by(active=True).all()
    
    return render_template('orders/form.html', 
                         customers=customers, 
                         products=products,
                         selected_customer_id=selected_customer_id)

@orders_bp.route('/<int:id>')
@login_required
def view(id):
    order = Order.query.get_or_404(id)
    return render_template('orders/view.html', order=order)

@orders_bp.route('/<int:id>/print')
@login_required
def print_receipt(id):
    order = Order.query.get_or_404(id)
    
    # Generate PDF receipt
    print_service = PrintService()
    pdf_content = print_service.generate_receipt(order)
    
    response = make_response(pdf_content)
    response.headers['Content-Type'] = 'application/pdf'
    response.headers['Content-Disposition'] = f'inline; filename=pedido_{order.id}.pdf'
    
    return response

@orders_bp.route('/<int:id>/whatsapp')
@login_required
def send_whatsapp(id):
    order = Order.query.get_or_404(id)
    
    whatsapp_service = WhatsAppService()
    whatsapp_url = whatsapp_service.generate_order_link(order)
    
    return redirect(whatsapp_url)

@orders_bp.route('/<int:id>/status', methods=['POST'])
@login_required
def update_status(id):
    order = Order.query.get_or_404(id)
    new_status = request.form.get('status')
    
    if new_status in ['pending', 'confirmed', 'preparing', 'delivered', 'cancelled']:
        order.status = new_status
        db.session.commit()
        flash('Status do pedido atualizado!', 'success')
    else:
        flash('Status inválido.', 'error')
    
    return redirect(url_for('orders.view', id=id))
