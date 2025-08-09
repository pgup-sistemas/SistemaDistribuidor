from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from werkzeug.security import generate_password_hash
from models import User, db

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
        name = request.form.get('name')
        email = request.form.get('email')
        password = request.form.get('password')
        role = request.form.get('role')
        
        if not all([name, email, password, role]):
            flash('Todos os campos são obrigatórios.', 'error')
            return render_template('users/form.html')
        
        if role not in ['admin', 'attendant', 'stock_manager', 'delivery', 'manager']:
            flash('Função inválida.', 'error')
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
        
        db.session.add(user)
        db.session.commit()
        
        flash('Usuário criado com sucesso!', 'success')
        return redirect(url_for('users.index'))
    
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
