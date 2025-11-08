from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, current_app, Response
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename
import csv
import io
from models import CompanySettings, PublicContent, MediaFile, ContentVersion, AuditLog, db
import json
import os
import uuid
from datetime import datetime
from PIL import Image
import re

admin_public_bp = Blueprint('admin_public', __name__)

# Allowed file extensions for uploads
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp', 'svg', 'pdf', 'doc', 'docx'}
ALLOWED_IMAGE_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}

def allowed_file(filename, allowed_extensions=None):
    """Check if file extension is allowed"""
    if allowed_extensions is None:
        allowed_extensions = ALLOWED_EXTENSIONS
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in allowed_extensions

def allowed_image_file(filename):
    """Check if file is an allowed image"""
    return allowed_file(filename, ALLOWED_IMAGE_EXTENSIONS)

def save_uploaded_file(file, subfolder=''):
    """Save uploaded file and return the path"""
    if not file or not file.filename:
        return None

    filename = secure_filename(file.filename)
    # Add timestamp and UUID to prevent conflicts
    name, ext = os.path.splitext(filename)
    unique_filename = f"{name}_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}_{str(uuid.uuid4())[:8]}{ext}"

    upload_folder = os.path.join(current_app.root_path, 'static', 'uploads', subfolder)
    os.makedirs(upload_folder, exist_ok=True)

    file_path = os.path.join(upload_folder, unique_filename)
    file.save(file_path)

    # Return relative path for database storage
    return f"static/uploads/{subfolder}/{unique_filename}".lstrip('/')

def create_content_version(content_type, content_id, data, change_reason=''):
    """Create a new version of content for audit trail"""
    # Get next version number
    latest_version = ContentVersion.query.filter_by(
        content_type=content_type,
        content_id=content_id
    ).order_by(ContentVersion.version_number.desc()).first()

    version_number = (latest_version.version_number + 1) if latest_version else 1

    version = ContentVersion(
        content_type=content_type,
        content_id=content_id,
        version_number=version_number,
        data=json.dumps(data),
        change_reason=change_reason,
        changed_by=current_user.id
    )
    db.session.add(version)
    return version

# ==========================================
# COMPANY SETTINGS MANAGEMENT
# ==========================================

@admin_public_bp.route('/company-settings')
@login_required
def company_settings_index():
    """Display company settings"""
    if current_user.role not in ['admin', 'manager']:
        flash('Acesso negado. Apenas administradores e gerentes podem acessar as configurações.', 'error')
        return redirect(url_for('dashboard.index'))

    settings = CompanySettings.query.filter_by(active=True).first()
    return render_template('admin_public/company_settings/index.html', settings=settings)

@admin_public_bp.route('/company-settings/edit')
@login_required
def company_settings_edit():
    """Form to edit company settings"""
    if current_user.role not in ['admin', 'manager']:
        flash('Acesso negado. Apenas administradores e gerentes podem editar as configurações.', 'error')
        return redirect(url_for('dashboard.index'))

    settings = CompanySettings.query.filter_by(active=True).first()
    return render_template('admin_public/company_settings/form.html', settings=settings, action='edit')

