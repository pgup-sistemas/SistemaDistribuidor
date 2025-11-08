from flask import Blueprint, render_template, request, redirect, url_for, flash, current_app
from flask_login import login_required, current_user
from models import Product, Category, Supplier, StockMovement, db
from decimal import Decimal
import os
import uuid
from werkzeug.utils import secure_filename
import re

products_bp = Blueprint('products', __name__)

def allowed_file(filename):
    """Verificar se o arquivo é uma imagem válida"""
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def validate_sku(sku):
    """Validar formato do SKU"""
    if not sku:
        return False, "SKU é obrigatório"

    # Remover espaços e converter para maiúsculo
    sku = sku.strip().upper()

    # Validar formato: letras, números, hífens (máximo 20 caracteres)
    if not re.match(r'^[A-Z0-9\-]{1,20}$', sku):
        return False, "SKU deve conter apenas letras, números e hífens (máx. 20 caracteres)"

    return True, sku

def validate_product_data(sku, name, sale_price, cost_price=None):
    """Validações enterprise para dados do produto"""
    errors = []

    # Validar SKU
    sku_valid, sku_msg = validate_sku(sku)
    if not sku_valid:
        errors.append(sku_msg)
    else:
        sku = sku_msg  # Usar SKU normalizado

    # Validar nome
    if not name or len(name.strip()) < 2:
        errors.append("Nome deve ter pelo menos 2 caracteres")
    elif len(name.strip()) > 100:
        errors.append("Nome não pode exceder 100 caracteres")

    # Validar preços
    try:
        sale_price_decimal = Decimal(str(sale_price))
        if sale_price_decimal <= 0:
            errors.append("Preço de venda deve ser maior que zero")
        elif sale_price_decimal > 999999.99:
            errors.append("Preço de venda não pode exceder R$ 999.999,99")
    except:
        errors.append("Preço de venda deve ser um valor numérico válido")

    if cost_price:
        try:
            cost_price_decimal = Decimal(str(cost_price))
            if cost_price_decimal < 0:
                errors.append("Preço de custo não pode ser negativo")
            elif cost_price_decimal > sale_price_decimal:
                errors.append("Preço de custo não pode ser maior que o preço de venda")
        except:
            errors.append("Preço de custo deve ser um valor numérico válido")

    return errors, sku if sku_valid else None

def save_product_image(file):
    """Salvar imagem do produto e retornar o caminho"""
    if file and allowed_file(file.filename):
        # Gerar nome único para o arquivo
        filename = secure_filename(file.filename)
        unique_filename = f"{uuid.uuid4()}_{filename}"

        # Criar diretório se não existir
        upload_dir = os.path.join(current_app.root_path, 'uploads', 'products')
        os.makedirs(upload_dir, exist_ok=True)

        # Salvar arquivo
        file_path = os.path.join(upload_dir, unique_filename)
        file.save(file_path)

        # Retornar URL relativa
        return f"products/{unique_filename}"
    return None

@products_bp.route('/')
@login_required
def index():
    page = request.args.get('page', 1, type=int)
    search = request.args.get('search', '')
    category_id = request.args.get('category_id', type=int)
    
    query = Product.query.filter_by(active=True)
    
    if search:
        query = query.filter(Product.name.ilike(f'%{search}%'))
    
    if category_id:
        query = query.filter_by(category_id=category_id)
    
    products = query.order_by(Product.name).paginate(
        page=page, per_page=20, error_out=False)
    
    categories = Category.query.filter_by(active=True).all()
    
    return render_template('products/index.html', 
                         products=products, 
                         categories=categories,
                         search=search,
                         selected_category=category_id)

