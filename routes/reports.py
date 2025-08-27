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
    daily_sales_raw = db.session.query(
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
    
    # Convert to dict for JSON serialization
    daily_sales = [{'date': str(row.date), 'total': float(row.total), 'orders': row.orders} for row in daily_sales_raw]
    
    # Sales by payment method
    payment_sales_raw = db.session.query(
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
    
    # Convert to dict for JSON serialization
    payment_sales = [{'payment_method': row.payment_method, 'total': float(row.total), 'orders': row.orders} for row in payment_sales_raw]
    
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
    from models import OrderItem
    top_products = db.session.query(
        Product.name,
        func.sum(OrderItem.quantity).label('total_sold'),
        func.sum(OrderItem.quantity * OrderItem.unit_price).label('revenue')
    ).join(OrderItem).join(Order).filter(
        Order.status != 'cancelled'
    ).group_by(Product.id, Product.name).order_by(desc('total_sold')).limit(20).all()
    
    # Low stock products
    low_stock = Product.query.filter(
        Product.current_stock <= Product.minimum_stock,
        Product.active == True
    ).all()
    
    # Convert to dict for template
    top_products_dict = [{'name': row.name, 'total_sold': row.total_sold, 'revenue': float(row.revenue)} for row in top_products]
    
    return render_template('reports/products.html',
                         top_products=top_products_dict,
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
    
    # Convert to dict for JSON serialization
    top_customers_dict = [{'name': row.name, 'total_spent': float(row.total_spent), 'order_count': row.order_count} for row in top_customers]
    
    return render_template('reports/customers.html', top_customers=top_customers_dict)

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
