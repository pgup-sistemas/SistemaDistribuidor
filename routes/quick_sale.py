import io
from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, session
from flask_login import login_required, current_user
from models import QuickSale, QuickSaleItem, Product, Company, db
from services.print_service import PrintService
try:
    from weasyprint import HTML, CSS
    WEASYPRINT_AVAILABLE = True
except (ImportError, OSError):
    WEASYPRINT_AVAILABLE = False
from datetime import datetime
from decimal import Decimal

quick_sale_bp = Blueprint('quick_sale', __name__)

# Helper function for CSRF validation
def validate_csrf_token():
    """Validate CSRF token for API requests"""
    from flask_wtf.csrf import validate_csrf
    try:
        csrf_token = request.headers.get('X-CSRFToken') or request.form.get('csrf_token') or request.args.get('csrf_token')
        if not csrf_token:
            return jsonify({'success': False, 'message': 'Token CSRF não encontrado'}), 403
        validate_csrf(csrf_token)
    except:
        return jsonify({'success': False, 'message': 'Token de segurança inválido'}), 403
    return None

@quick_sale_bp.route('/')
@login_required
def index():
    """Página principal do PDV (Ponto de Venda)"""
    return render_template('quick_sale/index.html')

@quick_sale_bp.route('/api/scan', methods=['POST'])
@login_required
def scan_product():
    """API para escanear produto por código/SKU"""
    # Validate CSRF token
    csrf_result = validate_csrf_token()
    if csrf_result:
        return csrf_result
        
    data = request.get_json()
    code = data.get('code', '').strip()

    if not code:
        return jsonify({'success': False, 'message': 'Código não informado'}), 400

    # Buscar produto por SKU
    product = Product.query.filter_by(sku=code, active=True).first()

    if not product:
        return jsonify({'success': False, 'message': 'Produto não encontrado'}), 404

    if product.current_stock <= 0:
        return jsonify({'success': False, 'message': 'Produto sem estoque'}), 400

    return jsonify({
        'success': True,
        'product': {
            'id': product.id,
            'sku': product.sku,
            'name': product.name,
            'price': float(product.sale_price),
            'stock': product.current_stock,
            'unit': product.unit
        }
    })

@quick_sale_bp.route('/api/add-item', methods=['POST'])
@login_required
def add_item():
    """API para adicionar item à venda atual (armazenado em sessão)"""
    # Validate CSRF token
    csrf_result = validate_csrf_token()
    if csrf_result:
        return csrf_result
        
    data = request.get_json()
    product_id = data.get('product_id')
    quantity = data.get('quantity', 1)

    if not product_id:
        return jsonify({'success': False, 'message': 'ID do produto obrigatório'}), 400

    product = Product.query.get_or_404(product_id)

    if product.current_stock < quantity:
        return jsonify({'success': False, 'message': 'Estoque insuficiente'}), 400

    # Usar sessão para armazenar itens temporariamente
    if 'quick_sale_items' not in session:
        session['quick_sale_items'] = []

    items = session['quick_sale_items']

    # Verificar se produto já existe na venda
    existing_item = None
    for item in items:
        if item['product_id'] == product_id:
            existing_item = item
            break

    if existing_item:
        # Atualizar quantidade
        new_quantity = existing_item['quantity'] + quantity
        if product.current_stock < new_quantity:
            return jsonify({'success': False, 'message': 'Estoque insuficiente para quantidade total'}), 400
        existing_item['quantity'] = new_quantity
        existing_item['total'] = float(Decimal(str(new_quantity)) * product.sale_price)
    else:
        # Adicionar novo item
        item = {
            'product_id': product.id,
            'product_name': product.name,
            'product_sku': product.sku,
            'quantity': quantity,
            'unit_price': float(product.sale_price),
            'discount': 0.0,
            'total': float(Decimal(str(quantity)) * product.sale_price)
        }
        items.append(item)

    # IMPORTANT: Mark session as modified to ensure changes are saved
    session.modified = True

    # Calcular total
    total = sum(item['total'] for item in items)

    return jsonify({
        'success': True,
        'items': items,
        'total': total,
        'item_count': len(items)
    })

