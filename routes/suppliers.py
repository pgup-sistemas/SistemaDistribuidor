from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from models import Supplier, db

suppliers_bp = Blueprint('suppliers', __name__)

@suppliers_bp.route('/')
@login_required
def index():
    if current_user.role not in ['admin', 'manager']:
        flash('Acesso negado.', 'error')
        return redirect(url_for('dashboard.index'))
    
    search = request.args.get('search', '')
    page = request.args.get('page', 1, type=int)
    
    query = Supplier.query.filter_by(active=True)
    
    if search:
        query = query.filter(Supplier.name.ilike(f'%{search}%'))
    
    suppliers = query.order_by(Supplier.name).paginate(
        page=page, per_page=20, error_out=False)
    
    return render_template('suppliers/index.html', suppliers=suppliers, search=search)

@suppliers_bp.route('/new', methods=['GET', 'POST'])
@login_required
def new():
    if current_user.role not in ['admin', 'manager']:
        flash('Acesso negado.', 'error')
        return redirect(url_for('dashboard.index'))
    
    if request.method == 'POST':
        name = request.form.get('name')
        contact_name = request.form.get('contact_name')
        phone = request.form.get('phone')
        email = request.form.get('email')
        address = request.form.get('address')
        
        if not name:
            flash('Nome é obrigatório.', 'error')
            return render_template('suppliers/form.html')
        
        # Check if supplier already exists
        if Supplier.query.filter_by(name=name, active=True).first():
            flash('Fornecedor com este nome já existe.', 'error')
            return render_template('suppliers/form.html')
        
        supplier = Supplier(
            name=name,
            contact_name=contact_name,
            phone=phone,
            email=email,
            address=address
        )
        
        db.session.add(supplier)
        db.session.commit()
        
        flash('Fornecedor criado com sucesso!', 'success')
        return redirect(url_for('suppliers.index'))
    
    return render_template('suppliers/form.html')

@suppliers_bp.route('/<int:id>/edit', methods=['GET', 'POST'])
@login_required
def edit(id):
    if current_user.role not in ['admin', 'manager']:
        flash('Acesso negado.', 'error')
        return redirect(url_for('dashboard.index'))
    
    supplier = Supplier.query.get_or_404(id)
    
    if request.method == 'POST':
        supplier.name = request.form.get('name')
        supplier.contact_name = request.form.get('contact_name')
        supplier.phone = request.form.get('phone')
        supplier.email = request.form.get('email')
        supplier.address = request.form.get('address')
        
        if not supplier.name:
            flash('Nome é obrigatório.', 'error')
            return render_template('suppliers/form.html', supplier=supplier)
        
        db.session.commit()
        flash('Fornecedor atualizado com sucesso!', 'success')
        return redirect(url_for('suppliers.index'))
    
    return render_template('suppliers/form.html', supplier=supplier)

@suppliers_bp.route('/<int:id>/delete', methods=['POST'])
@login_required
def delete(id):
    if current_user.role not in ['admin', 'manager']:
        flash('Acesso negado.', 'error')
        return redirect(url_for('dashboard.index'))
    
    supplier = Supplier.query.get_or_404(id)
    supplier.active = False
    db.session.commit()
    
    flash('Fornecedor removido com sucesso!', 'success')
    return redirect(url_for('suppliers.index'))