from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from models import Customer, Order, db
from sqlalchemy import func

customers_bp = Blueprint('customers', __name__)

@customers_bp.route('/')
@login_required
def index():
    page = request.args.get('page', 1, type=int)
    search = request.args.get('search', '')
    
    query = Customer.query.filter_by(active=True)
    
    if search:
        query = query.filter(Customer.name.ilike(f'%{search}%'))
    
    customers = query.order_by(Customer.name).paginate(
        page=page, per_page=20, error_out=False)
    
    return render_template('customers/index.html', customers=customers, search=search)

@customers_bp.route('/new', methods=['GET', 'POST'])
@login_required
def new():
    if request.method == 'POST':
        name = request.form.get('name')
        document = request.form.get('document')
        phone = request.form.get('phone')
        email = request.form.get('email')
        address = request.form.get('address')
        notes = request.form.get('notes')
        
        if not name:
            flash('Nome é obrigatório.', 'error')
            return render_template('customers/form.html')
        
        # Check if customer already exists
        if Customer.query.filter_by(name=name, active=True).first():
            flash('Cliente com este nome já existe.', 'error')
            return render_template('customers/form.html')
        
        customer = Customer(
            name=name,
            document=document,
            phone=phone,
            email=email,
            address=address,
            notes=notes
        )
        
        db.session.add(customer)
        db.session.commit()
        
        flash('Cliente cadastrado com sucesso!', 'success')
        return redirect(url_for('customers.index'))
    
    return render_template('customers/form.html')

@customers_bp.route('/<int:id>/edit', methods=['GET', 'POST'])
@login_required
def edit(id):
    customer = Customer.query.get_or_404(id)
    
    if request.method == 'POST':
        customer.name = request.form.get('name')
        customer.document = request.form.get('document')
        customer.phone = request.form.get('phone')
        customer.email = request.form.get('email')
        customer.address = request.form.get('address')
        customer.notes = request.form.get('notes')
        
        if not customer.name:
            flash('Nome é obrigatório.', 'error')
            return render_template('customers/form.html', customer=customer)
        
        db.session.commit()
        flash('Cliente atualizado com sucesso!', 'success')
        return redirect(url_for('customers.index'))
    
    return render_template('customers/form.html', customer=customer)

@customers_bp.route('/<int:id>/delete', methods=['POST'])
@login_required
def delete(id):
    customer = Customer.query.get_or_404(id)
    
    # Check if customer has orders
    if Order.query.filter_by(customer_id=id).first():
        flash('Não é possível excluir cliente com pedidos cadastrados.', 'error')
    else:
        customer.active = False
        db.session.commit()
        flash('Cliente removido com sucesso!', 'success')
    
    return redirect(url_for('customers.index'))

@customers_bp.route('/<int:id>/orders')
@login_required
def orders(id):
    customer = Customer.query.get_or_404(id)
    page = request.args.get('page', 1, type=int)
    
    orders = Order.query.filter_by(customer_id=id).order_by(
        Order.created_at.desc()).paginate(
        page=page, per_page=10, error_out=False)
    
    return render_template('customers/orders.html', customer=customer, orders=orders)
