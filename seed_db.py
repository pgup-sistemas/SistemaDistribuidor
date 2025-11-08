from app import app, db
from models import User, Category, Supplier, Company, Customer, Product, Order, OrderItem, StockMovement, QuickSale, QuickSaleItem
from werkzeug.security import generate_password_hash
from datetime import datetime, timedelta
import random

def seed_database():
    """Seed the database with comprehensive test data"""
    with app.app_context():
        try:
            print("Starting database seeding...")

            # Get all existing users or create them
            users_data = [
                ('Administrador', 'admin@distribuidor.com', 'admin123', 'admin'),
                ('João Atendente', 'joao@distribuidor.com', 'atendente', 'attendant'),
                ('Maria Estoquista', 'maria@distribuidor.com', 'estoque123', 'stock_manager'),
                ('Pedro Entregador', 'pedro@distribuidor.com', 'entrega123', 'delivery'),
                ('Ana Gerente', 'ana@distribuidor.com', 'gerente123', 'manager'),
                ('Carlos Vendas', 'carlos@distribuidor.com', 'vendas123', 'attendant'),
            ]

            for name, email, password, role in users_data:
                if not User.query.filter_by(email=email).first():
                    user = User(
                        name=name,
                        email=email,
                        password_hash=generate_password_hash(password),
                        role=role,
                        active=True
                    )
                    db.session.add(user)

            db.session.commit()

            # Get all users (existing + newly created)
            users = User.query.filter_by(active=True).all()
            print(f"Total users available: {len(users)}")

            # Get or create categories
            categories_data = [
                ('Bebidas', 'Refrigerantes, sucos, águas'),
                ('Alimentos', 'Produtos alimentícios em geral'),
                ('Limpeza', 'Produtos de limpeza e higiene'),
                ('Higiene', 'Produtos de higiene pessoal'),
                ('Padaria', 'Pães, bolos e produtos de padaria'),
                ('Frios', 'Carnes, laticínios e congelados')
            ]

            categories = []
            for name, description in categories_data:
                category = Category.query.filter_by(name=name).first()
                if not category:
                    category = Category(name=name, description=description, active=True)
                    db.session.add(category)
                    db.session.commit()
                categories.append(category)

            print(f"Ensured {len(categories)} categories exist")

            # Get or create suppliers
            suppliers_data = [
                ('Fornecedor Padrão 1', 'João Silva', '11999999999', 'joao@fornecedor1.com'),
                ('Fornecedor Padrão 2', 'Maria Santos', '11888888888', 'maria@fornecedor2.com')
            ]

            suppliers = []
            for name, contact, phone, email in suppliers_data:
                supplier = Supplier.query.filter_by(name=name).first()
                if not supplier:
                    supplier = Supplier(
                        name=name, contact_name=contact, phone=phone, email=email, active=True
                    )
                    db.session.add(supplier)
                    db.session.commit()
                suppliers.append(supplier)

            print(f"Ensured {len(suppliers)} suppliers exist")

            # Get all existing customers or create them
            customers_data = [
                ('Supermercado Central', '12345678000101', '11999999991', 'contato@central.com'),
                ('Padaria São João', '12345678000102', '11999999992', 'pedidos@saojoao.com'),
                ('Restaurante Sabor', '12345678000103', '11999999993', 'compras@sabor.com'),
                ('Minimercado Popular', '12345678000104', '11999999994', 'vendas@popular.com'),
                ('Bar e Restaurante União', '12345678000105', '11999999995', 'bar@uniao.com'),
                ('Mercearia Família', '12345678000106', '11999999996', 'familia@mercearia.com'),
                ('Cafeteria Express', '12345678000107', '11999999997', 'cafe@express.com'),
                ('Hotel Comfort', '12345678000108', '11999999998', 'compras@comfort.com'),
                ('Escola Primária', '12345678000109', '11999999999', 'cantina@escola.com'),
                ('Clínica Saúde', '12345678000110', '11888888880', 'compras@clinica.com'),
                ('Lanchonete Rápida', '12345678000111', '11888888881', 'lanches@rapida.com'),
                ('Conveniência Noite', '12345678000112', '11888888882', 'noite@conveniencia.com'),
            ]

            for name, doc, phone, email in customers_data:
                if not Customer.query.filter_by(document=doc).first():
                    customer = Customer(
                        name=name, document=doc, phone=phone, email=email,
                        address='Rua Exemplo, 123', neighborhood='Centro',
                        city='São Paulo', state='SP', cep='01234000', active=True
                    )
                    db.session.add(customer)

            db.session.commit()

            # Get all customers (existing + newly created)
            customers = Customer.query.filter_by(active=True).all()
            print(f"Total customers available: {len(customers)}")

            # Create products (18 products) with numeric SKUs
            products_data = [
                # Bebidas (4)
                ('Coca-Cola 2L', 8.50, 6.00, 100, 10, categories[0], suppliers[0]),
                ('Fanta Laranja 2L', 7.50, 5.50, 80, 8, categories[0], suppliers[0]),
                ('Suco de Laranja 1L', 6.00, 4.00, 60, 6, categories[0], suppliers[1]),
                ('Água Mineral 500ml', 2.50, 1.50, 200, 20, categories[0], suppliers[1]),
                # Alimentos (4)
                ('Arroz Branco 5kg', 25.00, 18.00, 50, 5, categories[1], suppliers[0]),
                ('Feijão Carioca 2kg', 12.00, 8.50, 40, 4, categories[1], suppliers[0]),
                ('Macarrão Espaguete', 4.50, 3.00, 100, 10, categories[1], suppliers[1]),
                ('Óleo de Soja 900ml', 8.00, 5.50, 70, 7, categories[1], suppliers[1]),
                # Limpeza (3)
                ('Detergente 500ml', 3.50, 2.00, 120, 12, categories[2], suppliers[0]),
                ('Sabão em Pó 1kg', 15.00, 10.00, 60, 6, categories[2], suppliers[0]),
                ('Desinfetante 1L', 7.00, 4.50, 80, 8, categories[2], suppliers[1]),
                # Higiene (3)
                ('Shampoo 350ml', 12.00, 8.00, 90, 9, categories[3], suppliers[1]),
                ('Creme Dental 90g', 5.50, 3.50, 150, 15, categories[3], suppliers[1]),
                ('Sabonete 85g', 2.00, 1.20, 200, 20, categories[3], suppliers[0]),
                # Padaria (2)
                ('Pão Francês', 0.80, 0.50, 300, 30, categories[4], suppliers[0]),
                ('Bolo de Chocolate', 35.00, 25.00, 20, 2, categories[4], suppliers[1]),
                # Frios (2)
                ('Queijo Mussarela 1kg', 45.00, 32.00, 25, 3, categories[5], suppliers[1]),
                ('Presunto 500g', 28.00, 20.00, 40, 4, categories[5], suppliers[0]),
            ]

            products = []
            # Get the highest existing numeric SKU
            existing_skus = [int(p.sku) for p in Product.query.all() if p.sku and p.sku.isdigit()]
            next_sku = max(existing_skus or [0]) + 1

            for name, sale_price, cost_price, stock, min_stock, category, supplier in products_data:
                sku = f"{next_sku:04d}"  # SKU numérico sequencial com 4 dígitos
                if not Product.query.filter_by(sku=sku).first():
                    product = Product(
                        sku=sku, name=name, description=name,
                        sale_price=sale_price, cost_price=cost_price,
                        current_stock=stock, minimum_stock=min_stock,
                        unit='UN', category_id=category.id, supplier_id=supplier.id, active=True
                    )
                    db.session.add(product)
                    products.append(product)
                    next_sku += 1

            db.session.commit()
            print(f"Created {len(products)} products")

            # Get all products (existing + newly created)
            products = Product.query.filter_by(active=True).all()
            print(f"Total products available: {len(products)}")

            # Create orders (25 orders)
            base_date = datetime.utcnow() - timedelta(days=60)
            orders = []

            for i in range(25):
                order_date = base_date + timedelta(days=random.randint(0, 60))
                customer = random.choice(customers)
                user = random.choice([u for u in users if u.role in ['admin', 'attendant']])

                payment_methods = ['cash', 'card', 'pix', 'bank_slip']
                statuses = ['confirmed', 'delivered']

                # First calculate total from items
                num_items = random.randint(2, 5)
                selected_products = random.sample(products, min(num_items, len(products)))
                total = 0

                for product in selected_products:
                    quantity = random.randint(1, 5)
                    total += quantity * product.sale_price

                # Create order with calculated total
                order = Order(
                    customer_id=customer.id, user_id=user.id,
                    payment_method=random.choice(payment_methods),
                    status=random.choice(statuses), created_at=order_date,
                    total=total
                )
                db.session.add(order)
                db.session.flush()

                # Add items
                for product in selected_products:
                    quantity = random.randint(1, 5)
                    unit_price = product.sale_price

                    order_item = OrderItem(
                        order_id=order.id, product_id=product.id,
                        quantity=quantity, unit_price=unit_price
                    )
                    db.session.add(order_item)

                    # Update product stock
                    product.current_stock -= quantity

                orders.append(order)

            db.session.commit()
            print(f"Created {len(orders)} orders")

            # Create quick sales (15 sales)
            quick_sales = []
            for i in range(15):
                sale_date = base_date + timedelta(days=random.randint(0, 60))
                user = random.choice([u for u in users if u.role in ['admin', 'attendant']])

                # First calculate total from items
                num_items = random.randint(1, 3)
                selected_products = random.sample(products, min(num_items, len(products)))
                total = 0

                for product in selected_products:
                    quantity = random.randint(1, 3)
                    total += quantity * product.sale_price

                # Create sale with temporary sale_number first
                temp_sale_number = f"TEMP_{i}_{int(datetime.utcnow().timestamp())}"
                sale = QuickSale(
                    sale_number=temp_sale_number,  # Temporary unique value
                    payment_method=random.choice(['cash', 'card', 'pix']),
                    status='completed', created_at=sale_date, user_id=user.id,
                    total=total
                )
                db.session.add(sale)
                db.session.commit()  # Commit to get ID

                # Now update with proper sale number
                sale.sale_number = sale.generate_sale_number()
                db.session.commit()

                # Add items
                for product in selected_products:
                    quantity = random.randint(1, 3)
                    unit_price = product.sale_price

                    quick_item = QuickSaleItem(
                        quick_sale_id=sale.id, product_id=product.id,
                        product_name=product.name, product_sku=product.sku,
                        quantity=quantity, unit_price=unit_price, total=quantity * unit_price
                    )
                    db.session.add(quick_item)
                    product.current_stock -= quantity

                quick_sales.append(sale)

            db.session.commit()
            print(f"Created {len(quick_sales)} quick sales")

            # Create company
            if not Company.query.first():
                company = Company(
                    company_name='Minha Distribuidora Ltda',
                    trade_name='Distribuidora Exemplo',
                    cnpj='12.345.678/0001-90',
                    address='Rua das Distribuidoras, 123',
                    city='São Paulo', state='SP',
                    phone='1133334444', email='contato@distribuidora.com',
                    active=True
                )
                db.session.add(company)
                db.session.commit()
                print("Created company")

            print("Database seeding completed successfully!")

        except Exception as e:
            db.session.rollback()
            print(f"Error during seeding: {e}")
            raise

if __name__ == '__main__':
    seed_database()