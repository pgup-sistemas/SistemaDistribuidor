from flask import Blueprint, render_template
from flask_login import login_required, current_user
from sqlalchemy import func, and_
from datetime import datetime, timedelta
from models import Order, Product, Customer, StockMovement, db

dashboard_bp = Blueprint('dashboard', __name__)

@dashboard_bp.route('/')
@login_required
def index():
    # Calculate KPIs
    today = datetime.utcnow().date()
    
    # Today's sales
    today_sales = db.session.query(func.sum(Order.total)).filter(
        func.date(Order.created_at) == today,
        Order.status != 'cancelled'
    ).scalar() or 0
    
    # Today's orders count
    today_orders = Order.query.filter(
        func.date(Order.created_at) == today,
        Order.status != 'cancelled'
    ).count()
    
    # Low stock products
    low_stock_products = Product.query.filter(
        Product.current_stock <= Product.minimum_stock,
        Product.active == True
    ).all()
    
    # Total customers
    total_customers = Customer.query.filter_by(active=True).count()
    
    # Recent orders
    recent_orders = Order.query.filter(
        Order.status != 'cancelled'
    ).order_by(Order.created_at.desc()).limit(5).all()
    
    # Sales chart data (last 7 days)
    sales_data = []
    for i in range(7):
        date = today - timedelta(days=i)
        daily_sales = db.session.query(func.sum(Order.total)).filter(
            func.date(Order.created_at) == date,
            Order.status != 'cancelled'
        ).scalar() or 0
        sales_data.append({
            'date': date.strftime('%d/%m'),
            'sales': float(daily_sales)
        })
    
    sales_data.reverse()
    
    return render_template('dashboard/index.html',
                         today_sales=today_sales,
                         today_orders=today_orders,
                         low_stock_count=len(low_stock_products),
                         total_customers=total_customers,
                         low_stock_products=low_stock_products,
                         recent_orders=recent_orders,
                         sales_data=sales_data)