@quick_sale_bp.route('/api/remove-item', methods=['POST'])
@login_required
def remove_item():
    """API para remover item da venda atual"""
    # Validate CSRF token
    csrf_result = validate_csrf_token()
    if csrf_result:
        return csrf_result
        
    data = request.get_json()
    product_id = data.get('product_id')

    if 'quick_sale_items' not in session:
        return jsonify({'success': False, 'message': 'Nenhuma venda em andamento'}), 400

    items = session['quick_sale_items']

    # Remover item
    items[:] = [item for item in items if item['product_id'] != product_id]

    # Mark session as modified
    session.modified = True

    total = sum(item['total'] for item in items)

    return jsonify({
        'success': True,
        'items': items,
        'total': total,
        'item_count': len(items)
    })

@quick_sale_bp.route('/api/clear-sale', methods=['POST'])
@login_required
def clear_sale():
    """API para limpar venda atual"""
    # Validate CSRF token
    csrf_result = validate_csrf_token()
    if csrf_result:
        return csrf_result
        
    if 'quick_sale_items' in session:
        del session['quick_sale_items']

    return jsonify({'success': True})
@quick_sale_bp.route('/api/current-state', methods=['GET'])
@login_required
def get_current_state():
    """API para obter o estado atual da venda em andamento"""
    items = session.get('quick_sale_items', [])
    total = sum(item['total'] for item in items)
    
    return jsonify({
        'success': True,
        'items': items,
        'total': total,
        'item_count': len(items)
    })

@quick_sale_bp.route('/api/finalize', methods=['POST'])
@login_required
def finalize_sale():
    """API para finalizar venda"""
    # Validate CSRF token
    csrf_result = validate_csrf_token()
    if csrf_result:
        return csrf_result
        
    data = request.get_json()
    payment_method = data.get('payment_method')

    if not payment_method:
        return jsonify({'success': False, 'message': 'Método de pagamento obrigatório'}), 400

    if payment_method not in ['cash', 'card', 'pix', 'bank_slip']:
        return jsonify({'success': False, 'message': 'Método de pagamento inválido'}), 400

    if 'quick_sale_items' not in session:
        return jsonify({'success': False, 'message': 'Nenhum item na venda'}), 400

    items = session['quick_sale_items']

    if not items:
        return jsonify({'success': False, 'message': 'Nenhum item na venda'}), 400

    try:
        # Calcular total
        total = sum(item['total'] for item in items)

        # Criar venda
        sale = QuickSale(
            total=Decimal(str(total)),
            payment_method=payment_method,
            user_id=current_user.id,
            status='completed'
        )

        db.session.add(sale)
        db.session.flush()  # Para obter o ID

        # Gerar número da venda
        sale.sale_number = sale.generate_sale_number()
        db.session.commit()

        # Adicionar itens e atualizar estoque
        for item_data in items:
            product = Product.query.get(item_data['product_id'])

            # Verificar estoque novamente
            if product.current_stock < item_data['quantity']:
                db.session.rollback()
                return jsonify({'success': False, 'message': f'Estoque insuficiente para {product.name}'}), 400

            # Criar item da venda
            sale_item = QuickSaleItem(
                quick_sale_id=sale.id,
                product_id=product.id,
                product_name=product.name,
                product_sku=product.sku,
                quantity=item_data['quantity'],
                unit_price=Decimal(str(item_data['unit_price'])),
                discount=Decimal(str(item_data['discount'])),
                total=Decimal(str(item_data['total']))
            )

            db.session.add(sale_item)

            # Atualizar estoque
            product.current_stock -= item_data['quantity']

        db.session.commit()

        # Limpar sessão
        if 'quick_sale_items' in session:
            del session['quick_sale_items']

        return jsonify({
            'success': True,
            'sale_id': sale.id,
            'sale_number': sale.sale_number,
            'total': float(total),
            'receipt_url': url_for('quick_sale.receipt', sale_id=sale.id)
        })

    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': 'Erro ao finalizar venda'}), 500

