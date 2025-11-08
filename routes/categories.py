from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from models import Category, db
import re

categories_bp = Blueprint('categories', __name__)

def validate_category_data(name, description=None):
    """Validações enterprise para dados de categoria"""
    errors = []

    if not name or len(name.strip()) < 2:
        errors.append("Nome da categoria deve ter pelo menos 2 caracteres")
    elif len(name.strip()) > 50:
        errors.append("Nome da categoria não pode exceder 50 caracteres")

    # Validar caracteres especiais no nome
    if re.search(r'[<>"/\\|?*]', name):
        errors.append("Nome da categoria não pode conter caracteres especiais (< > \" / \\ | ? *)")

    if description and len(description.strip()) > 200:
        errors.append("Descrição não pode exceder 200 caracteres")

    return errors

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
        name = request.form.get('name', '').strip()
        description = request.form.get('description', '').strip()

        # Validações enterprise
        validation_errors = validate_category_data(name, description)

        if validation_errors:
            for error in validation_errors:
                flash(error, 'error')
            return render_template('categories/form.html')

        # Check if category already exists (case-insensitive)
        existing_category = Category.query.filter(
            db.func.upper(Category.name) == name.upper(),
            Category.active == True
        ).first()

        if existing_category:
            flash(f'Categoria "{name}" já existe.', 'error')
            return render_template('categories/form.html')
        
        category = Category(
            name=name,
            description=description
        )

        db.session.add(category)
        db.session.commit()

        flash(f'Categoria "{category.name}" criada com sucesso!', 'success')
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
        new_name = request.form.get('name', '').strip()
        new_description = request.form.get('description', '').strip()

        # Validações enterprise
        validation_errors = validate_category_data(new_name, new_description)

        if validation_errors:
            for error in validation_errors:
                flash(error, 'error')
            return render_template('categories/form.html', category=category)

        # Verificar se nome mudou e se já existe
        if new_name.upper() != category.name.upper():
            existing_category = Category.query.filter(
                db.func.upper(Category.name) == new_name.upper(),
                Category.active == True,
                Category.id != category.id
            ).first()

            if existing_category:
                flash(f'Categoria "{new_name}" já existe.', 'error')
                return render_template('categories/form.html', category=category)

        # Aplicar mudanças
        category.name = new_name
        category.description = new_description

        db.session.commit()
        flash(f'Categoria "{category.name}" atualizada com sucesso!', 'success')
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

    flash(f'Categoria "{category.name}" removida com sucesso!', 'success')
    return redirect(url_for('categories.index'))