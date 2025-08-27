from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from models import Company, AuditLog
from app import db
import json
import re

company_bp = Blueprint('company', __name__)

def format_cnpj(cnpj):
    """Formatar CNPJ para exibição"""
    if not cnpj:
        return ''
    # Remove caracteres não numéricos
    cnpj = re.sub(r'\D', '', cnpj)
    if len(cnpj) == 14:
        return f"{cnpj[:2]}.{cnpj[2:5]}.{cnpj[5:8]}/{cnpj[8:12]}-{cnpj[12:]}"
    return cnpj

def format_phone(phone):
    """Formatar telefone para exibição"""
    if not phone:
        return ''
    # Remove caracteres não numéricos
    phone = re.sub(r'\D', '', phone)
    if len(phone) == 11:  # Celular
        return f"({phone[:2]}) {phone[2:7]}-{phone[7:]}"
    elif len(phone) == 10:  # Fixo
        return f"({phone[:2]}) {phone[2:6]}-{phone[6:]}"
    return phone

def format_zip_code(zip_code):
    """Formatar CEP para exibição"""
    if not zip_code:
        return ''
    # Remove caracteres não numéricos
    zip_code = re.sub(r'\D', '', zip_code)
    if len(zip_code) == 8:
        return f"{zip_code[:5]}-{zip_code[5:]}"
    return zip_code

@company_bp.route('/')
@login_required
def index():
    """Exibir configurações da empresa"""
    if current_user.role not in ['admin', 'manager']:
        flash('Acesso negado. Apenas administradores e gerentes podem acessar as configurações da empresa.', 'error')
        return redirect(url_for('dashboard.index'))
    
    company = Company.query.first()
    return render_template('company/index.html', company=company)

@company_bp.route('/edit')
@login_required
def edit():
    """Formulário para editar configurações da empresa"""
    if current_user.role not in ['admin', 'manager']:
        flash('Acesso negado. Apenas administradores e gerentes podem editar as configurações da empresa.', 'error')
        return redirect(url_for('dashboard.index'))
    
    company = Company.query.first()
    return render_template('company/form.html', company=company, action='edit')