@admin_public_bp.route('/company-settings/save', methods=['POST'])
@login_required
def company_settings_save():
    """Save company settings"""
    if current_user.role not in ['admin', 'manager']:
        flash('Acesso negado. Apenas administradores e gerentes podem salvar as configurações.', 'error')
        return redirect(url_for('dashboard.index'))

    try:
        # Get existing settings or create new
        settings = CompanySettings.query.filter_by(active=True).first()
        old_data = None

        if settings:
            old_data = {
                'company_name': settings.company_name,
                'tagline': settings.tagline,
                'description': settings.description,
                'phone': settings.phone,
                'email': settings.email
            }
            action = 'UPDATE'
        else:
            settings = CompanySettings()
            db.session.add(settings)
            action = 'CREATE'

        # Basic information
        settings.company_name = request.form.get('company_name', '').strip()
        settings.tagline = request.form.get('tagline', '').strip()
        settings.description = request.form.get('description', '').strip()

        # Contact information
        settings.phone = re.sub(r'\D', '', request.form.get('phone', ''))
        settings.whatsapp = re.sub(r'\D', '', request.form.get('whatsapp', ''))
        settings.email = request.form.get('email', '').strip()
        settings.website = request.form.get('website', '').strip()

        # Address
        settings.address = request.form.get('address', '').strip()
        settings.city = request.form.get('city', '').strip()
        settings.state = request.form.get('state', '').strip()
        settings.zip_code = re.sub(r'\D', '', request.form.get('zip_code', ''))

        # Social media (JSON)
        social_media = {
            'facebook': request.form.get('facebook', '').strip(),
            'instagram': request.form.get('instagram', '').strip(),
            'twitter': request.form.get('twitter', '').strip(),
            'linkedin': request.form.get('linkedin', '').strip()
        }
        settings.social_media = json.dumps(social_media)

        # Business hours (JSON)
        business_hours = {
            'monday': request.form.get('monday', '').strip(),
            'tuesday': request.form.get('tuesday', '').strip(),
            'wednesday': request.form.get('wednesday', '').strip(),
            'thursday': request.form.get('thursday', '').strip(),
            'friday': request.form.get('friday', '').strip(),
            'saturday': request.form.get('saturday', '').strip(),
            'sunday': request.form.get('sunday', '').strip()
        }
        settings.business_hours = json.dumps(business_hours)

        # Branding
        settings.primary_color = request.form.get('primary_color', '').strip()
        settings.secondary_color = request.form.get('secondary_color', '').strip()

        # Settings
        settings.maintenance_mode = bool(request.form.get('maintenance_mode'))
        settings.allow_public_orders = bool(request.form.get('allow_public_orders'))
        settings.timezone = request.form.get('timezone', 'America/Cuiaba')

        # Handle logo upload
        if 'logo' in request.files:
            logo_file = request.files['logo']
            if logo_file and logo_file.filename and allowed_image_file(logo_file.filename):
                logo_path = save_uploaded_file(logo_file, 'logos')
                if logo_path:
                    settings.logo_url = logo_path

        # Handle favicon upload
        if 'favicon' in request.files:
            favicon_file = request.files['favicon']
            if favicon_file and favicon_file.filename and allowed_image_file(favicon_file.filename):
                favicon_path = save_uploaded_file(favicon_file, 'favicons')
                if favicon_path:
                    settings.favicon_url = favicon_path

        db.session.commit()

        # Create version for audit trail
        new_data = {
            'company_name': settings.company_name,
            'tagline': settings.tagline,
            'description': settings.description,
            'phone': settings.phone,
            'email': settings.email
        }
        create_content_version('company_settings', settings.id, new_data, 'Company settings updated')

        # Audit log
        audit_log = AuditLog(
            user_id=current_user.id,
            action=action,
            entity='CompanySettings',
            entity_id=settings.id,
            old_data=json.dumps(old_data) if old_data else None,
            new_data=json.dumps(new_data)
        )
        db.session.add(audit_log)
        db.session.commit()

        flash(f'Configurações da empresa {"atualizadas" if action == "UPDATE" else "criadas"} com sucesso!', 'success')
        return redirect(url_for('admin_public.company_settings_index'))

    except Exception as e:
        db.session.rollback()
        flash(f'Erro ao salvar configurações: {str(e)}', 'error')
        return redirect(url_for('admin_public.company_settings_edit'))

# ==========================================
# PUBLIC CONTENT MANAGEMENT
# ==========================================

@admin_public_bp.route('/content')
@login_required
def content_index():
    """Display public content overview"""
    if current_user.role not in ['admin', 'manager']:
        flash('Acesso negado.', 'error')
        return redirect(url_for('dashboard.index'))

    sections = ['hero', 'features', 'about', 'contact', 'footer']
    content = {}
    for section in sections:
        content[section] = PublicContent.query.filter_by(
            section=section, active=True
        ).order_by(PublicContent.order).all()

    return render_template('admin_public/content/index.html', content=content)

