import os
import subprocess
from datetime import datetime
from app_logging.app_logger import app_logger

class BackupManager:
    @staticmethod
    def create_backup():
        """Creates a PostgreSQL dump for the database."""
        db_name = os.getenv('DB_NAME', 'wms_erp')
        db_user = os.getenv('DB_USER', 'postgres')
        db_pass = os.getenv('DB_PASS', 'postgres')
        db_host = os.getenv('DB_HOST', 'localhost')

        backup_dir = "backups"
        if not os.path.exists(backup_dir):
            os.makedirs(backup_dir)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{backup_dir}/{db_name}_backup_{timestamp}.sql"

        try:
            # Note: pg_dump requires password. Usually handled via .pgpass or environment
            os.environ['PGPASSWORD'] = db_pass
            cmd = f"pg_dump -h {db_host} -U {db_user} {db_name} > {filename}"
            subprocess.run(cmd, shell=True, check=True)
            app_logger.info(f"Backup created successfully: {filename}")
            return filename
        except Exception as e:
            app_logger.error(f"Backup failed: {e}")
            return None
        finally:
            if 'PGPASSWORD' in os.environ:
                del os.environ['PGPASSWORD']
