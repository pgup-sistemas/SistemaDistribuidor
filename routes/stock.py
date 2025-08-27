
from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, send_file
from flask_login import login_required, current_user
from models import Product, Category, Supplier, StockMovement, db
from sqlalchemy import or_
import pandas as pd
from io import BytesIO
import os
from werkzeug.utils import secure_filename

stock_bp = Blueprint('stock', __name__)

ALLOWED_EXTENSIONS = {'xlsx', 'xls', 'csv'}
UPLOAD_FOLDER = 'uploads'

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@stock_bp.route('/')
@login_required
def index():
    search = request.args.get('search', '')
    page = request.args.get('page', 1, type=int)
    
    query = Product.query.filter_by(active=True)
    
    if search:
        query = query.filter(
            or_(
                Product.name.ilike(f'%{search}%'),
                Product.sku.ilike(f'%{search}%'),
                Product.description.ilike(f'%{search}%')
            )
        )
    
    products = query.order_by(Product.name).paginate(
        page=page, per_page=20, error_out=False
    )
    
    return render_template('stock/index.html', products=products, search=search)

@stock_bp.route('/movements')
@login_required
def movements():
    page = request.args.get('page', 1, type=int)
    product_id = request.args.get('product_id', type=int)
    
    query = StockMovement.query
    
    if product_id:
        query = query.filter_by(product_id=product_id)
    
    movements = query.order_by(StockMovement.created_at.desc()).paginate(
        page=page, per_page=20, error_out=False
    )
    
    products = Product.query.filter_by(active=True).all()
    selected_product = Product.query.get(product_id) if product_id else None
    
    return render_template('stock/movements.html', 
                         movements=movements, 
                         products=products,
                         selected_product=selected_product)

@stock_bp.route('/movement', methods=['GET', 'POST'])
@login_required
def movement():
    if current_user.role not in ['admin', 'stock_manager', 'manager']:
        flash('Acesso negado.', 'error')
        return redirect(url_for('dashboard.index'))
    
    if request.method == 'POST':
        try:
            product_id = request.form.get('product_id')
            movement_type = request.form.get('movement_type')
            quantity = int(request.form.get('quantity'))
            reason = request.form.get('reason')
            
            product = Product.query.get_or_404(product_id)
            
            # Create movement
            movement = StockMovement(
                product_id=product_id,
                movement_type=movement_type,
                quantity=quantity,
                reason=reason,
                user_id=current_user.id
            )
            
            # Update product stock
            if movement_type == 'entry':
                product.current_stock += quantity
            elif movement_type == 'exit':
                if product.current_stock < quantity:
                    flash('Quantidade insuficiente em estoque.', 'error')
                    return redirect(request.url)
                product.current_stock -= quantity
            elif movement_type == 'adjustment':
                product.current_stock = quantity
                movement.quantity = quantity - product.current_stock
            
            db.session.add(movement)
            db.session.commit()
            
            flash('Movimentação registrada com sucesso!', 'success')
            return redirect(url_for('stock.movements'))
            
        except Exception as e:
            db.session.rollback()
            flash(f'Erro ao registrar movimentação: {str(e)}', 'error')
    
    products = Product.query.filter_by(active=True).order_by(Product.name).all()
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
                        old_stock = product.current_stock
                        product.current_stock += int(row['quantity'])
                        
                        # Create stock movement
                        movement = StockMovement(
                            product_id=product.id,
                            movement_type='entry',
                            quantity=int(row['quantity']),
                            reason=f'Importação planilha: {file.filename}',
                            user_id=current_user.id
                        )
                        db.session.add(movement)
                    else:
                        # Create new product
                        # Get or create category
                        category = None
                        if 'category' in row and pd.notna(row['category']):
                            category = Category.query.filter_by(name=str(row['category']), active=True).first()
                            if not category:
                                category = Category(name=str(row['category']), description=f'Categoria criada automaticamente')
                                db.session.add(category)
                                db.session.flush()

                        # Get or create supplier
                        supplier = None
                        if 'supplier' in row and pd.notna(row['supplier']):
                            supplier = Supplier.query.filter_by(name=str(row['supplier']), active=True).first()
                            if not supplier:
                                supplier = Supplier(
                                    name=str(row['supplier']),
                                    email='',
                                    phone='',
                                    address='Endereço não informado'
                                )
                                db.session.add(supplier)
                                db.session.flush()

                        product = Product(
                            sku=str(row['sku']),
                            name=str(row['name']),
                            description=str(row.get('description', '')),
                            sale_price=float(row['sale_price']),
                            cost_price=float(row.get('cost_price', row['sale_price'] * 0.7)),
                            current_stock=int(row['quantity']),
                            minimum_stock=int(row.get('minimum_stock', 0)),
                            unit=str(row.get('unit', 'UN')),
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
    """Handle invoice-based import (simplified version)"""
    if 'invoice_file' not in request.files:
        flash('Nenhum arquivo de nota fiscal selecionado.', 'error')
        return redirect(request.url)

    file = request.files['invoice_file']
    supplier_id = request.form.get('supplier_id')
    
    if not supplier_id:
        flash('Fornecedor é obrigatório para importação de nota fiscal.', 'error')
        return redirect(request.url)

    if file.filename == '':
        flash('Nenhum arquivo selecionado.', 'error')
        return redirect(request.url)

    if file and allowed_file(file.filename):
        try:
            # Read the invoice file
            if file.filename.endswith('.csv'):
                df = pd.read_csv(file)
            else:
                df = pd.read_excel(file)

            # Expected columns for invoice: product_code, product_name, quantity, unit_price
            required_columns = ['product_code', 'product_name', 'quantity', 'unit_price']

            # Check if required columns exist
            missing_columns = [col for col in required_columns if col not in df.columns]
            if missing_columns:
                flash(f'Colunas obrigatórias da nota fiscal faltando: {", ".join(missing_columns)}', 'error')
                return redirect(request.url)

            success_count = 0
            error_count = 0
            errors = []

            for index, row in df.iterrows():
                try:
                    # Look for existing product by SKU or create new
                    product = Product.query.filter_by(sku=str(row['product_code']), active=True).first()
                    
                    if not product:
                        # Create new product from invoice
                        product = Product(
                            sku=str(row['product_code']),
                            name=str(row['product_name']),
                            description=f'Produto importado da NF: {file.filename}',
                            sale_price=float(row['unit_price']) * 1.3,  # 30% markup
                            cost_price=float(row['unit_price']),
                            current_stock=int(row['quantity']),
                            minimum_stock=5,
                            unit='UN',
                            supplier_id=supplier_id
                        )
                        db.session.add(product)
                        db.session.flush()
                    else:
                        # Update existing product
                        product.current_stock += int(row['quantity'])
                        product.cost_price = float(row['unit_price'])  # Update cost price

                    # Create stock movement
                    movement = StockMovement(
                        product_id=product.id,
                        movement_type='entry',
                        quantity=int(row['quantity']),
                        reason=f'Entrada NF: {file.filename}',
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
                flash(f'Importação de nota fiscal concluída! {success_count} produtos processados.', 'success')

            if error_count > 0:
                flash(f'{error_count} erros encontrados: {"; ".join(errors[:5])}', 'warning')

        except Exception as e:
            db.session.rollback()
            flash(f'Erro ao processar nota fiscal: {str(e)}', 'error')

    else:
        flash('Tipo de arquivo não permitido. Use Excel (.xlsx, .xls) ou CSV.', 'error')

    return redirect(url_for('stock.bulk_import'))
