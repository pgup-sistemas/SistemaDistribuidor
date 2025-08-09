from flask import Blueprint, render_template, request, make_response
from flask_login import login_required
from models import Order, Product, Customer, StockMovement, db
from sqlalchemy import func, and_, desc
from datetime import datetime, timedelta
import csv
import io

reports_bp = Blueprint('reports', __name__)

@reports_bp.route('/')
@login_required
def index():
    return render_template('reports/index.html')

@reports_bp.route('/sales')
@login_required
def sales():
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    export_format = request.args.get('export')
    
    # Default to last 30 days if no dates provided
    if not start_date:
        start_date = (datetime.utcnow() - timedelta(days=30)).strftime('%Y-%m-%d')
    if not end_date:
        end_date = datetime.utcnow().strftime('%Y-%m-%d')
    
    # Convert to datetime
    start_dt = datetime.strptime(start_date, '%Y-%m-%d')
    end_dt = datetime.strptime(end_date, '%Y-%m-%d') + timedelta(days=1)
    
    # Sales summary
    orders = Order.query.filter(
        and_(
            Order.created_at >= start_dt,
            Order.created_at < end_dt,
            Order.status != 'cancelled'
        )
    ).all()
    
    total_sales = sum(order.total for order in orders)
    total_orders = len(orders)
    
    # Sales by day
    daily_sales = db.session.query(
        func.date(Order.created_at).label('date'),
        func.sum(Order.total).label('total'),
        func.count(Order.id).label('orders')
    ).filter(
        and_(
            Order.created_at >= start_dt,
            Order.created_at < end_dt,
            Order.status != 'cancelled'
        )
    ).group_by(func.date(Order.created_at)).order_by('date').all()
    
    # Sales by payment method
    payment_sales = db.session.query(
        Order.payment_method,
        func.sum(Order.total).label('total'),
        func.count(Order.id).label('orders')
    ).filter(
        and_(
            Order.created_at >= start_dt,
            Order.created_at < end_dt,
            Order.status != 'cancelled'
        )
    ).group_by(Order.payment_method).all()
    
    if export_format == 'csv':
        return export_sales_csv(orders, start_date, end_date)
    
    return render_template('reports/sales.html',
                         orders=orders,
                         total_sales=total_sales,
                         total_orders=total_orders,
                         daily_sales=daily_sales,
                         payment_sales=payment_sales,
                         start_date=start_date,
                         end_date=end_date)

@reports_bp.route('/products')
@login_required
def products():
    # Most sold products
    top_products = db.session.query(
        Product.name,
        func.sum(Order.order_items.quantity).label('total_sold'),
        func.sum(Order.order_items.quantity * Order.order_items.unit_price).label('revenue')
    ).join(Order.order_items).join(Order).filter(
        Order.status != 'cancelled'
    ).group_by(Product.id, Product.name).order_by(desc('total_sold')).limit(20).all()
    
    # Low stock products
    low_stock = Product.query.filter(
        Product.current_stock <= Product.minimum_stock,
        Product.active == True
    ).all()
    
    return render_template('reports/products.html',
                         top_products=top_products,
                         low_stock=low_stock)

@reports_bp.route('/customers')
@login_required
def customers():
    # Top customers by revenue
    top_customers = db.session.query(
        Customer.name,
        func.sum(Order.total).label('total_spent'),
        func.count(Order.id).label('order_count')
    ).join(Order).filter(
        Order.status != 'cancelled'
    ).group_by(Customer.id, Customer.name).order_by(desc('total_spent')).limit(20).all()
    
    return render_template('reports/customers.html', top_customers=top_customers)

def export_sales_csv(orders, start_date, end_date):
    output = io.StringIO()
    writer = csv.writer(output)
    
    # CSV Headers
    writer.writerow([
        'Data', 'Pedido', 'Cliente', 'Total', 'Pagamento', 'Status'
    ])
    
    # Data rows
    for order in orders:
        writer.writerow([
            order.created_at.strftime('%d/%m/%Y %H:%M'),
            order.id,
            order.customer.name,
            f'{order.total:.2f}',
            order.payment_method,
            order.status
        ])
    
    output.seek(0)
    
    response = make_response(output.getvalue())
    response.headers['Content-Type'] = 'text/csv'
    response.headers['Content-Disposition'] = f'attachment; filename=vendas_{start_date}_{end_date}.csv'
    
    return response
