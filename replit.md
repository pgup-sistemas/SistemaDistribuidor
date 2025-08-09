# Overview

This is a comprehensive web-based distributor management system designed for small and medium beverage, water, gas, pet food, and delivery distributors. The system is built with Flask as the backend framework and provides complete business management functionality including customer management, product catalog, inventory control, order processing, and reporting. It features WhatsApp integration for order sharing, thermal receipt printing, and role-based user access control.

# User Preferences

Preferred communication style: Simple, everyday language.

# System Architecture

## Backend Framework
- **Flask**: Main web framework with modular blueprint architecture
- **SQLAlchemy**: ORM for database operations with declarative base model
- **Flask-Login**: User session management and authentication
- **PostgreSQL**: Primary database for data persistence

## Application Structure
- **Modular Blueprint Design**: Organized into functional modules (auth, dashboard, customers, products, orders, stock, reports, backup, users)
- **Model-View-Controller Pattern**: Clear separation between data models, business logic, and presentation
- **Service Layer Architecture**: Dedicated services for WhatsApp integration, printing, and backup operations

## Authentication & Authorization
- **Role-Based Access Control**: Five distinct user roles (admin, attendant, stock_manager, delivery, manager)
- **Session Management**: Secure login/logout with remember-me functionality
- **Permission-Based Views**: Route-level access control based on user roles

## Database Design
- **Normalized Schema**: Separate entities for Users, Customers, Products, Categories, Suppliers, Orders, OrderItems, StockMovements, Deliveries, and AuditLog
- **Relationship Management**: Proper foreign key relationships with cascade handling
- **Audit Trail**: Complete tracking of all stock movements and system changes

## Frontend Architecture
- **Server-Side Rendering**: Flask templates with Jinja2 templating engine
- **Bootstrap 5**: Responsive UI framework with dark theme support
- **Progressive Enhancement**: JavaScript for dynamic interactions while maintaining functionality without JS
- **Component-Based Templates**: Reusable template blocks with inheritance hierarchy

## Business Logic Components
- **Order Management**: Complete order lifecycle from creation to delivery with multiple payment methods
- **Inventory Control**: Real-time stock tracking with automatic alerts for low stock
- **Reporting Engine**: Comprehensive sales, product, and customer analytics
- **Print System**: Thermal receipt generation with PDF export capabilities

## Data Management
- **Backup System**: Automated database backup with JSON export/import functionality
- **Pagination**: Efficient data loading with configurable page sizes
- **Search & Filtering**: Full-text search capabilities across all major entities

# External Dependencies

## Core Framework Dependencies
- **Flask**: Web application framework
- **SQLAlchemy & Flask-SQLAlchemy**: Database ORM and Flask integration
- **Flask-Login**: User authentication and session management
- **Werkzeug**: WSGI utilities and security helpers
- **WeasyPrint**: PDF generation for receipts and reports

## Frontend Assets
- **Bootstrap 5**: CSS framework via CDN with dark theme support
- **Font Awesome 6**: Icon library for UI elements
- **Custom CSS**: Application-specific styling

## Database
- **PostgreSQL**: Primary database system
- **Connection Pooling**: Configured with pool recycling and pre-ping for reliability

## Integration Services
- **WhatsApp Web API**: Direct linking for order sharing via URL scheme
- **Thermal Printer Support**: CSS-based receipt formatting for 80mm thermal printers

## JavaScript Libraries
- **Chart.js**: Dashboard analytics and reporting visualizations
- **Date Formatting**: Moment.js for date/time handling
- **Currency Formatting**: Intl.NumberFormat for Brazilian Real formatting

## Development & Deployment
- **Python 3.x**: Runtime environment
- **Environment Variables**: Configuration via DATABASE_URL and SESSION_SECRET
- **Static File Serving**: Flask's built-in static file handler
- **WSGI Middleware**: ProxyFix for proper header handling in production