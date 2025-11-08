from flask import Blueprint, render_template, request, make_response
from flask_login import login_required
from models import Order, Product, Customer, Category, StockMovement, db
from sqlalchemy import func, and_, desc
from datetime import datetime, timedelta
import csv
import io

# Try to import WeasyPrint for PDF generation
try:
    import weasyprint
    from weasyprint import HTML, CSS
    from weasyprint.text.fonts import FontConfiguration
    WEASYPRINT_AVAILABLE = True
except (ImportError, OSError) as e:
    WEASYPRINT_AVAILABLE = False
    print(f"WeasyPrint not available, PDF generation disabled: {e}")
    weasyprint = None
    HTML = None
    CSS = None
    FontConfiguration = None

reports_bp = Blueprint('reports', __name__)

@reports_bp.route('/')
@login_required
def index():
    # Calculate summary metrics
    from datetime import datetime, timedelta

    # Last 30 days sales
    thirty_days_ago = datetime.utcnow() - timedelta(days=30)
    recent_sales = db.session.query(
        func.sum(Order.total).label('total'),
        func.count(Order.id).label('orders')
    ).filter(
        and_(
            Order.created_at >= thirty_days_ago,
            Order.status != 'cancelled'
        )
    ).first()

    # Active products count
    active_products = Product.query.filter_by(active=True).count()
    categories_count = Category.query.filter_by(active=True).count()

    # Active customers count
    active_customers = Customer.query.filter_by(active=True).count()

    # Low stock alerts
    low_stock_count = Product.query.filter(
        and_(
            Product.current_stock <= Product.minimum_stock,
            Product.active == True
        )
    ).count()

    return render_template('reports/index.html',
                          recent_sales_total=recent_sales.total or 0,
                          recent_sales_orders=recent_sales.orders or 0,
                          active_products=active_products,
                          categories_count=categories_count,
                          active_customers=active_customers,
                          low_stock_count=low_stock_count,
                          weasyprint_available=WEASYPRINT_AVAILABLE)

