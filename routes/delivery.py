from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from models import Order, Delivery, User, db
from services.email_service import EmailService
from datetime import datetime

delivery_bp = Blueprint('delivery', __name__)

@delivery_bp.route('/')
@login_required
def index():
    """Lista todas as entregas"""
    if current_user.role not in ['admin', 'delivery', 'manager']:
        flash('Acesso negado.', 'error')
        return redirect(url_for('dashboard.index'))
    
    page = request.args.get('page', 1, type=int)
    status = request.args.get('status', '')
    
    query = Delivery.query
    
    if status:
        query = query.filter_by(status=status)
    
    # Se for entregador, mostrar apenas suas entregas
    if current_user.role == 'delivery':
        query = query.filter_by(delivery_user_id=current_user.id)
    
    deliveries = query.order_by(Delivery.created_at.desc()).paginate(
        page=page, per_page=20, error_out=False)
    
    return render_template('delivery/index.html', deliveries=deliveries, selected_status=status)

@delivery_bp.route('/assign/<int:order_id>')
@login_required
def assign(order_id):
    """Atribuir pedido para entrega"""
    if current_user.role not in ['admin', 'manager']:
        flash('Acesso negado.', 'error')
        return redirect(url_for('orders.index'))
    
    order = Order.query.get_or_404(order_id)
    
    # Verificar se o pedido já tem entrega
    if order.delivery:
        flash('Este pedido já possui uma entrega atribuída.', 'warning')
        return redirect(url_for('orders.view', id=order_id))
    
    # Verificar se o pedido está confirmado
    if order.status not in ['confirmed', 'preparing']:
        flash('Apenas pedidos confirmados ou em preparação podem ser atribuídos para entrega.', 'error')
        return redirect(url_for('orders.view', id=order_id))
    
    # Buscar entregadores disponíveis
    delivery_users = User.query.filter_by(role='delivery', active=True).all()
    
    return render_template('delivery/assign.html', order=order, delivery_users=delivery_users)

@delivery_bp.route('/assign/<int:order_id>', methods=['POST'])
@login_required
def assign_post(order_id):
    """Processar atribuição de entrega"""
    if current_user.role not in ['admin', 'manager']:
        flash('Acesso negado.', 'error')
        return redirect(url_for('orders.index'))
    
    order = Order.query.get_or_404(order_id)
    delivery_user_id = request.form.get('delivery_user_id', type=int)
    notes = request.form.get('notes', '')
    
    if not delivery_user_id:
        flash('Selecione um entregador.', 'error')
        return redirect(url_for('delivery.assign', order_id=order_id))
    
    try:
        # Criar registro de entrega
        delivery = Delivery(
            order_id=order_id,
            delivery_user_id=delivery_user_id,
            status='pending',
            notes=notes
        )
        
        db.session.add(delivery)
        
        # Atualizar status do pedido
        order.status = 'preparing'
        
        db.session.commit()
        
        flash('Entrega atribuída com sucesso!', 'success')
        return redirect(url_for('orders.view', id=order_id))
        
    except Exception as e:
        db.session.rollback()
        flash(f'Erro ao atribuir entrega: {str(e)}', 'error')
        return redirect(url_for('delivery.assign', order_id=order_id))

@delivery_bp.route('/<int:delivery_id>/status', methods=['POST'])
@login_required
def update_status(delivery_id):
    """Atualizar status da entrega"""
    delivery = Delivery.query.get_or_404(delivery_id)
    
    # Verificar permissões
    if current_user.role not in ['admin', 'manager'] and delivery.delivery_user_id != current_user.id:
        flash('Acesso negado.', 'error')
        return redirect(url_for('delivery.index'))
    
    new_status = request.form.get('status')
    delivery_proof = request.form.get('delivery_proof', '')
    notes = request.form.get('notes', '')
    
    if new_status not in ['pending', 'in_transit', 'delivered', 'failed']:
        flash('Status inválido.', 'error')
        return redirect(url_for('delivery.index'))
    
    try:
        old_status = delivery.status
        delivery.status = new_status
        delivery.notes = notes
        
        if new_status == 'delivered':
            delivery.delivered_at = datetime.utcnow()
            delivery.delivery_proof = delivery_proof
            # Atualizar status do pedido
            delivery.order.status = 'delivered'
            
            # Enviar email de confirmação de entrega
            if delivery.order.customer.email:
                email_service = EmailService()
                email_service.send_order_status_update(
                    delivery.order, 
                    delivery.order.customer.email,
                    old_status,
                    'delivered'
                )
        
        elif new_status == 'failed':
            delivery.order.status = 'pending'  # Voltar para pendente se falhou
        
        db.session.commit()
        
        flash('Status da entrega atualizado com sucesso!', 'success')
        return redirect(url_for('delivery.index'))
        
    except Exception as e:
        db.session.rollback()
        flash(f'Erro ao atualizar status: {str(e)}', 'error')
        return redirect(url_for('delivery.index'))

@delivery_bp.route('/<int:delivery_id>')
@login_required
def view(delivery_id):
    """Visualizar detalhes da entrega"""
    delivery = Delivery.query.get_or_404(delivery_id)
    
    # Verificar permissões
    if current_user.role not in ['admin', 'manager'] and delivery.delivery_user_id != current_user.id:
        flash('Acesso negado.', 'error')
        return redirect(url_for('delivery.index'))
    
    return render_template('delivery/view.html', delivery=delivery)

@delivery_bp.route('/api/status/<int:delivery_id>')
@login_required
def api_status(delivery_id):
    """API para obter status da entrega"""
    delivery = Delivery.query.get_or_404(delivery_id)
    
    # Verificar permissões
    if current_user.role not in ['admin', 'manager'] and delivery.delivery_user_id != current_user.id:
        return jsonify({'error': 'Access denied'}), 403
    
    return jsonify({
        'id': delivery.id,
        'status': delivery.status,
        'created_at': delivery.created_at.isoformat(),
        'delivered_at': delivery.delivered_at.isoformat() if delivery.delivered_at else None,
        'notes': delivery.notes,
        'delivery_proof': delivery.delivery_proof,
        'order': {
            'id': delivery.order.id,
            'customer_name': delivery.order.customer.name,
            'customer_phone': delivery.order.customer.phone,
            'customer_address': delivery.order.customer.address,
            'total': float(delivery.order.total)
        }
    })

@delivery_bp.route('/my-deliveries')
@login_required
def my_deliveries():
    """Entregas do usuário logado (para entregadores)"""
    if current_user.role != 'delivery':
        flash('Acesso negado.', 'error')
        return redirect(url_for('dashboard.index'))
    
    page = request.args.get('page', 1, type=int)
    status = request.args.get('status', '')
    
    query = Delivery.query.filter_by(delivery_user_id=current_user.id)
    
    if status:
        query = query.filter_by(status=status)
    
    deliveries = query.order_by(Delivery.created_at.desc()).paginate(
        page=page, per_page=20, error_out=False)
    
    return render_template('delivery/my_deliveries.html', deliveries=deliveries, selected_status=status)