@admin_public_bp.route('/content/<section>')
@login_required
def content_section(section):
    """Display content for a specific section"""
    if current_user.role not in ['admin', 'manager']:
        flash('Acesso negado.', 'error')
        return redirect(url_for('dashboard.index'))

    if section not in ['hero', 'features', 'about', 'contact', 'footer']:
        flash('Seção inválida.', 'error')
        return redirect(url_for('admin_public.content_index'))

    content_items = PublicContent.query.filter_by(
        section=section, active=True
    ).order_by(PublicContent.order).all()

    # Build a lightweight section object for templates (keeps templates working with object-like access)
    section_obj = {
        'id': section,
        'name': section.title(),
        'icon': 'file-alt',
        'description': '',
        'status': 'active',
        'content_count': len(content_items),
        'updated_at': max([item.updated_at for item in content_items]) if content_items else None
    }

    return render_template('admin_public/content/section.html',
                         section=section_obj, content_items=content_items)

@admin_public_bp.route('/content/<section>/new')
@login_required
def content_new(section):
    """Form to create new content"""
    if current_user.role not in ['admin', 'manager']:
        flash('Acesso negado.', 'error')
        return redirect(url_for('dashboard.index'))

    if section not in ['hero', 'features', 'about', 'contact', 'footer']:
        flash('Seção inválida.', 'error')
        return redirect(url_for('admin_public.content_index'))

    return render_template('admin_public/content/form.html',
                         section=section, action='new')

@admin_public_bp.route('/content/<section>/create', methods=['POST'])
@login_required
def content_create(section):
    """Create new content"""
    if current_user.role not in ['admin', 'manager']:
        flash('Acesso negado.', 'error')
        return redirect(url_for('dashboard.index'))

    if section not in ['hero', 'features', 'about', 'contact', 'footer']:
        flash('Seção inválida.', 'error')
        return redirect(url_for('admin_public.content_index'))

    try:
        content = PublicContent(
            section=section,
            title=request.form.get('title', '').strip(),
            content=request.form.get('content', '').strip(),
            order=int(request.form.get('order', 0))
        )

        # Handle image upload
        if 'image' in request.files:
            image_file = request.files['image']
            if image_file and image_file.filename and allowed_image_file(image_file.filename):
                image_path = save_uploaded_file(image_file, f'content/{section}')
                if image_path:
                    content.image_url = image_path

        db.session.add(content)
        db.session.commit()

        # Create version for audit trail
        content_data = {
            'section': content.section,
            'title': content.title,
            'content': content.content,
            'order': content.order,
            'image_url': content.image_url
        }
        create_content_version('public_content', content.id, content_data, 'Content created')

        # Audit log
        audit_log = AuditLog(
            user_id=current_user.id,
            action='CREATE',
            entity='PublicContent',
            entity_id=content.id,
            new_data=json.dumps(content_data)
        )
        db.session.add(audit_log)
        db.session.commit()

        flash('Conteúdo criado com sucesso!', 'success')
        return redirect(url_for('admin_public.content_section', section=section))

    except Exception as e:
        db.session.rollback()
        flash(f'Erro ao criar conteúdo: {str(e)}', 'error')
        return redirect(url_for('admin_public.content_new', section=section))

@admin_public_bp.route('/content/<int:id>/edit')
@login_required
def content_edit(id):
    """Form to edit content"""
    if current_user.role not in ['admin', 'manager']:
        flash('Acesso negado.', 'error')
        return redirect(url_for('dashboard.index'))

    content = PublicContent.query.get_or_404(id)
    return render_template('admin_public/content/form.html',
                         content=content, section=content.section, action='edit')

