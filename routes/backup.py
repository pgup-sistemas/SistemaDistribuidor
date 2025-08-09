from flask import Blueprint, render_template, request, redirect, url_for, flash, send_file
from flask_login import login_required, current_user
from services.backup_service import BackupService
import os

backup_bp = Blueprint('backup', __name__)

@backup_bp.route('/')
@login_required
def index():
    if current_user.role not in ['admin', 'manager']:
        flash('Acesso negado.', 'error')
        return redirect(url_for('dashboard.index'))
    
    backup_service = BackupService()
    backups = backup_service.list_backups()
    
    return render_template('backup/index.html', backups=backups)

@backup_bp.route('/create', methods=['POST'])
@login_required
def create():
    if current_user.role not in ['admin', 'manager']:
        flash('Acesso negado.', 'error')
        return redirect(url_for('dashboard.index'))
    
    try:
        backup_service = BackupService()
        backup_file = backup_service.create_backup()
        flash(f'Backup criado com sucesso: {backup_file}', 'success')
    except Exception as e:
        flash(f'Erro ao criar backup: {str(e)}', 'error')
    
    return redirect(url_for('backup.index'))

@backup_bp.route('/download/<filename>')
@login_required
def download(filename):
    if current_user.role not in ['admin', 'manager']:
        flash('Acesso negado.', 'error')
        return redirect(url_for('dashboard.index'))
    
    try:
        backup_service = BackupService()
        backup_path = backup_service.get_backup_path(filename)
        
        if os.path.exists(backup_path):
            return send_file(backup_path, as_attachment=True)
        else:
            flash('Arquivo de backup não encontrado.', 'error')
    except Exception as e:
        flash(f'Erro ao baixar backup: {str(e)}', 'error')
    
    return redirect(url_for('backup.index'))