@products_bp.route('/new', methods=['GET', 'POST'])
@login_required
def new():
    if request.method == 'POST':
        sku = request.form.get('sku', '').strip()
        name = request.form.get('name', '').strip()
        description = request.form.get('description', '').strip()
        sale_price = request.form.get('sale_price')
        cost_price = request.form.get('cost_price')
        minimum_stock = request.form.get('minimum_stock', 0, type=int)
        unit = request.form.get('unit', 'UN')
        category_id = request.form.get('category_id', type=int)
        supplier_id = request.form.get('supplier_id', type=int)

        # Validações enterprise
        validation_errors, normalized_sku = validate_product_data(sku, name, sale_price, cost_price)

        if validation_errors:
            for error in validation_errors:
                flash(error, 'error')
            return render_template('products/form.html',
                                 categories=Category.query.filter_by(active=True).all(),
                                 suppliers=Supplier.query.filter_by(active=True).all())

        # Usar SKU normalizado
        sku = normalized_sku

        # Check if SKU already exists (case-insensitive)
        existing_product = Product.query.filter(
            db.func.upper(Product.sku) == sku.upper(),
            Product.active == True
        ).first()

        if existing_product:
            flash(f'SKU "{sku}" já existe no produto "{existing_product.name}".', 'error')
            return render_template('products/form.html',
                                 categories=Category.query.filter_by(active=True).all(),
                                 suppliers=Supplier.query.filter_by(active=True).all())
        
        try:
            # Processar upload de imagem
            image_url = None
            if 'image' in request.files:
                image_file = request.files['image']
                if image_file.filename:  # Se um arquivo foi selecionado
                    image_url = save_product_image(image_file)
                    if not image_url:
                        flash('Formato de arquivo inválido. Use PNG, JPG, JPEG, GIF ou WEBP.', 'error')
                        return render_template('products/form.html',
                                             categories=Category.query.filter_by(active=True).all(),
                                             suppliers=Supplier.query.filter_by(active=True).all())
            
            product = Product(
                sku=sku,
                name=name,
                description=description,
                sale_price=Decimal(sale_price),
                cost_price=Decimal(cost_price) if cost_price else None,
                minimum_stock=minimum_stock,
                unit=unit,
                image_url=image_url,
                category_id=category_id if category_id else None,
                supplier_id=supplier_id if supplier_id else None
            )
            
            db.session.add(product)
            db.session.commit()

            flash(f'Produto "{product.name}" (SKU: {product.sku}) cadastrado com sucesso!', 'success')
            return redirect(url_for('products.index'))
        except ValueError:
            flash('Preços devem ser valores numéricos válidos.', 'error')
    
    categories = Category.query.filter_by(active=True).all()
    suppliers = Supplier.query.filter_by(active=True).all()
    
    return render_template('products/form.html', categories=categories, suppliers=suppliers)