@admin_public_bp.route('/content/<int:id>/update', methods=['POST'])
@login_required
def content_update(id):
    """Update content"""
    if current_user.role not in ['admin', 'manager']:
        flash('Acesso negado.', 'error')
        return redirect(url_for('dashboard.index'))

    content = PublicContent.query.get_or_404(id)
    old_data = {
        'section': content.section,
        'title': content.title,
        'content': content.content,
        'order': content.order,
        'image_url': content.image_url
    }

    try:
        content.title = request.form.get('title', '').strip()
        content.content = request.form.get('content', '').strip()
        content.order = int(request.form.get('order', 0))

        # Handle image upload
        if 'image' in request.files:
            image_file = request.files['image']
            if image_file and image_file.filename and allowed_image_file(image_file.filename):
                image_path = save_uploaded_file(image_file, f'content/{content.section}')
                if image_path:
                    content.image_url = image_path

        db.session.commit()

        # Create version for audit trail
        new_data = {
            'section': content.section,
            'title': content.title,
            'content': content.content,
            'order': content.order,
            'image_url': content.image_url
        }
        create_content_version('public_content', content.id, new_data, 'Content updated')

        # Audit log
        audit_log = AuditLog(
            user_id=current_user.id,
            action='UPDATE',
            entity='PublicContent',
            entity_id=content.id,
            old_data=json.dumps(old_data),
            new_data=json.dumps(new_data)
        )
        db.session.add(audit_log)
        db.session.commit()

        flash('Conteúdo atualizado com sucesso!', 'success')
        return redirect(url_for('admin_public.content_section', section=content.section))

    except Exception as e:
        db.session.rollback()
        flash(f'Erro ao atualizar conteúdo: {str(e)}', 'error')
        return redirect(url_for('admin_public.content_edit', id=id))

@admin_public_bp.route('/content/<int:id>/delete', methods=['POST'])
@login_required
def content_delete(id):
    """Delete content"""
    if current_user.role not in ['admin', 'manager']:
        flash('Acesso negado.', 'error')
        return redirect(url_for('dashboard.index'))

    content = PublicContent.query.get_or_404(id)
    section = content.section

    try:
        # Create version for audit trail before deletion
        content_data = {
            'section': content.section,
            'title': content.title,
            'content': content.content,
            'order': content.order,
            'image_url': content.image_url
        }
        create_content_version('public_content', content.id, content_data, 'Content deleted')

        # Audit log
        audit_log = AuditLog(
            user_id=current_user.id,
            action='DELETE',
            entity='PublicContent',
            entity_id=content.id,
            old_data=json.dumps(content_data)
        )
        db.session.add(audit_log)

        # Soft delete
        content.active = False
        db.session.commit()

        flash('Conteúdo removido com sucesso!', 'success')
        return redirect(url_for('admin_public.content_section', section=section))

    except Exception as e:
        db.session.rollback()
        flash(f'Erro ao remover conteúdo: {str(e)}', 'error')
        return redirect(url_for('admin_public.content_section', section=section))

# ==========================================
# MEDIA FILE MANAGEMENT
# ==========================================

@admin_public_bp.route('/media')
@login_required
def media_index():
    """Display media files"""
    if current_user.role not in ['admin', 'manager']:
        flash('Acesso negado.', 'error')
        return redirect(url_for('dashboard.index'))

    page = int(request.args.get('page', 1))
    per_page = 20
    file_type = request.args.get('type', '')

    query = MediaFile.query
    if file_type:
        query = query.filter_by(file_type=file_type)

    media_files = query.order_by(MediaFile.uploaded_at.desc()).paginate(
        page=page, per_page=per_page, error_out=False
    )

    return render_template('admin_public/media/index.html',
                         media_files=media_files, file_type=file_type)

