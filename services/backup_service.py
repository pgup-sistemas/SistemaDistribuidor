import os
import json
import zipfile
import shutil
import logging
from datetime import datetime
from pathlib import Path
from flask import current_app
from models import User, Customer, Product, Category, Supplier, Order, OrderItem, StockMovement, Delivery, AuditLog

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/backup.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class BackupService:
    def __init__(self):
        self.backup_dir = Path('backups')
        self.backup_dir.mkdir(exist_ok=True)

        # Retention settings
        self.retention_days = int(os.environ.get('BACKUP_RETENTION_DAYS', '30'))

        # Directories to backup
        self.backup_dirs = [
            'instance',  # Database files
            'uploads',   # Uploaded files
            'logs',      # Application logs
        ]

    def create_backup(self):
        """Create a complete system backup"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_filename = f'backup_{timestamp}.zip'
        backup_path = self.backup_dir / backup_filename

        # Create temporary directory for backup files
        temp_dir = Path(f'temp_backup_{timestamp}')
        temp_dir.mkdir(exist_ok=True)

        try:
            logger.info(f"Starting backup creation: {backup_filename}")

            # Export all database tables to JSON
            tables_exported = self._export_all_tables_to_json(temp_dir)

            # Backup system files and directories
            files_backed_up = self._backup_system_files(temp_dir)

            # Create backup info file
            backup_info = {
                'timestamp': timestamp,
                'version': '2.0',
                'created_at': datetime.now().isoformat(),
                'tables': tables_exported,
                'files_backed_up': files_backed_up,
                'system_info': {
                    'python_version': os.sys.version,
                    'platform': os.sys.platform,
                    'backup_service_version': '2.0'
                }
            }

            with open(temp_dir / 'backup_info.json', 'w', encoding='utf-8') as f:
                json.dump(backup_info, f, ensure_ascii=False, indent=2)

            # Create ZIP file
            with zipfile.ZipFile(backup_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                for root, dirs, files in os.walk(temp_dir):
                    for file in files:
                        file_path = Path(root) / file
                        arcname = file_path.relative_to(temp_dir)
                        zipf.write(file_path, arcname)

            # Verify backup was created and has content
            if backup_path.exists() and backup_path.stat().st_size > 0:
                logger.info(f"Backup created successfully: {backup_path} ({backup_path.stat().st_size} bytes)")
                return backup_filename
            else:
                logger.error(f"Backup file was not created or is empty: {backup_path}")
                return None

        except Exception as e:
            logger.error(f"Error creating backup: {str(e)}")
            raise
        finally:
            # Clean up temporary directory
            if temp_dir.exists():
                shutil.rmtree(temp_dir)

            # Clean up old backups
            self._cleanup_old_backups()
    
    def _export_all_tables_to_json(self, temp_dir):
        """Export all database tables to JSON files"""
        tables = [
            ('users', User),
            ('customers', Customer),
            ('categories', Category),
            ('suppliers', Supplier),
            ('products', Product),
            ('orders', Order),
            ('order_items', OrderItem),
            ('stock_movements', StockMovement),
            ('deliveries', Delivery),
            ('audit_logs', AuditLog)
        ]

        exported_tables = []

        # Ensure we have application context
        app_context = None
        if not current_app:
            from app import create_app
            app = create_app()
            app_context = app.app_context()
            app_context.push()
            logger.info("Created new application context for backup")
        else:
            logger.info("Using existing application context for backup")

        try:
            for table_name, model in tables:
                filepath = temp_dir / f'{table_name}.json'
                try:
                    records = []
                    query_result = model.query.all()

                    if not query_result:
                        logger.warning(f"No records found in table: {table_name}")
                        # Create empty JSON array for empty tables
                        records = []

                    for record in query_result:
                        record_dict = {}
                        for column in model.__table__.columns:
                            value = getattr(record, column.name)
                            if isinstance(value, datetime):
                                value = value.isoformat()
                            elif hasattr(value, '__str__'):
                                value = str(value)
                            else:
                                value = None
                            record_dict[column.name] = value
                        records.append(record_dict)

                    with open(filepath, 'w', encoding='utf-8') as f:
                        json.dump(records, f, ensure_ascii=False, indent=2)

                    # Verify file was created and has content
                    if filepath.exists() and filepath.stat().st_size > 0:
                        exported_tables.append(table_name)
                        logger.info(f"Exported {len(records)} records from {table_name}")
                    else:
                        logger.warning(f"Table {table_name} export resulted in empty file")

                except Exception as e:
                    logger.error(f"Error exporting table {table_name}: {str(e)}")
                    # Create empty JSON array as fallback
                    with open(filepath, 'w', encoding='utf-8') as f:
                        json.dump([], f, ensure_ascii=False, indent=2)

        finally:
            if app_context:
                app_context.pop()

        return exported_tables

    def _backup_system_files(self, temp_dir):
        """Backup system files and directories"""
        backed_up_files = []

        for item in self.backup_dirs:
            item_path = Path(item)
            if item_path.exists():
                try:
                    if item_path.is_file():
                        # Copy single file
                        dest_path = temp_dir / item_path.name
                        shutil.copy2(item_path, dest_path)
                        backed_up_files.append(str(item_path))
                        logger.info(f"Backed up file: {item_path}")
                    elif item_path.is_dir():
                        # Copy directory
                        dest_path = temp_dir / item_path.name
                        shutil.copytree(item_path, dest_path, dirs_exist_ok=True)
                        backed_up_files.append(str(item_path))
                        logger.info(f"Backed up directory: {item_path}")
                except Exception as e:
                    logger.error(f"Error backing up {item_path}: {str(e)}")

        return backed_up_files

    def _cleanup_old_backups(self):
        """Remove backups older than retention period"""
        try:
            cutoff_date = datetime.now().timestamp() - (self.retention_days * 24 * 60 * 60)

            removed_count = 0
            for backup_file in self.backup_dir.glob('*.zip'):
                if backup_file.stat().st_mtime < cutoff_date:
                    backup_file.unlink()
                    removed_count += 1
                    logger.info(f"Removed old backup: {backup_file}")

            if removed_count > 0:
                logger.info(f"Cleaned up {removed_count} old backup files")

        except Exception as e:
            logger.error(f"Cleanup error: {e}")

    def list_backups(self):
        """List all available backups"""
        backups = []

        if not self.backup_dir.exists():
            return backups

        for backup_file in self.backup_dir.glob('backup_*.zip'):
            stat = backup_file.stat()

            # Extract timestamp from filename
            filename = backup_file.name
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
                'timestamp': timestamp
            })

        # Sort by timestamp (newest first)
        backups.sort(key=lambda x: x['timestamp'], reverse=True)

        return backups

    def get_backup_path(self, filename):
        """Get full path to backup file"""
        return self.backup_dir / filename

    def _format_file_size(self, size_bytes):
        """Format file size in human readable format"""
        if size_bytes < 1024:
            return f"{size_bytes} B"
        elif size_bytes < 1024 * 1024:
            return f"{size_bytes / 1024:.1f} KB"
        else:
            return f"{size_bytes / (1024 * 1024):.1f} MB"