@products_bp.route('/<int:id>/edit', methods=['GET', 'POST'])
@login_required
def edit(id):
    product = Product.query.get_or_404(id)
    
    if request.method == 'POST':
        new_sku = request.form.get('sku', '').strip()
        new_name = request.form.get('name', '').strip()
        new_description = request.form.get('description', '').strip()
        sale_price = request.form.get('sale_price')
        cost_price = request.form.get('cost_price')
        new_minimum_stock = request.form.get('minimum_stock', 0, type=int)
        new_unit = request.form.get('unit', 'UN')
        new_category_id = request.form.get('category_id', type=int)
        new_supplier_id = request.form.get('supplier_id', type=int)

        # Validações enterprise
        validation_errors, normalized_sku = validate_product_data(new_sku, new_name, sale_price, cost_price)

        if validation_errors:
            for error in validation_errors:
                flash(error, 'error')
            return render_template('products/form.html',
                                 product=product,
                                 categories=Category.query.filter_by(active=True).all(),
                                 suppliers=Supplier.query.filter_by(active=True).all())

        # Verificar se SKU mudou e se já existe
        if normalized_sku != product.sku.upper():
            existing_product = Product.query.filter(
                db.func.upper(Product.sku) == normalized_sku,
                Product.active == True,
                Product.id != product.id
            ).first()

            if existing_product:
                flash(f'SKU "{normalized_sku}" já existe no produto "{existing_product.name}".', 'error')
                return render_template('products/form.html',
                                     product=product,
                                     categories=Category.query.filter_by(active=True).all(),
                                     suppliers=Supplier.query.filter_by(active=True).all())

        # Aplicar mudanças validadas
        product.sku = normalized_sku
        product.name = new_name
        product.description = new_description
        product.minimum_stock = new_minimum_stock
        product.unit = new_unit
        product.category_id = new_category_id
        product.supplier_id = new_supplier_id
        
        try:
            # Processar upload de nova imagem
            if 'image' in request.files:
                image_file = request.files['image']
                if image_file.filename:  # Se um arquivo foi selecionado
                    new_image_url = save_product_image(image_file)
                    if new_image_url:
                        # Remover imagem antiga se existir
                        if product.image_url:
                            old_image_path = os.path.join(current_app.root_path, 'uploads', product.image_url)
                            if os.path.exists(old_image_path):
                                os.remove(old_image_path)
                        product.image_url = new_image_url
                    else:
                        flash('Formato de arquivo inválido. Use PNG, JPG, JPEG, GIF ou WEBP.', 'error')
                        return render_template('products/form.html', 
                                             product=product,
                                             categories=Category.query.filter_by(active=True).all(),
                                             suppliers=Supplier.query.filter_by(active=True).all())
            
            product.sale_price = Decimal(sale_price)
            product.cost_price = Decimal(cost_price) if cost_price else None

            db.session.commit()
            flash(f'Produto "{product.name}" (SKU: {product.sku}) atualizado com sucesso!', 'success')
            return redirect(url_for('products.index'))
        except ValueError:
            flash('Preços devem ser valores numéricos válidos.', 'error')
    
    categories = Category.query.filter_by(active=True).all()
    suppliers = Supplier.query.filter_by(active=True).all()
    
    return render_template('products/form.html', 
                         product=product, 
                         categories=categories, 
                         suppliers=suppliers)

@products_bp.route('/<int:id>/delete', methods=['POST'])
@login_required
def delete(id):
    product = Product.query.get_or_404(id)
    
    # Check if product has stock movements or orders
    if StockMovement.query.filter_by(product_id=id).first():
        flash(f'Não é possível excluir o produto "{product.name}" pois possui movimentações de estoque registradas.', 'error')
    else:
        product.active = False
        db.session.commit()
        flash(f'Produto "{product.name}" (SKU: {product.sku}) removido com sucesso!', 'success')
    
    return redirect(url_for('products.index'))

@products_bp.route('/categories')
@login_required
def categories():
    categories = Category.query.filter_by(active=True).all()
    return render_template('products/categories.html', categories=categories)

@products_bp.route('/categories/new', methods=['POST'])
@login_required
def new_category():
    name = request.form.get('name')
    description = request.form.get('description')
    
    if not name:
        flash('Nome da categoria é obrigatório.', 'error')
        return redirect(url_for('products.categories'))
    
    category = Category(name=name, description=description)
    db.session.add(category)
    db.session.commit()
    
    flash('Categoria criada com sucesso!', 'success')
    return redirect(url_for('products.categories'))

@products_bp.route('/api/search')
@login_required
def api_search_products():
    """API endpoint para busca de produtos por SKU (para leitores de código de barras)"""
    sku = request.args.get('sku', '').strip().upper()

    if not sku:
        return jsonify({'error': 'SKU é obrigatório'}), 400

    # Buscar produto por SKU exato
    product = Product.query.filter_by(sku=sku, active=True).first()

    if product:
        return jsonify({
            'success': True,
            'product': {
                'id': product.id,
                'sku': product.sku,
                'name': product.name,
                'description': product.description,
                'sale_price': float(product.sale_price),
                'cost_price': float(product.cost_price) if product.cost_price else None,
                'current_stock': product.current_stock,
                'minimum_stock': product.minimum_stock,
                'unit': product.unit,
                'category': product.category.name if product.category else None,
                'supplier': product.supplier.name if product.supplier else None,
                'image_url': product.image_url
            }
        })
    else:
        return jsonify({
            'success': False,
            'error': f'Produto com SKU "{sku}" não encontrado'
        }), 404