@admin_public_bp.route('/media/upload', methods=['POST'])
@login_required
def media_upload():
    """Upload media file"""
    if current_user.role not in ['admin', 'manager']:
        return jsonify({'error': 'Acesso negado'}), 403

    try:
        if 'file' not in request.files:
            return jsonify({'error': 'Nenhum arquivo enviado'}), 400

        file = request.files['file']
        if not file or not file.filename:
            return jsonify({'error': 'Arquivo inválido'}), 400

        if not allowed_file(file.filename):
            return jsonify({'error': 'Tipo de arquivo não permitido'}), 400

        # Determine file type
        filename = file.filename.lower()
        if any(filename.endswith(ext) for ext in ['.png', '.jpg', '.jpeg', '.gif', '.webp', '.svg']):
            file_type = 'image'
        elif any(filename.endswith(ext) for ext in ['.pdf']):
            file_type = 'document'
        elif any(filename.endswith(ext) for ext in ['.mp4', '.avi', '.mov']):
            file_type = 'video'
        elif any(filename.endswith(ext) for ext in ['.mp3', '.wav']):
            file_type = 'audio'
        else:
            file_type = 'other'

        # Save file
        subfolder = file_type + 's'  # images, documents, videos, audios
        file_path = save_uploaded_file(file, subfolder)

        if not file_path:
            return jsonify({'error': 'Erro ao salvar arquivo'}), 500

        # Create database record
        media_file = MediaFile(
            filename=os.path.basename(file_path),
            original_filename=file.filename,
            file_path=file_path,
            file_type=file_type,
            mime_type=file.mimetype,
            file_size=os.path.getsize(os.path.join(current_app.root_path, file_path)),
            alt_text=request.form.get('alt_text', ''),
            description=request.form.get('description', ''),
            uploaded_by=current_user.id
        )

        db.session.add(media_file)
        db.session.commit()

        return jsonify({
            'success': True,
            'id': media_file.id,
            'filename': media_file.filename,
            'file_path': file_path,
            'file_type': file_type
        })

    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@admin_public_bp.route('/media/<int:id>/delete', methods=['POST'])
@login_required
def media_delete(id):
    """Delete media file"""
    if current_user.role not in ['admin', 'manager']:
        return jsonify({'error': 'Acesso negado'}), 403

    try:
        media_file = MediaFile.query.get_or_404(id)

        # Delete physical file
        file_path = os.path.join(current_app.root_path, media_file.file_path)
        if os.path.exists(file_path):
            os.remove(file_path)

        # Delete database record
        db.session.delete(media_file)
        db.session.commit()

        return jsonify({'success': True})

    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

# ==========================================
# CONTENT VERSIONING AND AUDIT
# ==========================================

@admin_public_bp.route('/versions')
@login_required
def versions_overview():
    """Display all version history overview"""
    if current_user.role not in ['admin', 'manager']:
        flash('Acesso negado.', 'error')
        return redirect(url_for('dashboard.index'))

    # Get recent versions from all content types
    versions = ContentVersion.query.order_by(
        ContentVersion.created_at.desc()
    ).limit(50).all()

    return render_template('admin_public/versions/index.html',
                         versions=versions, content_type='all', content_id=0)

@admin_public_bp.route('/versions/<content_type>/<int:content_id>')
@login_required
def content_versions(content_type, content_id):
    """Display version history for specific content"""
    if current_user.role not in ['admin', 'manager']:
        flash('Acesso negado.', 'error')
        return redirect(url_for('dashboard.index'))

    versions = ContentVersion.query.filter_by(
        content_type=content_type,
        content_id=content_id
    ).order_by(ContentVersion.version_number.desc()).all()

    return render_template('admin_public/versions/index.html',
                         versions=versions, content_type=content_type, content_id=content_id)

@admin_public_bp.route('/versions/<int:version_id>')
@login_required
def content_version_detail(version_id):
    """Display version details"""
    if current_user.role not in ['admin', 'manager']:
        flash('Acesso negado.', 'error')
        return redirect(url_for('dashboard.index'))

    version = ContentVersion.query.get_or_404(version_id)
    return render_template('admin_public/versions/detail.html', version=version)

