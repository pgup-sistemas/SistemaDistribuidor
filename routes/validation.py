from flask import Blueprint, jsonify, request
from services.validation_service import ValidationService

validation_bp = Blueprint('validation', __name__)

@validation_bp.route('/cpf', methods=['POST'])
def validate_cpf():
    """Endpoint para validar CPF"""
    data = request.get_json()
    cpf = data.get('cpf', '')
    
    is_valid = ValidationService.validate_cpf(cpf)
    formatted = ValidationService.format_cpf(cpf) if is_valid else cpf
    
    return jsonify({
        'valid': is_valid,
        'formatted': formatted,
        'message': 'CPF válido' if is_valid else 'CPF inválido'
    })

@validation_bp.route('/cnpj', methods=['POST'])
def validate_cnpj():
    """Endpoint para validar CNPJ"""
    data = request.get_json()
    cnpj = data.get('cnpj', '')
    
    is_valid = ValidationService.validate_cnpj(cnpj)
    formatted = ValidationService.format_cnpj(cnpj) if is_valid else cnpj
    
    return jsonify({
        'valid': is_valid,
        'formatted': formatted,
        'message': 'CNPJ válido' if is_valid else 'CNPJ inválido'
    })

@validation_bp.route('/cep', methods=['POST'])
def get_address_by_cep():
    """Endpoint para consultar endereço por CEP"""
    data = request.get_json()
    cep = data.get('cep', '')
    
    if not ValidationService.validate_cep(cep):
        return jsonify({
            'success': False,
            'message': 'CEP inválido',
            'data': None
        }), 400
    
    address_data = ValidationService.get_address_by_cep(cep)
    
    if address_data:
        return jsonify({
            'success': True,
            'message': 'CEP encontrado',
            'data': address_data
        })
    else:
        return jsonify({
            'success': False,
            'message': 'CEP não encontrado',
            'data': None
        }), 404

@validation_bp.route('/document', methods=['POST'])
def validate_document():
    """Endpoint para validar documento (CPF ou CNPJ automaticamente)"""
    data = request.get_json()
    document = data.get('document', '')
    
    doc_type = ValidationService.identify_document_type(document)
    
    if doc_type == 'cpf':
        is_valid = ValidationService.validate_cpf(document)
        formatted = ValidationService.format_cpf(document) if is_valid else document
        message = 'CPF válido' if is_valid else 'CPF inválido'
    elif doc_type == 'cnpj':
        is_valid = ValidationService.validate_cnpj(document)
        formatted = ValidationService.format_cnpj(document) if is_valid else document
        message = 'CNPJ válido' if is_valid else 'CNPJ inválido'
    else:
        is_valid = False
        formatted = document
        message = 'Documento deve ter 11 dígitos (CPF) ou 14 dígitos (CNPJ)'
    
    return jsonify({
        'valid': is_valid,
        'formatted': formatted,
        'type': doc_type,
        'message': message
    })

@validation_bp.route('/format/phone', methods=['POST'])
def format_phone():
    """Endpoint para formatar telefone"""
    data = request.get_json()
    phone = data.get('phone', '')
    
    formatted = ValidationService.format_phone(phone)
    
    return jsonify({
        'formatted': formatted
    })

@validation_bp.route('/email', methods=['POST'])
def validate_email():
    """Endpoint para validar email"""
    data = request.get_json()
    email = data.get('email', '')
    
    is_valid = ValidationService.validate_email(email)
    
    return jsonify({
        'valid': is_valid,
        'message': 'Email válido' if is_valid else 'Email inválido'
    })