@reports_bp.route('/sales')
@login_required
def sales():
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    payment_method = request.args.get('payment_method')
    customer_id = request.args.get('customer_id')
    category_id = request.args.get('category_id')
    export_format = request.args.get('export')
    page = int(request.args.get('page', 1))
    per_page = int(request.args.get('per_page', 25))

    # Default to last 30 days if no dates provided
    if not start_date:
        start_date = (datetime.utcnow() - timedelta(days=30)).strftime('%Y-%m-%d')
    if not end_date:
        end_date = datetime.utcnow().strftime('%Y-%m-%d')

    # Convert to datetime
    start_dt = datetime.strptime(start_date, '%Y-%m-%d')
    end_dt = datetime.strptime(end_date, '%Y-%m-%d') + timedelta(days=1)

    # Build base query with filters
    from models import OrderItem
    query = Order.query.filter(
        and_(
            Order.created_at >= start_dt,
            Order.created_at < end_dt,
            Order.status != 'cancelled'
        )
    )

    if payment_method:
        query = query.filter(Order.payment_method == payment_method)
    if customer_id:
        query = query.filter(Order.customer_id == customer_id)

    # Filter by category if specified
    if category_id:
        query = query.join(OrderItem).join(Product).filter(Product.category_id == category_id)

    # Get total count for pagination
    total_orders_count = query.count()

    # Apply pagination
    orders = query.order_by(Order.created_at.desc()).paginate(page=page, per_page=per_page, error_out=False).items

    # Calculate totals from all orders (not just paginated)
    total_query = Order.query.filter(
        and_(
            Order.created_at >= start_dt,
            Order.created_at < end_dt,
            Order.status != 'cancelled'
        )
    )

    if payment_method:
        total_query = total_query.filter(Order.payment_method == payment_method)
    if customer_id:
        total_query = total_query.filter(Order.customer_id == customer_id)
    if category_id:
        total_query = total_query.join(OrderItem).join(Product).filter(Product.category_id == category_id)

    all_orders = total_query.all()
    total_sales = sum(order.total for order in all_orders)
    total_orders = len(all_orders)
    
    # Sales by day
    daily_query = db.session.query(
        func.date(Order.created_at).label('date'),
        func.sum(Order.total).label('total'),
        func.count(Order.id).label('orders')
    ).filter(
        and_(
            Order.created_at >= start_dt,
            Order.created_at < end_dt,
            Order.status != 'cancelled'
        )
    )

    if payment_method:
        daily_query = daily_query.filter(Order.payment_method == payment_method)
    if customer_id:
        daily_query = daily_query.filter(Order.customer_id == customer_id)
    if category_id:
        daily_query = daily_query.join(OrderItem, Order.id == OrderItem.order_id).join(Product, OrderItem.product_id == Product.id).filter(Product.category_id == category_id)

    daily_sales_raw = daily_query.group_by(func.date(Order.created_at)).order_by('date').all()

    # Convert to dict for JSON serialization
    daily_sales = []
    for row in daily_sales_raw:
        try:
            date_str = row.date.strftime('%Y-%m-%d') if row.date else None
            daily_sales.append({
                'date': date_str,
                'total': float(row.total or 0),
                'orders': int(row.orders or 0)
            })
        except (AttributeError, TypeError):
            # Skip invalid rows
            continue
    
    # Sales by payment method
    payment_query = db.session.query(
        Order.payment_method,
        func.sum(Order.total).label('total'),
        func.count(Order.id).label('orders')
    ).filter(
        and_(
            Order.created_at >= start_dt,
            Order.created_at < end_dt,
            Order.status != 'cancelled'
        )
    )

    if payment_method:
        payment_query = payment_query.filter(Order.payment_method == payment_method)
    if customer_id:
        payment_query = payment_query.filter(Order.customer_id == customer_id)
    if category_id:
        payment_query = payment_query.join(OrderItem, Order.id == OrderItem.order_id).join(Product, OrderItem.product_id == Product.id).filter(Product.category_id == category_id)

    payment_sales_raw = payment_query.group_by(Order.payment_method).all()

    # Convert to dict for JSON serialization
    payment_sales = []
    for row in payment_sales_raw:
        payment_sales.append({
            'payment_method': row.payment_method or 'unknown',
            'total': float(row.total or 0),
            'orders': int(row.orders or 0)
        })

    # Get filter options
    customers = Customer.query.filter_by(active=True).order_by(Customer.name).all()
    categories = Category.query.filter_by(active=True).order_by(Category.name).all()

    # Calculate comparison with previous period
    period_days = (end_dt - start_dt).days
    prev_start_dt = start_dt - timedelta(days=period_days)
    prev_end_dt = start_dt

    prev_orders = Order.query.filter(
        and_(
            Order.created_at >= prev_start_dt,
            Order.created_at < prev_end_dt,
            Order.status != 'cancelled'
        )
    ).all()

    prev_total_sales = sum(order.total for order in prev_orders)
    prev_total_orders = len(prev_orders)

    # Calculate growth percentages
    sales_growth = ((total_sales - prev_total_sales) / prev_total_sales * 100) if prev_total_sales > 0 else 0
    orders_growth = ((total_orders - prev_total_orders) / prev_total_orders * 100) if prev_total_orders > 0 else 0

    if export_format == 'csv':
        return export_sales_csv(orders, start_date, end_date)
    elif export_format == 'pdf':
        if not WEASYPRINT_AVAILABLE:
            from flask import flash, redirect, url_for
            flash('PDF export não está disponível. WeasyPrint não foi instalado corretamente.', 'warning')
            return redirect(url_for('reports.sales', start_date=start_date, end_date=end_date,
                                  payment_method=payment_method, customer_id=customer_id, category_id=category_id))
        return export_sales_pdf(orders, start_date, end_date, total_sales, total_orders, daily_sales, payment_sales)

    # Calculate pagination info
    total_pages = (total_orders_count + per_page - 1) // per_page
    has_next = page < total_pages
    has_prev = page > 1
    next_page = page + 1 if has_next else None
    prev_page = page - 1 if has_prev else None

    return render_template('reports/sales.html',
                           orders=orders,
                           total_sales=total_sales,
                           total_orders=total_orders,
                           daily_sales=daily_sales,
                           payment_sales=payment_sales,
                           start_date=start_date,
                           end_date=end_date,
                           customers=customers,
                           categories=categories,
                           filters={
                               'payment_method': payment_method,
                               'customer_id': customer_id,
                               'category_id': category_id
                           },
                           prev_total_sales=prev_total_sales,
                           prev_total_orders=prev_total_orders,
                           sales_growth=sales_growth,
                           orders_growth=orders_growth,
                           weasyprint_available=WEASYPRINT_AVAILABLE,
                           # Pagination data
                           page=page,
                           per_page=per_page,
                           total_pages=total_pages,
                           total_orders_count=total_orders_count,
                           has_next=has_next,
                           has_prev=has_prev,
                           next_page=next_page,
                           prev_page=prev_page)