@admin_public_bp.route('/versions/<int:version_id>/rollback', methods=['POST'])
@login_required
def versions_rollback(version_id):
    """Rollback content to a specific version"""
    if current_user.role not in ['admin', 'manager']:
        flash('Acesso negado.', 'error')
        return redirect(url_for('dashboard.index'))

    version = ContentVersion.query.get_or_404(version_id)
    content_data = json.loads(version.content_data)
    
    # Get the current content
    if version.content_type == 'public_content':
        content = PublicContent.query.get_or_404(version.content_id)
        content.title = content_data.get('title', content.title)
        content.content = content_data.get('content', content.content)
        content.section = content_data.get('section', content.section)
        content.order = content_data.get('order', content.order)
    else:
        flash('Tipo de conteúdo não suportado para rollback.', 'error')
        return redirect(url_for('admin_public.content_version_detail', version_id=version_id))
    
    try:
        db.session.commit()
        create_content_version(version.content_type, version.content_id, content_data, 
                             f'Rollback to version from {version.created_at}')
        flash('Conteúdo restaurado com sucesso.', 'success')
    except Exception as e:
        db.session.rollback()
        flash('Erro ao restaurar conteúdo.', 'error')
        current_app.logger.error(f'Error in rollback: {str(e)}')
    
    return redirect(url_for('admin_public.content_versions', 
                          content_type=version.content_type, 
                          content_id=version.content_id))

@admin_public_bp.route('/audit')
@login_required
def audit_log():
    """Display audit log"""
    if current_user.role not in ['admin', 'manager']:
        flash('Acesso negado.', 'error')
        return redirect(url_for('dashboard.index'))

    # Get page number from query parameters
    page = request.args.get('page', 1, type=int)
    per_page = 50  # Number of items per page

    # Get search parameters
    search_email = request.args.get('email', '')
    search_action = request.args.get('action', '')
    search_date_start = request.args.get('date_start', '')
    search_date_end = request.args.get('date_end', '')

    # Base query
    query = AuditLog.query

    # Apply filters if provided
    if search_email:
        query = query.filter(AuditLog.user_email.ilike(f'%{search_email}%'))
    if search_action:
        query = query.filter(AuditLog.action.ilike(f'%{search_action}%'))
    if search_date_start:
        try:
            start_date = datetime.strptime(search_date_start, '%Y-%m-%d')
            query = query.filter(AuditLog.created_at >= start_date)
        except ValueError:
            pass
    if search_date_end:
        try:
            end_date = datetime.strptime(search_date_end, '%Y-%m-%d')
            query = query.filter(AuditLog.created_at <= end_date)
        except ValueError:
            pass

    # Order by created_at descending (most recent first)
    query = query.order_by(AuditLog.created_at.desc())

    # Paginate results
    pagination = query.paginate(page=page, per_page=per_page, error_out=False)

    # Get distinct actions for filter dropdown
    distinct_actions = db.session.query(AuditLog.action).distinct().all()
    actions = [action[0] for action in distinct_actions]

    return render_template(
        'admin_public/audit/index.html',
        logs=pagination.items,
        pagination=pagination,
        actions=actions,
        search_email=search_email,
        search_action=search_action,
        search_date_start=search_date_start,
        search_date_end=search_date_end
    )
        
@admin_public_bp.route('/audit/export', methods=['POST'])
@login_required
def audit_export():
    """Export audit log as CSV"""
    if current_user.role not in ['admin', 'manager']:
        flash('Acesso negado.', 'error')
        return redirect(url_for('dashboard.index'))

    try:
        # Query all audit logs ordered by timestamp
        logs = AuditLog.query.order_by(AuditLog.timestamp.desc()).all()
        
        # Create CSV in memory
        output = io.StringIO()
        writer = csv.writer(output)
        
        # Write headers
        writer.writerow(['Data/Hora', 'Usuário', 'Ação', 'Detalhes'])
        
        # Write data
        for log in logs:
            writer.writerow([
                log.timestamp.strftime('%Y-%m-%d %H:%M:%S'),
                log.user_email,
                log.action,
                log.details
            ])
            
        # Prepare response
        output.seek(0)
        return Response(
            output.getvalue(),
            mimetype='text/csv',
            headers={'Content-Disposition': 'attachment; filename=audit_log.csv'}
        )
        
    except Exception as e:
        current_app.logger.error(f'Error exporting audit log: {str(e)}')
        flash('Erro ao exportar log de auditoria.', 'error')
        return redirect(url_for('admin_public.audit_log'))

    page = int(request.args.get('page', 1))
    per_page = 50
    entity = request.args.get('entity', '')
    action = request.args.get('action', '')

    query = AuditLog.query
    if entity:
        query = query.filter_by(entity=entity)
    if action:
        query = query.filter_by(action=action)

    audit_logs = query.order_by(AuditLog.created_at.desc()).paginate(
        page=page, per_page=per_page, error_out=False
    )

    return render_template('admin_public/audit/index.html',
                         audit_logs=audit_logs, entity=entity, action=action)