@quick_sale_bp.route('/receipt/<int:sale_id>')
@login_required
def receipt(sale_id):
    """Página do recibo da venda rápida"""
    sale = QuickSale.query.get_or_404(sale_id)
    company = Company.query.first()

    # Verificar se usuário tem permissão para ver esta venda
    if sale.user_id != current_user.id and current_user.role != 'admin':
        flash('Acesso negado.', 'error')
        return redirect(url_for('dashboard.index'))

    return render_template('quick_sale/receipt.html', sale=sale, company=company)

@quick_sale_bp.route('/print-receipt/<int:sale_id>')
@login_required
def print_receipt(sale_id):
    """Imprimir recibo da venda rápida"""
    sale = QuickSale.query.get_or_404(sale_id)

    # Verificar permissões
    if sale.user_id != current_user.id and current_user.role != 'admin':
        flash('Acesso negado.', 'error')
        return redirect(url_for('dashboard.index'))

    # Usar o PrintService existente, adaptado para QuickSale
    print_service = QuickSalePrintService()
    pdf_content = print_service.generate_receipt(sale)

    # Check if PDF generation was successful (bytes) or fallback (str)
    if isinstance(pdf_content, bytes):
        mimetype = 'application/pdf'
        filename = f'recibo_venda_{sale.sale_number}.pdf'
    else:
        mimetype = 'text/html'
        filename = f'recibo_venda_{sale.sale_number}.html'

    from flask import Response
    return Response(
        pdf_content,
        mimetype=mimetype,
        headers={'Content-Disposition': f'inline; filename={filename}'}
    )

class QuickSalePrintService(PrintService):
    """Serviço de impressão adaptado para vendas rápidas"""

    def generate_receipt(self, sale):
        """Generate thermal receipt PDF for quick sale"""
        company = Company.query.first()

        receipt_html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <title>Venda {sale.sale_number}</title>
        </head>
        <body>
            <div class="receipt-header">
                <div class="company-name">{company.trade_name or company.company_name if company else 'Sistema Distribuidor'}</div>
                <div>CNPJ: {company.cnpj if company else 'Não configurado'}</div>
                <div style="font-size: 10px;">{company.address if company else 'Configure os dados da empresa'}</div>
            </div>

            <div class="order-info">
                <strong>CUPOM FISCAL</strong><br>
                <strong>Venda: {sale.sale_number}</strong><br>
                Data: {sale.created_at.strftime('%d/%m/%Y %H:%M')}<br>
                Atendente: {sale.user.name}
            </div>

            <table class="items-table">
        """

        # Add items
        for item in sale.items:
            receipt_html += f"""
                <tr>
                    <td class="item-name" colspan="2">{item.product_name}</td>
                </tr>
                <tr>
                    <td>{item.quantity} x R$ {item.unit_price:.2f}</td>
                    <td class="item-details">R$ {item.total:.2f}</td>
                </tr>
            """

        payment_method_name = {
            'cash': 'Dinheiro',
            'card': 'Cartão',
            'pix': 'PIX',
            'bank_slip': 'Boleto'
        }.get(sale.payment_method, sale.payment_method)

        receipt_html += f"""
            </table>

            <div class="total-section">
                <div>TOTAL: R$ {sale.total:.2f}</div>
                <div style="font-size: 12px; font-weight: normal;">
                    Pagamento: {payment_method_name}
                </div>
            </div>

            <div class="receipt-footer">
                Obrigado pela preferência!<br>
                Sistema PDV v1.0<br>
                Venda: {sale.sale_number}
            </div>
        </body>
        </html>
        """

        # Generate PDF if WeasyPrint is available
        if not WEASYPRINT_AVAILABLE:
            return receipt_html

        from weasyprint import HTML, CSS
        html_doc = HTML(string=receipt_html)
        css_doc = CSS(string=self.thermal_css)

        pdf_buffer = io.BytesIO()
        html_doc.write_pdf(pdf_buffer, stylesheets=[css_doc])
        pdf_buffer.seek(0)

        return pdf_buffer.getvalue()