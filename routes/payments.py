from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, session
from flask_login import login_required, current_user
from flask_wtf.csrf import CSRFProtect
from models import Order, db
from services.mercadopago_service import MercadoPagoService
import logging

# Get CSRF instance to allow exemptions
csrf = CSRFProtect()

payments_bp = Blueprint('payments', __name__)

@payments_bp.route('/create/<int:order_id>')
@login_required
def create_payment(order_id):
    """Cria um pagamento MercadoPago para um pedido"""
    try:
        order = Order.query.get_or_404(order_id)
        
        # Verificar se o pedido pertence ao usuário ou se é admin
        if order.user_id != current_user.id and current_user.role != 'admin':
            flash('Acesso negado.', 'error')
            return redirect(url_for('orders.index'))
        
        # Verificar se o pedido já tem um pagamento
        if order.payment_id:
            flash('Este pedido já possui um pagamento processado.', 'warning')
            return redirect(url_for('orders.view', id=order_id))
        
        # Criar serviço MercadoPago
        mp_service = MercadoPagoService()
        
        # Criar preferência de pagamento
        result = mp_service.create_preference(order)
        
        if result['success']:
            # Salvar preference_id no pedido
            order.preference_id = result['preference_id']
            order.payment_method = 'mercadopago'
            order.payment_status = 'pending'
            db.session.commit()
            
            # Redirecionar para o MercadoPago
            payment_url = result.get('sandbox_init_point') or result['init_point']
            flash('Redirecionando para o MercadoPago...', 'info')
            return redirect(payment_url)
        else:
            flash(f'Erro ao criar pagamento: {result["error"]}', 'error')
            return redirect(url_for('orders.view', id=order_id))
            
    except Exception as e:
        logging.error(f"Error creating payment for order {order_id}: {str(e)}")
        flash('Erro interno ao criar pagamento.', 'error')
        return redirect(url_for('orders.view', id=order_id))

@payments_bp.route('/success')
@login_required
def payment_success():
    """Página de sucesso do pagamento"""
    payment_id = request.args.get('payment_id')
    external_reference = request.args.get('external_reference')
    
    if external_reference:
        order = Order.query.get(int(external_reference))
        if order:
            flash('Pagamento aprovado com sucesso!', 'success')
            return redirect(url_for('orders.view', id=order.id))
    
    flash('Pagamento processado com sucesso!', 'success')
    return redirect(url_for('orders.index'))

@payments_bp.route('/failure')
@login_required
def payment_failure():
    """Página de falha do pagamento"""
    external_reference = request.args.get('external_reference')
    
    if external_reference:
        order = Order.query.get(int(external_reference))
        if order:
            flash('Pagamento não foi aprovado. Tente novamente.', 'error')
            return redirect(url_for('orders.view', id=order.id))
    
    flash('Pagamento não foi aprovado. Tente novamente.', 'error')
    return redirect(url_for('orders.index'))

@payments_bp.route('/pending')
@login_required
def payment_pending():
    """Página de pagamento pendente"""
    external_reference = request.args.get('external_reference')
    
    if external_reference:
        order = Order.query.get(int(external_reference))
        if order:
            flash('Pagamento está sendo processado. Você será notificado quando for aprovado.', 'info')
            return redirect(url_for('orders.view', id=order.id))
    
    flash('Pagamento está sendo processado.', 'info')
    return redirect(url_for('orders.index'))

@payments_bp.route('/webhook', methods=['POST'])
@csrf.exempt
def webhook():
    """Webhook para receber notificações do MercadoPago"""
    try:
        # Obter dados da notificação
        notification_data = request.get_json()
        
        if not notification_data:
            return jsonify({'error': 'No data received'}), 400
        
        # Processar notificação
        mp_service = MercadoPagoService()
        result = mp_service.process_webhook(notification_data)
        
        if result['success']:
            return jsonify({'status': 'ok'}), 200
        else:
            logging.error(f"Webhook processing failed: {result['error']}")
            return jsonify({'error': result['error']}), 400
            
    except Exception as e:
        logging.error(f"Webhook error: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

@payments_bp.route('/status/<int:order_id>')
@login_required
def payment_status(order_id):
    """Verifica o status de um pagamento"""
    try:
        order = Order.query.get_or_404(order_id)
        
        # Verificar se o pedido pertence ao usuário ou se é admin
        if order.user_id != current_user.id and current_user.role != 'admin':
            return jsonify({'error': 'Access denied'}), 403
        
        if not order.payment_id:
            return jsonify({'error': 'No payment found'}), 404
        
        # Buscar informações do pagamento no MercadoPago
        mp_service = MercadoPagoService()
        result = mp_service.get_payment_info(order.payment_id)
        
        if result['success']:
            payment = result['payment']
            return jsonify({
                'payment_id': payment['id'],
                'status': payment['status'],
                'status_detail': payment.get('status_detail'),
                'payment_method': payment.get('payment_method_id'),
                'amount': payment.get('transaction_amount'),
                'currency': payment.get('currency_id'),
                'date_approved': payment.get('date_approved'),
                'date_created': payment.get('date_created')
            })
        else:
            return jsonify({'error': result['error']}), 400
            
    except Exception as e:
        logging.error(f"Error checking payment status for order {order_id}: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

@payments_bp.route('/config')
@login_required
def payment_config():
    """Retorna configurações do MercadoPago para o frontend"""
    if current_user.role not in ['admin', 'manager']:
        return jsonify({'error': 'Access denied'}), 403
    
    from config import Config
    
    return jsonify({
        'public_key': Config.MERCADOPAGO_PUBLIC_KEY,
        'sandbox': Config.MERCADOPAGO_SANDBOX
    })

@payments_bp.route('/info')
@login_required
def payment_info():
    """Mostra informações sobre o sistema de pagamento"""
    from config import Config
    return render_template('payments/info.html', config=Config)

@payments_bp.route('/test-payment/<int:order_id>')
@login_required
def test_payment(order_id):
    """Página para testar pagamentos (apenas em sandbox)"""
    if current_user.role != 'admin':
        flash('Acesso negado.', 'error')
        return redirect(url_for('orders.index'))
    
    order = Order.query.get_or_404(order_id)
    
    return render_template('payments/test.html', order=order)
