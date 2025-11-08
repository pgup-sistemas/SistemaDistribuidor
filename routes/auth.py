import re
from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from flask_login import login_user, logout_user, login_required, current_user
from flask_wtf.csrf import validate_csrf
from werkzeug.security import check_password_hash, generate_password_hash
from models import User, db
from app import limiter
from services.email_service import EmailService
from datetime import datetime, timedelta

auth_bp = Blueprint('auth', __name__)

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

@auth_bp.route('/login', methods=['GET', 'POST'])
@limiter.limit("5 per minute", methods=["POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard.index'))

    if request.method == 'POST':
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password')
        remember = bool(request.form.get('remember'))

        if not email or not password:
            flash('Email e senha são obrigatórios.', 'error')
            return render_template('auth/login.html')

        user = User.query.filter_by(email=email, active=True).first()

        if user and check_password_hash(user.password_hash, password):
            login_user(user, remember=remember)
            next_page = request.args.get('next')
            flash(f'Bem-vindo, {user.name}!', 'success')
            print(f"Login successful for user: {user.name}, redirecting to dashboard")
            return redirect(next_page or url_for('dashboard.index'))
        else:
            flash('Email ou senha incorretos.', 'error')
            print("Login failed: invalid credentials")

    return render_template('auth/login.html')

@auth_bp.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Logout realizado com sucesso.', 'info')
    return redirect(url_for('auth.login'))

@auth_bp.route('/forgot_password', methods=['GET', 'POST'])
def forgot_password():
    """Solicitar redefinição de senha"""
    if current_user.is_authenticated:
        return redirect(url_for('dashboard.index'))
        
    if request.method == 'POST':
        email = request.form.get('email', '').strip().lower()
        
        if not email:
            flash('Email é obrigatório.', 'error')
            return render_template('auth/forgot_password.html')
        
        user = User.query.filter_by(email=email, active=True).first()
        
        if user:
            email_service = EmailService()
            if email_service.send_password_reset(user):
                flash('Instruções de redefinição de senha foram enviadas para seu email.', 'success')
            else:
                flash('Erro ao enviar email. Tente novamente.', 'error')
        else:
            # Não revelar se o email existe ou não
            flash('Se o email existir em nossa base, você receberá as instruções em breve.', 'info')
        
        return redirect(url_for('auth.login'))
        
    return render_template('auth/forgot_password.html')

@auth_bp.route('/reset_password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    """Redefinir senha com token"""
    if current_user.is_authenticated:
        return redirect(url_for('dashboard.index'))
        
    try:
        # Validar token (expira em 1 hora)
        email_service = EmailService()
        email = email_service.token_serializer.loads(
            token,
            salt='password-reset-salt',
            max_age=3600
        )
        
        user = User.query.filter_by(email=email, active=True).first()
        
        if not user:
            flash('Link inválido ou expirado.', 'error')
            return redirect(url_for('auth.login'))
            
        if request.method == 'POST':
            password = request.form.get('password')
            confirm_password = request.form.get('confirm_password')
            
            if not password or not confirm_password:
                flash('Senha e confirmação são obrigatórias.', 'error')
                return render_template('auth/reset_password.html')
                
            if password != confirm_password:
                flash('As senhas não conferem.', 'error')
                return render_template('auth/reset_password.html')
                
            is_valid, msg = validate_password(password)
            if not is_valid:
                flash(msg, 'error')
                return render_template('auth/reset_password.html')
            
            user.password_hash = generate_password_hash(password)
            db.session.commit()
            
            flash('Senha redefinida com sucesso! Você pode fazer login agora.', 'success')
            return redirect(url_for('auth.login'))
            
        return render_template('auth/reset_password.html')
        
    except Exception as e:
        flash('Link inválido ou expirado.', 'error')
        return redirect(url_for('auth.login'))