@reports_bp.route('/products')
@login_required
def products():
    page = int(request.args.get('page', 1))
    per_page = int(request.args.get('per_page', 25))

    # Most sold products - get total count first
    from models import OrderItem
    total_products_query = db.session.query(
        Product.id
    ).select_from(Product).join(OrderItem, Product.id == OrderItem.product_id).join(Order, OrderItem.order_id == Order.id).filter(
        Order.status != 'cancelled'
    ).group_by(Product.id)

    total_products = total_products_query.count()

    # Get paginated top products
    top_products = db.session.query(
        Product.name,
        func.sum(OrderItem.quantity).label('total_sold'),
        func.sum(OrderItem.quantity * OrderItem.unit_price).label('revenue')
    ).select_from(Product).join(OrderItem, Product.id == OrderItem.product_id).join(Order, OrderItem.order_id == Order.id).filter(
        Order.status != 'cancelled'
    ).group_by(Product.id, Product.name).order_by(desc(func.sum(OrderItem.quantity))).offset((page - 1) * per_page).limit(per_page).all()

    # Low stock products
    low_stock = Product.query.filter(
        Product.current_stock <= Product.minimum_stock,
        Product.active == True
    ).all()

    # Convert to dict for template
    top_products_dict = [{'name': row.name, 'total_sold': int(row.total_sold or 0), 'revenue': float(row.revenue or 0)} for row in top_products]

    # Pagination info
    total_pages = (total_products + per_page - 1) // per_page
    has_next = page < total_pages
    has_prev = page > 1
    next_page = page + 1 if has_next else None
    prev_page = page - 1 if has_prev else None

    return render_template('reports/products.html',
                           top_products=top_products_dict,
                           low_stock=low_stock,
                           # Pagination data
                           page=page,
                           per_page=per_page,
                           total_pages=total_pages,
                           total_products=total_products,
                           has_next=has_next,
                           has_prev=has_prev,
                           next_page=next_page,
                           prev_page=prev_page)

@reports_bp.route('/customers')
@login_required
def customers():
    # Top customers by revenue
    top_customers = db.session.query(
        Customer.name,
        Customer.phone,
        Customer.created_at,
        func.sum(Order.total).label('total_spent'),
        func.count(Order.id).label('order_count')
    ).select_from(Customer).join(Order, Customer.id == Order.customer_id).filter(
        Order.status != 'cancelled'
    ).group_by(Customer.id, Customer.name, Customer.phone, Customer.created_at).order_by(desc(func.sum(Order.total))).limit(20).all()

    # Convert to dict for JSON serialization
    top_customers_dict = []
    for row in top_customers:
        top_customers_dict.append({
            'name': row.name,
            'phone': row.phone,
            'created_at': row.created_at,
            'total_spent': float(row.total_spent or 0),
            'order_count': int(row.order_count or 0)
        })

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

