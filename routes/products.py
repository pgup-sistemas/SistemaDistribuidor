from flask import Blueprint, render_template, request, redirect, url_for, flash, current_app
from flask_login import login_required, current_user
from models import Product, Category, Supplier, StockMovement, db
from decimal import Decimal
import os
import uuid
from werkzeug.utils import secure_filename

products_bp = Blueprint('products', __name__)

def allowed_file(filename):
    """Verificar se o arquivo é uma imagem válida"""
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

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
        sku = request.form.get('sku')
        name = request.form.get('name')
        description = request.form.get('description')
        sale_price = request.form.get('sale_price')
        cost_price = request.form.get('cost_price')
        minimum_stock = request.form.get('minimum_stock', 0, type=int)
        unit = request.form.get('unit', 'UN')
        category_id = request.form.get('category_id', type=int)
        supplier_id = request.form.get('supplier_id', type=int)
        
        if not all([sku, name, sale_price]):
            flash('SKU, Nome e Preço de Venda são obrigatórios.', 'error')
            return render_template('products/form.html', 
                                 categories=Category.query.filter_by(active=True).all(),
                                 suppliers=Supplier.query.filter_by(active=True).all())
        
        # Check if SKU already exists
        if Product.query.filter_by(sku=sku, active=True).first():
            flash('SKU já existe.', 'error')
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
            
            flash('Produto cadastrado com sucesso!', 'success')
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
        product.sku = request.form.get('sku')
        product.name = request.form.get('name')
        product.description = request.form.get('description')
        sale_price = request.form.get('sale_price')
        cost_price = request.form.get('cost_price')
        product.minimum_stock = request.form.get('minimum_stock', 0, type=int)
        product.unit = request.form.get('unit', 'UN')
        product.category_id = request.form.get('category_id', type=int) or None
        product.supplier_id = request.form.get('supplier_id', type=int) or None
        
        if not all([product.sku, product.name, sale_price]):
            flash('SKU, Nome e Preço de Venda são obrigatórios.', 'error')
            return render_template('products/form.html', 
                                 product=product,
                                 categories=Category.query.filter_by(active=True).all(),
                                 suppliers=Supplier.query.filter_by(active=True).all())
        
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
            flash('Produto atualizado com sucesso!', 'success')
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
        flash('Não é possível excluir produto com movimentações de estoque.', 'error')
    else:
        product.active = False
        db.session.commit()
        flash('Produto removido com sucesso!', 'success')
    
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
