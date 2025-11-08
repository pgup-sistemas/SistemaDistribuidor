#!/usr/bin/env python3
"""
Sistema de Backup Automático - Sistema Distribuidor
Executa backups do banco de dados e arquivos periodicamente
"""

import os
import subprocess
import shutil
from datetime import datetime
from pathlib import Path
import logging
import gzip
import json

# Configuração de logging
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

        # Configurações do backup
        self.db_url = os.environ.get('DATABASE_URL', 'sqlite:///instance/distributor_system.db')
        self.retention_days = int(os.environ.get('BACKUP_RETENTION_DAYS', '30'))

        # Diretórios para backup
        self.backup_dirs = [
            'instance',  # Banco SQLite
            'uploads',   # Arquivos enviados
            'logs',      # Logs da aplicação
        ]

    def create_database_backup(self):
        """Cria backup do banco de dados"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_filename = f"db_backup_{timestamp}"

        try:
            if self.db_url.startswith('sqlite'):
                # Backup SQLite
                db_path = self.db_url.replace('sqlite:///', '')
                if os.path.exists(db_path):
                    backup_path = self.backup_dir / f"{backup_filename}.db"
                    shutil.copy2(db_path, backup_path)
                    logger.info(f"SQLite backup created: {backup_path}")

                    # Comprimir
                    with open(backup_path, 'rb') as f_in:
                        with gzip.open(f"{backup_path}.gz", 'wb') as f_out:
                            shutil.copyfileobj(f_in, f_out)
                    os.remove(backup_path)  # Remover arquivo não comprimido
                    return f"{backup_path}.gz"

            elif 'postgresql' in self.db_url:
                # Backup PostgreSQL
                backup_path = self.backup_dir / f"{backup_filename}.sql"
                cmd = [
                    'pg_dump',
                    self.db_url,
                    '-f', str(backup_path),
                    '--no-password',
                    '--format=custom'  # Formato comprimido
                ]

                result = subprocess.run(cmd, capture_output=True, text=True)
                if result.returncode == 0:
                    logger.info(f"PostgreSQL backup created: {backup_path}")
                    return backup_path
                else:
                    logger.error(f"PostgreSQL backup failed: {result.stderr}")
                    return None

        except Exception as e:
            logger.error(f"Database backup error: {e}")
            return None

    def create_files_backup(self):
        """Cria backup dos arquivos do sistema"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_filename = f"files_backup_{timestamp}.tar.gz"
        backup_path = self.backup_dir / backup_filename

        try:
            # Criar lista de arquivos/diretórios para backup
            items_to_backup = []
            for item in self.backup_dirs:
                if os.path.exists(item):
                    items_to_backup.append(item)

            if not items_to_backup:
                logger.warning("No directories found for backup")
                return None

            # Criar arquivo tar.gz
            cmd = ['tar', '-czf', str(backup_path)] + items_to_backup
            result = subprocess.run(cmd, capture_output=True, text=True)

            if result.returncode == 0:
                logger.info(f"Files backup created: {backup_path}")
                return backup_path
            else:
                logger.error(f"Files backup failed: {result.stderr}")
                return None

        except Exception as e:
            logger.error(f"Files backup error: {e}")
            return None

    def create_config_backup(self):
        """Cria backup das configurações (sem senhas)"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_filename = f"config_backup_{timestamp}.json"
        backup_path = self.backup_dir / backup_filename

        try:
            # Coletar configurações não sensíveis
            config_backup = {
                'timestamp': timestamp,
                'environment': os.environ.get('FLASK_ENV', 'development'),
                'backup_settings': {
                    'retention_days': self.retention_days,
                    'backup_dirs': self.backup_dirs
                },
                'system_info': {
                    'python_version': os.sys.version,
                    'platform': os.sys.platform
                }
            }

            with open(backup_path, 'w', encoding='utf-8') as f:
                json.dump(config_backup, f, indent=2, ensure_ascii=False)

            logger.info(f"Config backup created: {backup_path}")
            return backup_path

        except Exception as e:
            logger.error(f"Config backup error: {e}")
            return None

    def cleanup_old_backups(self):
        """Remove backups antigos baseado na retenção"""
        try:
            cutoff_date = datetime.now().timestamp() - (self.retention_days * 24 * 60 * 60)

            removed_count = 0
            for backup_file in self.backup_dir.glob('*'):
                if backup_file.stat().st_mtime < cutoff_date:
                    backup_file.unlink()
                    removed_count += 1
                    logger.info(f"Removed old backup: {backup_file}")

            if removed_count > 0:
                logger.info(f"Cleaned up {removed_count} old backup files")

        except Exception as e:
            logger.error(f"Cleanup error: {e}")

    def create_full_backup(self):
        """Executa backup completo"""
        logger.info("Starting full backup process")

        results = {
            'timestamp': datetime.now().isoformat(),
            'database': str(self.create_database_backup()) if self.create_database_backup() else None,
            'files': str(self.create_files_backup()) if self.create_files_backup() else None,
            'config': str(self.create_config_backup()) if self.create_config_backup() else None,
            'status': 'success'
        }

        # Verificar se todos os backups foram criados
        if not all([results['database'], results['files'], results['config']]):
            results['status'] = 'partial'
            logger.warning("Some backups failed - partial backup completed")
        else:
            logger.info("Full backup completed successfully")

        # Limpar backups antigos
        self.cleanup_old_backups()

        return results

    def get_backup_info(self):
        """Retorna informações sobre os backups existentes"""
        try:
            backups = []
            for backup_file in self.backup_dir.glob('*'):
                stat = backup_file.stat()
                backups.append({
                    'filename': backup_file.name,
                    'size': stat.st_size,
                    'created': datetime.fromtimestamp(stat.st_mtime).isoformat(),
                    'type': backup_file.suffix.replace('.', '')
                })

            # Ordenar por data de criação (mais recente primeiro)
            backups.sort(key=lambda x: x['created'], reverse=True)

            return {
                'total_backups': len(backups),
                'total_size': sum(b['size'] for b in backups),
                'backups': backups[:10],  # Últimos 10
                'retention_days': self.retention_days
            }

        except Exception as e:
            logger.error(f"Error getting backup info: {e}")
            return {'error': str(e)}

def main():
    """Função principal para execução via linha de comando"""
    service = BackupService()
    result = service.create_full_backup()

    print(json.dumps(result, indent=2, ensure_ascii=False))

if __name__ == '__main__':
    main()