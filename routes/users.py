import re
from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from werkzeug.security import generate_password_hash
from models import User, db

def validate_password(password):
    """Validate password strength"""
    if len(password) < 8:
        return False, "Senha deve ter pelo menos 8 caracteres."

    if not re.search(r'[A-Z]', password):
        return False, "Senha deve conter pelo menos uma letra maiúscula."

    if not re.search(r'[a-z]', password):
        return False, "Senha deve conter pelo menos uma letra minúscula."

    if not re.search(r'[0-9]', password):
        return False, "Senha deve conter pelo menos um número."

    return True, "Senha válida."

users_bp = Blueprint('users', __name__)

@users_bp.route('/')
@login_required
def index():
    if current_user.role != 'admin':
        flash('Acesso negado.', 'error')
        return redirect(url_for('dashboard.index'))
    
    users = User.query.filter_by(active=True).order_by(User.name).all()
    return render_template('users/index.html', users=users)

@users_bp.route('/new', methods=['GET', 'POST'])
@login_required
def new():
    if current_user.role != 'admin':
        flash('Acesso negado.', 'error')
        return redirect(url_for('dashboard.index'))
    
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')
        role = request.form.get('role', '')

        # Validation
        errors = []

        if not name or len(name) < 2:
            errors.append('Nome deve ter pelo menos 2 caracteres.')

        if not email:
            errors.append('Email é obrigatório.')
        elif not re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', email):
            errors.append('Email inválido.')

        if not password:
            errors.append('Senha é obrigatória.')
        else:
            is_valid, msg = validate_password(password)
            if not is_valid:
                errors.append(msg)

        if role not in ['admin', 'attendant', 'stock_manager', 'delivery', 'manager']:
            errors.append('Função inválida.')

        if errors:
            for error in errors:
                flash(error, 'error')
            return render_template('users/form.html')

        # Check if email already exists
        if User.query.filter_by(email=email, active=True).first():
            flash('Email já está em uso.', 'error')
            return render_template('users/form.html')

        user = User(
            name=name,
            email=email,
            password_hash=generate_password_hash(password),
            role=role
        )

        try:
            db.session.add(user)
            db.session.commit()
            flash('Usuário criado com sucesso!', 'success')
            return redirect(url_for('users.index'))
        except Exception as e:
            db.session.rollback()
            flash('Erro ao criar usuário. Tente novamente.', 'error')
            return render_template('users/form.html')
    
    return render_template('users/form.html')

@users_bp.route('/<int:id>/edit', methods=['GET', 'POST'])
@login_required
def edit(id):
    if current_user.role != 'admin':
        flash('Acesso negado.', 'error')
        return redirect(url_for('dashboard.index'))
    
    user = User.query.get_or_404(id)
    
    if request.method == 'POST':
        user.name = request.form.get('name')
        user.email = request.form.get('email')
        user.role = request.form.get('role')
        password = request.form.get('password')
        
        if not all([user.name, user.email, user.role]):
            flash('Nome, email e função são obrigatórios.', 'error')
            return render_template('users/form.html', user=user)
        
        if user.role not in ['admin', 'attendant', 'stock_manager', 'delivery', 'manager']:
            flash('Função inválida.', 'error')
            return render_template('users/form.html', user=user)
        
        # Update password if provided
        if password:
            user.password_hash = generate_password_hash(password)
        
        db.session.commit()
        flash('Usuário atualizado com sucesso!', 'success')
        return redirect(url_for('users.index'))
    
    return render_template('users/form.html', user=user)

@users_bp.route('/<int:id>/delete', methods=['POST'])
@login_required
def delete(id):
    if current_user.role != 'admin':
        flash('Acesso negado.', 'error')
        return redirect(url_for('dashboard.index'))
    
    user = User.query.get_or_404(id)
    
    if user.id == current_user.id:
        flash('Não é possível excluir seu próprio usuário.', 'error')
    else:
        user.active = False
        db.session.commit()
        flash('Usuário removido com sucesso!', 'success')
    
    return redirect(url_for('users.index'))
