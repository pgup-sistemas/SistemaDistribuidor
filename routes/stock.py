from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from models import Product, StockMovement, db
from sqlalchemy import desc

stock_bp = Blueprint('stock', __name__)

@stock_bp.route('/')
@login_required
def index():
    page = request.args.get('page', 1, type=int)
    search = request.args.get('search', '')
    
    query = Product.query.filter_by(active=True)
    
    if search:
        query = query.filter(Product.name.ilike(f'%{search}%'))
    
    products = query.order_by(Product.name).paginate(
        page=page, per_page=20, error_out=False)
    
    return render_template('stock/index.html', products=products, search=search)

@stock_bp.route('/movements')
@login_required
def movements():
    page = request.args.get('page', 1, type=int)
    product_id = request.args.get('product_id', type=int)
    
    query = StockMovement.query
    
    if product_id:
        query = query.filter_by(product_id=product_id)
    
    movements = query.order_by(desc(StockMovement.created_at)).paginate(
        page=page, per_page=20, error_out=False)
    
    products = Product.query.filter_by(active=True).all()
    
    return render_template('stock/movements.html', 
                         movements=movements, 
                         products=products,
                         selected_product=product_id)

@stock_bp.route('/movement/new', methods=['GET', 'POST'])
@login_required
def new_movement():
    if request.method == 'POST':
        product_id = request.form.get('product_id', type=int)
        movement_type = request.form.get('movement_type')
        quantity = request.form.get('quantity', type=int)
        reason = request.form.get('reason')
        
        if not all([product_id, movement_type, quantity, reason]):
            flash('Todos os campos são obrigatórios.', 'error')
            return render_template('stock/movement.html',
                                 products=Product.query.filter_by(active=True).all())
        
        product = Product.query.get_or_404(product_id)
        
        if movement_type not in ['entry', 'exit', 'adjustment']:
            flash('Tipo de movimentação inválido.', 'error')
            return render_template('stock/movement.html',
                                 products=Product.query.filter_by(active=True).all())
        
        if quantity <= 0:
            flash('Quantidade deve ser maior que zero.', 'error')
            return render_template('stock/movement.html',
                                 products=Product.query.filter_by(active=True).all())
        
        # Check if exit movement doesn't exceed stock
        if movement_type == 'exit' and product.current_stock < quantity:
            flash('Quantidade não pode ser maior que o estoque atual.', 'error')
            return render_template('stock/movement.html',
                                 products=Product.query.filter_by(active=True).all())
        
        # Update product stock
        if movement_type == 'entry':
            product.current_stock += quantity
        elif movement_type == 'exit':
            product.current_stock -= quantity
        else:  # adjustment
            product.current_stock = quantity
        
        # Create movement record
        movement = StockMovement(
            product_id=product_id,
            movement_type=movement_type,
            quantity=quantity,
            reason=reason,
            user_id=current_user.id
        )
        
        db.session.add(movement)
        db.session.commit()
        
        flash('Movimentação registrada com sucesso!', 'success')
        return redirect(url_for('stock.movements'))
    
    products = Product.query.filter_by(active=True).all()
    return render_template('stock/movement.html', products=products)

@stock_bp.route('/alerts')
@login_required
def alerts():
    # Products with low stock
    low_stock_products = Product.query.filter(
        Product.current_stock <= Product.minimum_stock,
        Product.active == True
    ).all()
    
    return render_template('stock/alerts.html', products=low_stock_products)
