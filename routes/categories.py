from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from models import Category, db

categories_bp = Blueprint('categories', __name__)

@categories_bp.route('/')
@login_required
def index():
    if current_user.role not in ['admin', 'manager']:
        flash('Acesso negado.', 'error')
        return redirect(url_for('dashboard.index'))
    
    search = request.args.get('search', '')
    page = request.args.get('page', 1, type=int)
    
    query = Category.query.filter_by(active=True)
    
    if search:
        query = query.filter(Category.name.ilike(f'%{search}%'))
    
    categories = query.order_by(Category.name).paginate(
        page=page, per_page=20, error_out=False)
    
    return render_template('categories/index.html', categories=categories, search=search)

@categories_bp.route('/new', methods=['GET', 'POST'])
@login_required
def new():
    if current_user.role not in ['admin', 'manager']:
        flash('Acesso negado.', 'error')
        return redirect(url_for('dashboard.index'))
    
    if request.method == 'POST':
        name = request.form.get('name')
        description = request.form.get('description')
        
        if not name:
            flash('Nome é obrigatório.', 'error')
            return render_template('categories/form.html')
        
        # Check if category already exists
        if Category.query.filter_by(name=name, active=True).first():
            flash('Categoria com este nome já existe.', 'error')
            return render_template('categories/form.html')
        
        category = Category(
            name=name,
            description=description
        )
        
        db.session.add(category)
        db.session.commit()
        
        flash('Categoria criada com sucesso!', 'success')
        return redirect(url_for('categories.index'))
    
    return render_template('categories/form.html')

@categories_bp.route('/<int:id>/edit', methods=['GET', 'POST'])
@login_required
def edit(id):
    if current_user.role not in ['admin', 'manager']:
        flash('Acesso negado.', 'error')
        return redirect(url_for('dashboard.index'))
    
    category = Category.query.get_or_404(id)
    
    if request.method == 'POST':
        category.name = request.form.get('name')
        category.description = request.form.get('description')
        
        if not category.name:
            flash('Nome é obrigatório.', 'error')
            return render_template('categories/form.html', category=category)
        
        db.session.commit()
        flash('Categoria atualizada com sucesso!', 'success')
        return redirect(url_for('categories.index'))
    
    return render_template('categories/form.html', category=category)

@categories_bp.route('/<int:id>/delete', methods=['POST'])
@login_required
def delete(id):
    if current_user.role not in ['admin', 'manager']:
        flash('Acesso negado.', 'error')
        return redirect(url_for('dashboard.index'))
    
    category = Category.query.get_or_404(id)
    category.active = False
    db.session.commit()
    
    flash('Categoria removida com sucesso!', 'success')
    return redirect(url_for('categories.index'))