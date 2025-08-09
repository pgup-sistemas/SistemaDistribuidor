import os
import json
import zipfile
import shutil
from datetime import datetime
from models import db, User, Customer, Product, Category, Supplier, Order, OrderItem, StockMovement, Delivery, AuditLog

class BackupService:
    def __init__(self):
        self.backup_dir = 'backups'
        self.ensure_backup_dir()
    
    def ensure_backup_dir(self):
        """Ensure backup directory exists"""
        if not os.path.exists(self.backup_dir):
            os.makedirs(self.backup_dir)
    
    def create_backup(self):
        """Create a complete database backup"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_filename = f'backup_{timestamp}.zip'
        backup_path = os.path.join(self.backup_dir, backup_filename)
        
        # Create temporary directory for backup files
        temp_dir = f'temp_backup_{timestamp}'
        os.makedirs(temp_dir, exist_ok=True)
        
        try:
            # Export all tables to JSON
            self._export_table_to_json(User, os.path.join(temp_dir, 'users.json'))
            self._export_table_to_json(Customer, os.path.join(temp_dir, 'customers.json'))
            self._export_table_to_json(Category, os.path.join(temp_dir, 'categories.json'))
            self._export_table_to_json(Supplier, os.path.join(temp_dir, 'suppliers.json'))
            self._export_table_to_json(Product, os.path.join(temp_dir, 'products.json'))
            self._export_table_to_json(Order, os.path.join(temp_dir, 'orders.json'))
            self._export_table_to_json(OrderItem, os.path.join(temp_dir, 'order_items.json'))
            self._export_table_to_json(StockMovement, os.path.join(temp_dir, 'stock_movements.json'))
            self._export_table_to_json(Delivery, os.path.join(temp_dir, 'deliveries.json'))
            self._export_table_to_json(AuditLog, os.path.join(temp_dir, 'audit_logs.json'))
            
            # Create backup info file
            backup_info = {
                'timestamp': timestamp,
                'version': '1.0',
                'tables': [
                    'users', 'customers', 'categories', 'suppliers', 'products',
                    'orders', 'order_items', 'stock_movements', 'deliveries', 'audit_logs'
                ]
            }
            
            with open(os.path.join(temp_dir, 'backup_info.json'), 'w', encoding='utf-8') as f:
                json.dump(backup_info, f, ensure_ascii=False, indent=2)
            
            # Create ZIP file
            with zipfile.ZipFile(backup_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                for root, dirs, files in os.walk(temp_dir):
                    for file in files:
                        file_path = os.path.join(root, file)
                        arcname = os.path.relpath(file_path, temp_dir)
                        zipf.write(file_path, arcname)
            
            return backup_filename
            
        finally:
            # Clean up temporary directory
            if os.path.exists(temp_dir):
                shutil.rmtree(temp_dir)
    
    def _export_table_to_json(self, model, filepath):
        """Export a table to JSON file"""
        records = []
        
        for record in model.query.all():
            record_dict = {}
            for column in model.__table__.columns:
                value = getattr(record, column.name)
                if isinstance(value, datetime):
                    value = value.isoformat()
                elif hasattr(value, '__str__'):
                    value = str(value)
                record_dict[column.name] = value
            records.append(record_dict)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(records, f, ensure_ascii=False, indent=2)
    
    def list_backups(self):
        """List all available backups"""
        backups = []
        
        if not os.path.exists(self.backup_dir):
            return backups
        
        for filename in os.listdir(self.backup_dir):
            if filename.startswith('backup_') and filename.endswith('.zip'):
                filepath = os.path.join(self.backup_dir, filename)
                stat = os.stat(filepath)
                
                # Extract timestamp from filename
                timestamp_str = filename.replace('backup_', '').replace('.zip', '')
                try:
                    timestamp = datetime.strptime(timestamp_str, '%Y%m%d_%H%M%S')
                    formatted_date = timestamp.strftime('%d/%m/%Y %H:%M:%S')
                except ValueError:
                    formatted_date = 'Data inválida'
                
                backups.append({
                    'filename': filename,
                    'size': self._format_file_size(stat.st_size),
                    'date': formatted_date,
                    'timestamp': timestamp if 'timestamp' in locals() else None
                })
        
        # Sort by timestamp (newest first)
        backups.sort(key=lambda x: x['timestamp'] or datetime.min, reverse=True)
        
        return backups
    
    def get_backup_path(self, filename):
        """Get full path to backup file"""
        return os.path.join(self.backup_dir, filename)
    
    def _format_file_size(self, size_bytes):
        """Format file size in human readable format"""
        if size_bytes < 1024:
            return f"{size_bytes} B"
        elif size_bytes < 1024 * 1024:
            return f"{size_bytes / 1024:.1f} KB"
        else:
            return f"{size_bytes / (1024 * 1024):.1f} MB"