# ==========================================
# ADMIN DASHBOARD
# ==========================================

@admin_public_bp.route('/dashboard')
@login_required
def admin_dashboard():
    """Admin dashboard for content overview"""
    current_app.logger.info(f"User {current_user.id} ({current_user.email}) accessing admin dashboard")
    current_app.logger.info(f"User role: {current_user.role}")

    if current_user.role not in ['admin', 'manager']:
        current_app.logger.warning(f"Access denied for user {current_user.id} with role {current_user.role}")
        flash('Acesso negado. Apenas administradores e gerentes podem acessar as configurações.', 'error')
        return redirect(url_for('dashboard.index'))

    current_app.logger.info("User authorized, proceeding to render dashboard")

    # Get statistics
    stats = {
        'company_settings': CompanySettings.query.filter_by(active=True).count(),
        'public_content': PublicContent.query.filter_by(active=True).count(),
        'media_files': MediaFile.query.count(),
        'content_versions': ContentVersion.query.count(),
        'recent_audit': AuditLog.query.order_by(AuditLog.created_at.desc()).limit(5).all()
    }

    current_app.logger.info(f"Stats: {stats}")

    # Get content by section
    sections = ['hero', 'features', 'about', 'contact', 'footer']
    content_stats = {}
    for section in sections:
        content_stats[section] = PublicContent.query.filter_by(
            section=section, active=True
        ).count()

    current_app.logger.info(f"Content stats: {content_stats}")

    current_app.logger.info("Rendering admin_public/dashboard/index.html")
    return render_template('admin_public/dashboard/index.html',
                          stats=stats, content_stats=content_stats)

# ==========================================
# API ENDPOINTS
# ==========================================

@admin_public_bp.route('/api/content/<section>')
@login_required
def api_content_section(section):
    """API to get content for a section"""
    if current_user.role not in ['admin', 'manager']:
        return jsonify({'error': 'Acesso negado'}), 403

    content_items = PublicContent.query.filter_by(
        section=section, active=True
    ).order_by(PublicContent.order).all()

    return jsonify([{
        'id': item.id,
        'title': item.title,
        'content': item.content,
        'image_url': item.image_url,
        'order': item.order,
        'created_at': item.created_at.isoformat()
    } for item in content_items])

@admin_public_bp.route('/api/company-settings')
@login_required
def api_company_settings():
    """API to get company settings"""
    if current_user.role not in ['admin', 'manager']:
        return jsonify({'error': 'Acesso negado'}), 403

    settings = CompanySettings.query.filter_by(active=True).first()
    if not settings:
        return jsonify({'error': 'Configurações não encontradas'}), 404

    return jsonify({
        'id': settings.id,
        'company_name': settings.company_name,
        'tagline': settings.tagline,
        'description': settings.description,
        'phone': settings.phone,
        'whatsapp': settings.whatsapp,
        'email': settings.email,
        'website': settings.website,
        'address': settings.address,
        'city': settings.city,
        'state': settings.state,
        'zip_code': settings.zip_code,
        'social_media': json.loads(settings.social_media or '{}'),
        'business_hours': json.loads(settings.business_hours or '{}'),
        'logo_url': settings.logo_url,
        'favicon_url': settings.favicon_url,
        'primary_color': settings.primary_color,
        'secondary_color': settings.secondary_color,
        'maintenance_mode': settings.maintenance_mode,
        'allow_public_orders': settings.allow_public_orders,
        'timezone': settings.timezone
    })