from app import app, db
from models import User, Category, Supplier, Company, Customer, Product, Order, OrderItem, StockMovement, QuickSale, QuickSaleItem
from werkzeug.security import generate_password_hash
from datetime import datetime, timedelta
import random

def seed_database():
    """Seed the database with initial data"""
    with app.app_context():
        try:
            print("Starting database seeding...")

            # Create default admin user
            admin_email = 'admin@distribuidor.com'
            if not User.query.filter_by(email=admin_email).first():
                admin_user = User(
                    name='Administrador',
                    email=admin_email,
                    password_hash=generate_password_hash('admin123'),
                    role='admin',
                    active=True
                )
                db.session.add(admin_user)
                print("Created default admin user")

            # Create additional users
            additional_users = [
                ('João Atendente', 'joao@distribuidor.com', 'atendente', 'attendant'),
                ('Maria Estoquista', 'maria@distribuidor.com', 'estoque123', 'stock_manager'),
                ('Pedro Entregador', 'pedro@distribuidor.com', 'entrega123', 'delivery'),
                ('Ana Gerente', 'ana@distribuidor.com', 'gerente123', 'manager'),
                ('Carlos Vendas', 'carlos@distribuidor.com', 'vendas123', 'attendant'),
            ]

            for name, email, password, role in additional_users:
                if not User.query.filter_by(email=email).first():
                    user = User(
                        name=name,
                        email=email,
                        password_hash=generate_password_hash(password),
                        role=role,
                        active=True
                    )
                    db.session.add(user)

            print("Created additional users")

            # Create default categories
            default_categories = [
                ('Bebidas', 'Refrigerantes, sucos, águas'),
                ('Alimentos', 'Produtos alimentícios em geral'),
                ('Limpeza', 'Produtos de limpeza e higiene'),
                ('Higiene', 'Produtos de higiene pessoal'),
                ('Padaria', 'Pães, bolos e produtos de padaria'),
                ('Frios', 'Carnes, laticínios e congelados')
            ]

            for name, description in default_categories:
                if not Category.query.filter_by(name=name, active=True).first():
                    category = Category(
                        name=name,
                        description=description,
                        active=True
                    )
                    db.session.add(category)

            print("Created default categories")

            # Create default suppliers
            default_suppliers = [
                ('Fornecedor Padrão 1', 'João Silva', '11999999999', 'joao@fornecedor1.com'),
                ('Fornecedor Padrão 2', 'Maria Santos', '11888888888', 'maria@fornecedor2.com')
            ]

            for name, contact, phone, email in default_suppliers:
                if not Supplier.query.filter_by(name=name, active=True).first():
                    supplier = Supplier(
                        name=name,
                        contact_name=contact,
                        phone=phone,
                        email=email,
                        active=True
                    )
                    db.session.add(supplier)

            print("Created default suppliers")

            # Create test customers
            test_customers = [
                ('Supermercado Central', '12345678000101', '11999999991', 'contato@central.com', 'Rua A, 100', 'Centro', 'São Paulo', 'SP', '01234000'),
                ('Padaria São João', '12345678000102', '11999999992', 'pedidos@saojoao.com', 'Av B, 200', 'Vila Nova', 'São Paulo', 'SP', '01234001'),
                ('Restaurante Sabor', '12345678000103', '11999999993', 'compras@sabor.com', 'Rua C, 300', 'Jardim', 'São Paulo', 'SP', '01234002'),
                ('Minimercado Popular', '12345678000104', '11999999994', 'vendas@popular.com', 'Av D, 400', 'Mooca', 'São Paulo', 'SP', '01234003'),
                ('Bar e Restaurante União', '12345678000105', '11999999995', 'bar@uniao.com', 'Rua E, 500', 'Liberdade', 'São Paulo', 'SP', '01234004'),
                ('Mercearia Família', '12345678000106', '11999999996', 'familia@mercearia.com', 'Av F, 600', 'Tatuapé', 'São Paulo', 'SP', '01234005'),
                ('Cafeteria Express', '12345678000107', '11999999997', 'cafe@express.com', 'Rua G, 700', 'Pinheiros', 'São Paulo', 'SP', '01234006'),
                ('Hotel Comfort', '12345678000108', '11999999998', 'compras@comfort.com', 'Av H, 800', 'Vila Madalena', 'São Paulo', 'SP', '01234007'),
                ('Escola Primária', '12345678000109', '11999999999', 'cantina@escola.com', 'Rua I, 900', 'Vila Mariana', 'São Paulo', 'SP', '01234008'),
                ('Clínica Saúde', '12345678000110', '11888888880', 'compras@clinica.com', 'Av J, 1000', 'Saúde', 'São Paulo', 'SP', '01234009'),
                ('Lanchonete Rápida', '12345678000111', '11888888881', 'lanches@rapida.com', 'Rua K, 1100', 'República', 'São Paulo', 'SP', '01234010'),
                ('Conveniência Noite', '12345678000112', '11888888882', 'noite@conveniencia.com', 'Av L, 1200', 'Sé', 'São Paulo', 'SP', '01234011'),
            ]

            for name, doc, phone, email, address, neighborhood, city, state, zip_code in test_customers:
                if not Customer.query.filter_by(document=doc).first():
                    customer = Customer(
                        name=name,
                        document=doc,
                        phone=phone,
                        email=email,
                        address=address,
                        neighborhood=neighborhood,
                        city=city,
                        state=state,
                        cep=zip_code,
                        active=True
                    )
                    db.session.add(customer)

            db.session.commit()  # Commit customers
            print("Created test customers")

            # Create default company if not exists
            if not Company.query.first():
                company = Company(
                    company_name='Minha Distribuidora Ltda',
                    trade_name='Distribuidora Exemplo',
                    cnpj='12.345.678/0001-90',
                    ie='123.456.789.012',
                    address='Rua das Distribuidoras, 123',
                    address_number='123',
                    neighborhood='Centro',
                    city='São Paulo',
                    state='SP',
                    zip_code='01234-567',
                    phone='1133334444',
                    mobile='11999999999',
                    email='contato@distribuidora.com',
                    website='https://www.distribuidora.com',
                    receipt_header='DISTRIBUIDORA EXEMPLO\nCNPJ: 12.345.678/0001-90\nRua das Distribuidoras, 123 - Centro\nSão Paulo/SP - CEP: 01234-567',
                    receipt_footer='Obrigado pela preferência!\nVolte sempre!',
                    order_notes='Pedido sujeito à confirmação de estoque.\nPrazo de entrega: 2-3 dias úteis.',
                    active=True
                )
                db.session.add(company)
                print("Created default company")
    
                # Create test products
                categories = Category.query.filter_by(active=True).all()
                suppliers = Supplier.query.filter_by(active=True).all()
    
                if categories and suppliers:
                    test_products = [
                        # Bebidas
                        ('Coca-Cola 2L', 'Refrigerante Coca-Cola 2 litros', 8.50, 6.00, 100, 10, 'UN', categories[0].id, suppliers[0].id),
                        ('Fanta Laranja 2L', 'Refrigerante Fanta Laranja 2 litros', 7.50, 5.50, 80, 8, 'UN', categories[0].id, suppliers[0].id),
                        ('Suco de Laranja 1L', 'Suco natural de laranja 1 litro', 6.00, 4.00, 60, 6, 'UN', categories[0].id, suppliers[1].id),
                        ('Água Mineral 500ml', 'Água mineral sem gás 500ml', 2.50, 1.50, 200, 20, 'UN', categories[0].id, suppliers[1].id),
    
                        # Alimentos
                        ('Arroz Branco 5kg', 'Arroz branco tipo 1, 5kg', 25.00, 18.00, 50, 5, 'KG', categories[1].id, suppliers[0].id),
                        ('Feijão Carioca 2kg', 'Feijão carioca 2kg', 12.00, 8.50, 40, 4, 'KG', categories[1].id, suppliers[0].id),
                        ('Macarrão Espaguete', 'Macarrão espaguete 500g', 4.50, 3.00, 100, 10, 'UN', categories[1].id, suppliers[1].id),
                        ('Óleo de Soja 900ml', 'Óleo de soja 900ml', 8.00, 5.50, 70, 7, 'UN', categories[1].id, suppliers[1].id),
    
                        # Limpeza
                        ('Detergente 500ml', 'Detergente líquido neutro 500ml', 3.50, 2.00, 120, 12, 'UN', categories[2].id, suppliers[0].id),
                        ('Sabão em Pó 1kg', 'Sabão em pó para roupas 1kg', 15.00, 10.00, 60, 6, 'KG', categories[2].id, suppliers[0].id),
                        ('Desinfetante 1L', 'Desinfetante multiuso 1 litro', 7.00, 4.50, 80, 8, 'UN', categories[2].id, suppliers[1].id),
    
                        # Higiene
                        ('Shampoo 350ml', 'Shampoo para cabelos normais 350ml', 12.00, 8.00, 90, 9, 'UN', categories[3].id, suppliers[1].id),
                        ('Creme Dental 90g', 'Creme dental menta 90g', 5.50, 3.50, 150, 15, 'UN', categories[3].id, suppliers[1].id),
                        ('Sabonete 85g', 'Sabonete em barra 85g', 2.00, 1.20, 200, 20, 'UN', categories[3].id, suppliers[0].id),
    
                        # Padaria
                        ('Pão Francês', 'Pão francês fresco (unidade)', 0.80, 0.50, 300, 30, 'UN', categories[4].id, suppliers[0].id),
                        ('Bolo de Chocolate', 'Bolo de chocolate 1kg', 35.00, 25.00, 20, 2, 'KG', categories[4].id, suppliers[1].id),
    
                        # Frios
                        ('Queijo Mussarela 1kg', 'Queijo mussarela fatiado 1kg', 45.00, 32.00, 25, 3, 'KG', categories[5].id, suppliers[1].id),
                        ('Presunto 500g', 'Presunto fatiado 500g', 28.00, 20.00, 40, 4, 'UN', categories[5].id, suppliers[0].id),
                        ('Manteiga 200g', 'Manteiga com sal 200g', 8.50, 6.00, 60, 6, 'UN', categories[5].id, suppliers[1].id),
                    ]
    
                    for sku, name, sale_price, cost_price, stock, min_stock, unit, cat_id, sup_id in test_products:
                        if not Product.query.filter_by(sku=sku).first():
                            product = Product(
                                sku=sku,
                                name=name,
                                description=name,
                                sale_price=sale_price,
                                cost_price=cost_price,
                                current_stock=stock,
                                minimum_stock=min_stock,
                                unit=unit,
                                category_id=cat_id,
                                supplier_id=sup_id,
                                active=True
                            )
                            db.session.add(product)
    
                    print("Created test products")
    
                    # Create test orders and order items
                    customers = Customer.query.filter_by(active=True).all()
                    products = Product.query.filter_by(active=True).all()
                    users = User.query.filter_by(active=True).all()
    
                    if customers and products and users:
                        # Create orders over the last 60 days
                        base_date = datetime.utcnow() - timedelta(days=60)
    
                        for i in range(25):  # Create 25 orders
                            order_date = base_date + timedelta(days=random.randint(0, 60))
                            customer = random.choice(customers)
                            user = random.choice([u for u in users if u.role in ['admin', 'attendant']])
    
                            # Create order
                            payment_methods = ['cash', 'card', 'pix', 'bank_slip']
                            statuses = ['confirmed', 'delivered', 'confirmed', 'delivered', 'confirmed']  # More confirmed/delivered
    
                            order = Order(
                                customer_id=customer.id,
                                user_id=user.id,
                                payment_method=random.choice(payment_methods),
                                status=random.choice(statuses),
                                created_at=order_date
                            )
                            db.session.add(order)
                            db.session.flush()  # Get order ID
    
                            # Add 2-5 random items to each order
                            num_items = random.randint(2, 5)
                            selected_products = random.sample(products, num_items)
                            total = 0
    
                            for product in selected_products:
                                quantity = random.randint(1, 5)
                                unit_price = product.sale_price
                                total += quantity * unit_price
    
                                order_item = OrderItem(
                                    order_id=order.id,
                                    product_id=product.id,
                                    quantity=quantity,
                                    unit_price=unit_price
                                )
                                db.session.add(order_item)
    
                                # Update product stock
                                product.current_stock -= quantity
    
                            order.total = total
                            db.session.add(order)
    
                        print("Created test orders and order items")
    
                        # Create stock movements
                        for product in products:
                            # Add some entry movements
                            for _ in range(random.randint(1, 3)):
                                entry_date = base_date + timedelta(days=random.randint(0, 60))
                                quantity = random.randint(10, 50)
                                stock_movement = StockMovement(
                                    product_id=product.id,
                                    movement_type='entry',
                                    quantity=quantity,
                                    reason='Compra de fornecedor',
                                    user_id=random.choice(users).id,
                                    created_at=entry_date
                                )
                                db.session.add(stock_movement)
                                product.current_stock += quantity
    
                            # Add some exit movements (adjustments)
                            for _ in range(random.randint(0, 2)):
                                exit_date = base_date + timedelta(days=random.randint(0, 60))
                                quantity = random.randint(1, 10)
                                stock_movement = StockMovement(
                                    product_id=product.id,
                                    movement_type='exit',
                                    quantity=quantity,
                                    reason='Ajuste de inventário',
                                    user_id=random.choice(users).id,
                                    created_at=exit_date
                                )
                                db.session.add(stock_movement)
                                product.current_stock -= quantity
    
                        print("Created stock movements")
    
                        # Create quick sales
                        for i in range(15):  # Create 15 quick sales
                            sale_date = base_date + timedelta(days=random.randint(0, 60))
                            user = random.choice([u for u in users if u.role in ['admin', 'attendant']])
    
                            payment_methods = ['cash', 'card', 'pix']
                            sale = QuickSale(
                                total=0,  # Will be calculated
                                payment_method=random.choice(payment_methods),
                                status='completed',
                                created_at=sale_date,
                                user_id=user.id
                            )
                            db.session.add(sale)
                            db.session.flush()
    
                            # Add 1-3 items to quick sale
                            num_items = random.randint(1, 3)
                            selected_products = random.sample(products, num_items)
                            total = 0
    
                            for product in selected_products:
                                quantity = random.randint(1, 3)
                                unit_price = product.sale_price
                                total += quantity * unit_price
    
                                quick_item = QuickSaleItem(
                                    quick_sale_id=sale.id,
                                    product_id=product.id,
                                    product_name=product.name,
                                    product_sku=product.sku,
                                    quantity=quantity,
                                    unit_price=unit_price,
                                    total=quantity * unit_price
                                )
                                db.session.add(quick_item)
    
                                # Update product stock
                                product.current_stock -= quantity
    
                            sale.total = total
                            db.session.add(sale)
    
                        print("Created quick sales")
    
                db.session.commit()
                print("Database seeding completed successfully!")

        except Exception as e:
            db.session.rollback()
            print(f"Error during seeding: {e}")
            raise

if __name__ == '__main__':
    seed_database()