def export_sales_pdf(orders, start_date, end_date, total_sales, total_orders, daily_sales, payment_sales):
    # Generate HTML content for PDF
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <title>Relatório de Vendas - {start_date} a {end_date}</title>
        <style>
            body {{ font-family: Arial, sans-serif; margin: 20px; }}
            .header {{ text-align: center; border-bottom: 2px solid #333; padding-bottom: 20px; margin-bottom: 30px; }}
            .summary {{ display: flex; justify-content: space-around; margin-bottom: 30px; }}
            .summary-item {{ text-align: center; padding: 20px; border: 1px solid #ddd; border-radius: 5px; }}
            .summary-item h3 {{ margin: 0; color: #007bff; }}
            .summary-item p {{ margin: 5px 0 0 0; color: #666; }}
            table {{ width: 100%; border-collapse: collapse; margin-top: 20px; }}
            th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
            th {{ background-color: #f8f9fa; font-weight: bold; }}
            .payment-methods {{ margin-top: 30px; }}
            .payment-method {{ display: flex; justify-content: space-between; padding: 5px 0; border-bottom: 1px solid #eee; }}
        </style>
    </head>
    <body>
        <div class="header">
            <h1>Relatório de Vendas</h1>
            <p>Período: {start_date} a {end_date}</p>
            <p>Gerado em: {datetime.now().strftime('%d/%m/%Y %H:%M')}</p>
        </div>

        <div class="summary">
            <div class="summary-item">
                <h3>R$ {total_sales:.2f}</h3>
                <p>Total de Vendas</p>
            </div>
            <div class="summary-item">
                <h3>{total_orders}</h3>
                <p>Total de Pedidos</p>
            </div>
        </div>

        <div class="payment-methods">
            <h3>Por Método de Pagamento</h3>
    """

    for payment in payment_sales:
        method_name = {
            'cash': 'Dinheiro',
            'card': 'Cartão',
            'pix': 'PIX',
            'bank_slip': 'Boleto'
        }.get(payment['payment_method'], payment['payment_method'])
        html_content += f"""
            <div class="payment-method">
                <span>{method_name}</span>
                <span>R$ {payment['total']:.2f} ({payment['orders']} pedidos)</span>
            </div>
        """

    html_content += """
        </div>

        <h3>Detalhamento de Pedidos</h3>
        <table>
            <thead>
                <tr>
                    <th>Data</th>
                    <th>Pedido</th>
                    <th>Cliente</th>
                    <th>Pagamento</th>
                    <th>Total</th>
                    <th>Status</th>
                </tr>
            </thead>
            <tbody>
    """

    for order in orders:
        payment_name = {
            'cash': 'Dinheiro',
            'card': 'Cartão',
            'pix': 'PIX',
            'bank_slip': 'Boleto'
        }.get(order.payment_method, order.payment_method)

        status_name = {
            'pending': 'Pendente',
            'confirmed': 'Confirmado',
            'preparing': 'Preparando',
            'delivered': 'Entregue',
            'cancelled': 'Cancelado'
        }.get(order.status, order.status)

        html_content += f"""
                <tr>
                    <td>{order.created_at.strftime('%d/%m/%Y %H:%M')}</td>
                    <td>#{order.id}</td>
                    <td>{order.customer.name}</td>
                    <td>{payment_name}</td>
                    <td>R$ {order.total:.2f}</td>
                    <td>{status_name}</td>
                </tr>
        """

    html_content += """
            </tbody>
        </table>
    </body>
    </html>
    """

    # Generate PDF
    font_config = FontConfiguration()
    html_doc = HTML(string=html_content)
    pdf_bytes = html_doc.write_pdf(font_config=font_config)

    response = make_response(pdf_bytes)
    response.headers['Content-Type'] = 'application/pdf'
    response.headers['Content-Disposition'] = f'attachment; filename=relatorio_vendas_{start_date}_{end_date}.pdf'

    return response