@company_bp.route('/save', methods=['POST'])
@login_required
def save():
    """Salvar configurações da empresa"""
    if current_user.role not in ['admin', 'manager']:
        flash('Acesso negado. Apenas administradores e gerentes podem salvar as configurações da empresa.', 'error')
        return redirect(url_for('dashboard.index'))
    
    try:
        # Validar CNPJ
        cnpj = re.sub(r'\D', '', request.form.get('cnpj', ''))
        if not cnpj or len(cnpj) != 14:
            flash('CNPJ deve ter 14 dígitos.', 'error')
            return redirect(url_for('company.edit'))
        
        company = Company.query.first()
        old_data = None
        
        if company:
            # Atualizar empresa existente
            old_data = {
                'company_name': company.company_name,
                'trade_name': company.trade_name,
                'cnpj': company.cnpj,
                'phone': company.phone,
                'email': company.email
            }
            
            company.company_name = request.form.get('company_name')
            company.trade_name = request.form.get('trade_name')
            company.cnpj = cnpj
            company.ie = request.form.get('ie')
            company.im = request.form.get('im')
            
            # Endereço
            company.address = request.form.get('address')
            company.address_number = request.form.get('address_number')
            company.complement = request.form.get('complement')
            company.neighborhood = request.form.get('neighborhood')
            company.city = request.form.get('city')
            company.state = request.form.get('state')
            company.zip_code = re.sub(r'\D', '', request.form.get('zip_code', ''))
            
            # Contatos
            company.phone = re.sub(r'\D', '', request.form.get('phone', ''))
            company.mobile = re.sub(r'\D', '', request.form.get('mobile', ''))
            company.whatsapp = re.sub(r'\D', '', request.form.get('whatsapp', ''))
            company.email = request.form.get('email')
            company.website = request.form.get('website')
            
            # Configurações de documentos
            company.receipt_header = request.form.get('receipt_header')
            company.receipt_footer = request.form.get('receipt_footer')
            company.order_notes = request.form.get('order_notes')
            
            # Dados bancários
            company.bank_name = request.form.get('bank_name')
            company.bank_agency = request.form.get('bank_agency')
            company.bank_account = request.form.get('bank_account')
            company.pix_key = request.form.get('pix_key')
            
            action = 'UPDATE'
            
        else:
            # Criar nova empresa
            company = Company(
                company_name=request.form.get('company_name'),
                trade_name=request.form.get('trade_name'),
                cnpj=cnpj,
                ie=request.form.get('ie'),
                im=request.form.get('im'),
                address=request.form.get('address'),
                address_number=request.form.get('address_number'),
                complement=request.form.get('complement'),
                neighborhood=request.form.get('neighborhood'),
                city=request.form.get('city'),
                state=request.form.get('state'),
                zip_code=re.sub(r'\D', '', request.form.get('zip_code', '')),
                phone=re.sub(r'\D', '', request.form.get('phone', '')),
                mobile=re.sub(r'\D', '', request.form.get('mobile', '')),
                whatsapp=re.sub(r'\D', '', request.form.get('whatsapp', '')),
                email=request.form.get('email'),
                website=request.form.get('website'),
                receipt_header=request.form.get('receipt_header'),
                receipt_footer=request.form.get('receipt_footer'),
                order_notes=request.form.get('order_notes'),
                bank_name=request.form.get('bank_name'),
                bank_agency=request.form.get('bank_agency'),
                bank_account=request.form.get('bank_account'),
                pix_key=request.form.get('pix_key')
            )
            db.session.add(company)
            action = 'CREATE'
        
        db.session.commit()
        
        # Log da auditoria
        new_data = {
            'company_name': company.company_name,
            'trade_name': company.trade_name,
            'cnpj': company.cnpj,
            'phone': company.phone,
            'email': company.email
        }
        
        audit_log = AuditLog(
            user_id=current_user.id,
            action=action,
            entity='Company',
            entity_id=company.id,
            old_data=json.dumps(old_data) if old_data else None,
            new_data=json.dumps(new_data)
        )
        db.session.add(audit_log)
        db.session.commit()
        
        flash(f'Configurações da empresa {"atualizadas" if action == "UPDATE" else "criadas"} com sucesso!', 'success')
        return redirect(url_for('company.index'))
        
    except Exception as e:
        db.session.rollback()
        flash(f'Erro ao salvar configurações: {str(e)}', 'error')
        return redirect(url_for('company.edit'))

@company_bp.route('/api/data')
@login_required
def api_data():
    """API para obter dados da empresa (para usar em recibos e documentos)"""
    company = Company.query.first()
    if not company:
        return jsonify({'error': 'Nenhuma empresa configurada'}), 404
    
    return jsonify({
        'id': company.id,
        'company_name': company.company_name,
        'trade_name': company.trade_name,
        'cnpj': format_cnpj(company.cnpj),
        'cnpj_raw': company.cnpj,
        'ie': company.ie,
        'im': company.im,
        'address': {
            'street': company.address,
            'number': company.address_number,
            'complement': company.complement,
            'neighborhood': company.neighborhood,
            'city': company.city,
            'state': company.state,
            'zip_code': format_zip_code(company.zip_code),
            'zip_code_raw': company.zip_code,
            'full': f"{company.address}, {company.address_number}" + 
                   (f", {company.complement}" if company.complement else "") +
                   f" - {company.neighborhood} - {company.city}/{company.state} - CEP: {format_zip_code(company.zip_code)}"
        },
        'contacts': {
            'phone': format_phone(company.phone),
            'phone_raw': company.phone,
            'mobile': format_phone(company.mobile),
            'mobile_raw': company.mobile,
            'whatsapp': format_phone(company.whatsapp),
            'whatsapp_raw': company.whatsapp,
            'email': company.email,
            'website': company.website
        },
        'documents': {
            'receipt_header': company.receipt_header,
            'receipt_footer': company.receipt_footer,
            'order_notes': company.order_notes
        },
        'banking': {
            'bank_name': company.bank_name,
            'bank_agency': company.bank_agency,
            'bank_account': company.bank_account,
            'pix_key': company.pix_key
        }
    })