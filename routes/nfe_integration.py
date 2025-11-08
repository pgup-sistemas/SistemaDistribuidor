from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from services.nfe_integration_service import get_nfe_service
from models import Supplier
import os

nfe_bp = Blueprint('nfe_integration', __name__)

@nfe_bp.route('/')
@login_required
def index():
    """Página principal de integração NF-e"""
    if current_user.role not in ['admin', 'manager']:
        flash('Acesso negado.', 'error')
        return redirect(url_for('dashboard.index'))

    nfe_service = get_nfe_service()
    config = nfe_service.get_configuracao()
    suppliers = Supplier.query.filter_by(active=True).all()

    return render_template('nfe_integration/index.html',
                         config=config,
                         suppliers=suppliers)

@nfe_bp.route('/consultar', methods=['POST'])
@login_required
def consultar_nfe():
    """API para consultar NF-e por chave de acesso"""
    if current_user.role not in ['admin', 'manager']:
        return jsonify({'success': False, 'message': 'Acesso negado'}), 403

    data = request.get_json()
    chave_acesso = data.get('chave_acesso', '').strip()

    if not chave_acesso:
        return jsonify({'success': False, 'message': 'Chave de acesso é obrigatória'}), 400

    nfe_service = get_nfe_service()

    # Validar formato da chave
    if not nfe_service.validar_chave_acesso(chave_acesso):
        return jsonify({'success': False, 'message': 'Formato de chave de acesso inválido'}), 400

    try:
        # Consultar NF-e
        nfe_data = nfe_service.consultar_nfe_api(chave_acesso)

        return jsonify({
            'success': True,
            'nfe_data': nfe_data
        })

    except Exception as e:
        return jsonify({'success': False, 'message': f'Erro ao consultar NF-e: {str(e)}'}), 500

@nfe_bp.route('/importar', methods=['POST'])
@login_required
def importar_nfe():
    """API para importar produtos de uma NF-e"""
    if current_user.role not in ['admin', 'manager']:
        return jsonify({'success': False, 'message': 'Acesso negado'}), 403

    data = request.get_json()
    chave_acesso = data.get('chave_acesso', '').strip()
    supplier_id = data.get('supplier_id')

    if not chave_acesso or not supplier_id:
        return jsonify({'success': False, 'message': 'Chave de acesso e fornecedor são obrigatórios'}), 400

    nfe_service = get_nfe_service()

    try:
        # Importar NF-e completa
        resultado = nfe_service.importar_nfe_completa(chave_acesso, int(supplier_id))

        if resultado['success']:
            # Mensagem de sucesso detalhada
            msg = f"NF-e importada com sucesso! {resultado['resultados']['processados']} itens processados"
            if resultado['resultados']['criados'] > 0:
                msg += f", {resultado['resultados']['criados']} produtos criados"
            if resultado['resultados']['atualizados'] > 0:
                msg += f", {resultado['resultados']['atualizados']} produtos atualizados"

            flash(msg, 'success')

            return jsonify({
                'success': True,
                'resultado': resultado
            })
        else:
            return jsonify({'success': False, 'message': resultado.get('error', 'Erro desconhecido')}), 500

    except Exception as e:
        return jsonify({'success': False, 'message': f'Erro na importação: {str(e)}'}), 500

@nfe_bp.route('/upload-xml', methods=['POST'])
@login_required
def upload_xml():
    """Upload de arquivo XML NF-e para processamento"""
    if current_user.role not in ['admin', 'manager']:
        flash('Acesso negado.', 'error')
        return redirect(url_for('nfe_integration.index'))

    if 'xml_file' not in request.files:
        flash('Nenhum arquivo selecionado.', 'error')
        return redirect(request.url)

    file = request.files['xml_file']
    supplier_id = request.form.get('supplier_id')

    if not supplier_id:
        flash('Fornecedor é obrigatório.', 'error')
        return redirect(request.url)

    if file.filename == '':
        flash('Nenhum arquivo selecionado.', 'error')
        return redirect(request.url)

    if file and file.filename.lower().endswith('.xml'):
        try:
            # Ler conteúdo do XML
            xml_content = file.read().decode('utf-8')

            nfe_service = get_nfe_service()

            # Parse do XML
            nfe_data = nfe_service.parse_xml_nfe(xml_content)

            # Importar dados
            resultado = nfe_service.importar_nfe_completa(
                nfe_data['chave_acesso'],
                int(supplier_id),
                fonte='xml'
            )

            if resultado['success']:
                msg = f"XML NF-e processado com sucesso! {resultado['resultados']['processados']} itens processados"
                if resultado['resultados']['criados'] > 0:
                    msg += f", {resultado['resultados']['criados']} produtos criados"
                if resultado['resultados']['atualizados'] > 0:
                    msg += f", {resultado['resultados']['atualizados']} produtos atualizados"
                flash(msg, 'success')
            else:
                flash(f'Erro no processamento: {resultado.get("error", "Erro desconhecido")}', 'error')

        except Exception as e:
            flash(f'Erro ao processar XML: {str(e)}', 'error')

    else:
        flash('Tipo de arquivo não permitido. Use apenas arquivos .xml', 'error')

    return redirect(url_for('nfe_integration.index'))

@nfe_bp.route('/config')
@login_required
def config():
    """Página de configuração da integração NF-e"""
    if current_user.role != 'admin':
        flash('Acesso negado.', 'error')
        return redirect(url_for('dashboard.index'))

    nfe_service = get_nfe_service()
    config = nfe_service.get_configuracao()

    return render_template('nfe_integration/config.html', config=config)

@nfe_bp.route('/test-connection', methods=['POST'])
@login_required
def test_connection():
    """Testar conexão com API NF-e"""
    if current_user.role != 'admin':
        return jsonify({'success': False, 'message': 'Acesso negado'}), 403

    nfe_service = get_nfe_service()

    try:
        # Testar com chave de exemplo
        test_chave = "35150812345678000127550010000000011000000000"  # Chave de exemplo
        resultado = nfe_service.consultar_nfe_api(test_chave)

        return jsonify({
            'success': True,
            'message': 'Conexão testada com sucesso',
            'provider': nfe_service.api_provider,
            'environment': nfe_service.environment
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Erro na conexão: {str(e)}',
            'provider': nfe_service.api_provider,
            'environment': nfe_service.environment
        }), 500