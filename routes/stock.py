from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, send_file
from flask_login import login_required, current_user
from models import Product, StockMovement, Category, Supplier, db
from sqlalchemy import desc
from decimal import Decimal
import pandas as pd
import os
from werkzeug.utils import secure_filename
from io import BytesIO

stock_bp = Blueprint('stock', __name__)

ALLOWED_EXTENSIONS = {'xlsx', 'xls', 'csv'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@stock_bp.route('/')
@login_required
def index():
    page = request.args.get('page', 1, type=int)
    search = request.args.get('search', '')

    query = Product.query.filter_by(active=True)

    if search:
        query = query.filter(Product.name.ilike(f'%{search}%'))

    products = query.order_by(Product.name).paginate(
        page=page, per_page=20, error_out=False)

    return render_template('stock/index.html', products=products, search=search)

@stock_bp.route('/movements')
@login_required
def movements():
    page = request.args.get('page', 1, type=int)
    product_id = request.args.get('product_id', type=int)

    query = StockMovement.query

    if product_id:
        query = query.filter_by(product_id=product_id)

    movements = query.order_by(desc(StockMovement.created_at)).paginate(
        page=page, per_page=20, error_out=False)

    products = Product.query.filter_by(active=True).all()

    return render_template('stock/movements.html',
                         movements=movements,
                         products=products,
                         selected_product=product_id)

@stock_bp.route('/movement/new', methods=['GET', 'POST'])
@login_required
def new_movement():
    if request.method == 'POST':
        product_id = request.form.get('product_id', type=int)
        movement_type = request.form.get('movement_type')
        quantity = request.form.get('quantity', type=int)
        reason = request.form.get('reason')

        if not all([product_id, movement_type, quantity, reason]):
            flash('Todos os campos são obrigatórios.', 'error')
            return render_template('stock/movement.html',
                                 products=Product.query.filter_by(active=True).all())

        product = Product.query.get_or_404(product_id)

        if movement_type not in ['entry', 'exit', 'adjustment']:
            flash('Tipo de movimentação inválido.', 'error')
            return render_template('stock/movement.html',
                                 products=Product.query.filter_by(active=True).all())

        if quantity <= 0:
            flash('Quantidade deve ser maior que zero.', 'error')
            return render_template('stock/movement.html',
                                 products=Product.query.filter_by(active=True).all())

        # Check if exit movement doesn't exceed stock
        if movement_type == 'exit' and product.current_stock < quantity:
            flash('Quantidade não pode ser maior que o estoque atual.', 'error')
            return render_template('stock/movement.html',
                                 products=Product.query.filter_by(active=True).all())

        # Update product stock
        if movement_type == 'entry':
            product.current_stock += quantity
        elif movement_type == 'exit':
            product.current_stock -= quantity
        else:  # adjustment
            product.current_stock = quantity

        # Create movement record
        movement = StockMovement(
            product_id=product_id,
            movement_type=movement_type,
            quantity=quantity,
            reason=reason,
            user_id=current_user.id
        )

        db.session.add(movement)
        db.session.commit()

        flash('Movimentação registrada com sucesso!', 'success')
        return redirect(url_for('stock.movements'))

    products = Product.query.filter_by(active=True).all()
    return render_template('stock/movement.html', products=products)

@stock_bp.route('/alerts')
@login_required
def alerts():
    # Get products with stock below minimum
    low_stock_products = Product.query.filter(
        Product.current_stock <= Product.minimum_stock,
        Product.active == True
    ).order_by(Product.minimum_stock.desc()).all()

    return render_template('stock/alerts.html', products=low_stock_products)

@stock_bp.route('/import', methods=['GET', 'POST'])
@login_required
def bulk_import():
    if current_user.role not in ['admin', 'stock_manager', 'manager']:
        flash('Acesso negado.', 'error')
        return redirect(url_for('dashboard.index'))

    if request.method == 'POST':
        import_type = request.form.get('import_type')

        if import_type == 'spreadsheet':
            return handle_spreadsheet_import()
        elif import_type == 'invoice':
            return handle_invoice_import()

    categories = Category.query.filter_by(active=True).all()
    suppliers = Supplier.query.filter_by(active=True).all()

    return render_template('stock/import.html', categories=categories, suppliers=suppliers)

def handle_spreadsheet_import():
    if 'file' not in request.files:
        flash('Nenhum arquivo selecionado.', 'error')
        return redirect(request.url)

    file = request.files['file']
    if file.filename == '':
        flash('Nenhum arquivo selecionado.', 'error')
        return redirect(request.url)

    if file and allowed_file(file.filename):
        try:
            # Read the spreadsheet
            if file.filename.endswith('.csv'):
                df = pd.read_csv(file)
            else:
                df = pd.read_excel(file)

            # Expected columns: sku, name, description, sale_price, cost_price, quantity, category, supplier
            required_columns = ['sku', 'name', 'sale_price', 'quantity']

            # Check if required columns exist
            missing_columns = [col for col in required_columns if col not in df.columns]
            if missing_columns:
                flash(f'Colunas obrigatórias faltando: {", ".join(missing_columns)}', 'error')
                return redirect(request.url)

            success_count = 0
            error_count = 0
            errors = []

            for index, row in df.iterrows():
                try:
                    # Check if product already exists
                    product = Product.query.filter_by(sku=str(row['sku']), active=True).first()

                    if product:
                        # Update existing product stock
                        quantity = int(row['quantity'])
                        product.current_stock += quantity

                        # Create stock movement
                        movement = StockMovement(
                            product_id=product.id,
                            movement_type='entry',
                            quantity=quantity,
                            reason=f'Importação em massa - arquivo: {file.filename}',
                            user_id=current_user.id
                        )
                        db.session.add(movement)
                    else:
                        # Create new product
                        category = None
                        if 'category' in row and pd.notna(row['category']):
                            category = Category.query.filter_by(name=str(row['category']), active=True).first()

                        supplier = None
                        if 'supplier' in row and pd.notna(row['supplier']):
                            supplier = Supplier.query.filter_by(name=str(row['supplier']), active=True).first()

                        product = Product(
                            sku=str(row['sku']),
                            name=str(row['name']),
                            description=str(row.get('description', '')) if pd.notna(row.get('description')) else '',
                            sale_price=Decimal(str(row['sale_price'])),
                            cost_price=Decimal(str(row.get('cost_price', 0))) if pd.notna(row.get('cost_price')) else None,
                            current_stock=int(row['quantity']),
                            minimum_stock=int(row.get('minimum_stock', 0)) if pd.notna(row.get('minimum_stock')) else 0,
                            unit=str(row.get('unit', 'UN')) if pd.notna(row.get('unit')) else 'UN',
                            category_id=category.id if category else None,
                            supplier_id=supplier.id if supplier else None
                        )
                        db.session.add(product)
                        db.session.flush()

                        # Create stock movement for new product
                        if int(row['quantity']) > 0:
                            movement = StockMovement(
                                product_id=product.id,
                                movement_type='entry',
                                quantity=int(row['quantity']),
                                reason=f'Estoque inicial - importação: {file.filename}',
                                user_id=current_user.id
                            )
                            db.session.add(movement)

                    success_count += 1

                except Exception as e:
                    error_count += 1
                    errors.append(f'Linha {index + 2}: {str(e)}')
                    db.session.rollback()

            if success_count > 0:
                db.session.commit()
                flash(f'Importação concluída! {success_count} produtos processados com sucesso.', 'success')

            if error_count > 0:
                flash(f'{error_count} erros encontrados: {"; ".join(errors[:5])}', 'warning')

        except Exception as e:
            db.session.rollback()
            flash(f'Erro ao processar arquivo: {str(e)}', 'error')

    else:
        flash('Tipo de arquivo não permitido. Use Excel (.xlsx, .xls) ou CSV.', 'error')

    return redirect(url_for('stock.bulk_import'))

def handle_invoice_import():
    # Get form data for invoice import
    supplier_id = request.form.get('supplier_id', type=int)
    invoice_number = request.form.get('invoice_number')

    if not supplier_id or not invoice_number:
        flash('Fornecedor e número da nota fiscal são obrigatórios.', 'error')
        return redirect(request.url)

    # Get products from form
    products_data = []
    i = 0
    while f'product_sku_{i}' in request.form:
        sku = request.form.get(f'product_sku_{i}')
        quantity = request.form.get(f'product_quantity_{i}', type=int)
        cost_price = request.form.get(f'product_cost_{i}')

        if sku and quantity:
            products_data.append({
                'sku': sku,
                'quantity': quantity,
                'cost_price': Decimal(str(cost_price)) if cost_price else None
            })
        i += 1

    if not products_data:
        flash('Nenhum produto informado.', 'error')
        return redirect(request.url)

    success_count = 0
    error_count = 0
    errors = []

    try:
        for product_data in products_data:
            product = Product.query.filter_by(sku=product_data['sku'], active=True).first()

            if product:
                # Update stock
                product.current_stock += product_data['quantity']

                # Update cost price if provided
                if product_data['cost_price']:
                    product.cost_price = product_data['cost_price']

                # Create stock movement
                movement = StockMovement(
                    product_id=product.id,
                    movement_type='entry',
                    quantity=product_data['quantity'],
                    reason=f'Nota Fiscal #{invoice_number} - Fornecedor: {Supplier.query.get(supplier_id).name}',
                    user_id=current_user.id
                )
                db.session.add(movement)
                success_count += 1
            else:
                error_count += 1
                errors.append(f'Produto não encontrado: {product_data["sku"]}')

        if success_count > 0:
            db.session.commit()
            flash(f'Nota fiscal importada! {success_count} produtos atualizados.', 'success')

        if error_count > 0:
            flash(f'{error_count} erros: {"; ".join(errors)}', 'warning')

    except Exception as e:
        db.session.rollback()
        flash(f'Erro ao processar nota fiscal: {str(e)}', 'error')

    return redirect(url_for('stock.bulk_import'))

@stock_bp.route('/download-template')
@login_required
def download_template():
    if current_user.role not in ['admin', 'stock_manager', 'manager']:
        flash('Acesso negado.', 'error')
        return redirect(url_for('dashboard.index'))

    try:
        # Create sample data for template
        data = {
            'sku': ['PROD001', 'PROD002'],
            'name': ['Produto Exemplo 1', 'Produto Exemplo 2'],
            'description': ['Descrição do produto 1', 'Descrição do produto 2'],
            'sale_price': [10.50, 25.00],
            'cost_price': [8.00, 20.00],
            'quantity': [100, 50],
            'minimum_stock': [10, 5],
            'unit': ['UN', 'KG'],
            'category': ['Categoria A', 'Categoria B'],
            'supplier': ['Fornecedor X', 'Fornecedor Y']
        }

        df = pd.DataFrame(data)

        # Create response
        output = BytesIO()
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            df.to_excel(writer, index=False, sheet_name='Produtos')

        output.seek(0)

        return send_file(
            output,
            mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            as_attachment=True,
            download_name='modelo_importacao_produtos.xlsx'
        )

    except Exception as e:
        flash(f'Erro ao gerar modelo: {str(e)}', 'error')
        return redirect(url_for('stock.bulk_import'))