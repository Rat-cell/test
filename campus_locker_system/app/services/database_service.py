"""
Database Service - Database initialization, validation, and health checking

This service ensures the database schema is correct on startup and provides
database management utilities.
"""
import os
import sqlite3
from datetime import datetime
import datetime as dt
from typing import Tuple, Dict, List, Any
from flask import current_app
from app import db
from app.persistence.models import AdminUser, AuditLog, LockerSensorData
from app.persistence.models import Locker as PersistenceLocker, Parcel as PersistenceParcel
import logging
from app.services.admin_auth_service import AdminAuthService
from app.business.admin_auth import AdminRole
from app.persistence.repositories.locker_repository import LockerRepository
from app.persistence.repositories.parcel_repository import ParcelRepository
from app.persistence.repositories.audit_log_repository import AuditLogRepository
from app.persistence.repositories.locker_sensor_data_repository import LockerSensorDataRepository

logger = logging.getLogger(__name__)

class DatabaseService:
    """
    Service for database initialization, validation, and management
    NFR-02: Reliability - SQLite WAL mode configuration for crash safety
    NFR-04: Backup - Automated scheduled backup management
    """
    
    @staticmethod
    def initialize_databases() -> Tuple[bool, str]:
        """
        Initialize databases with safety features and reliability configuration
        NFR-02: Reliability - Configures SQLite WAL mode for crash safety
        NFR-04: Backup - Includes backup status verification on startup

        Initialize and validate databases on application startup
        Returns (success, message)
        """
        try:
            logger.info("🗄️ Starting database initialization...")
            
            # 1. Ensure database directory exists
            db_dir = current_app.config.get('DATABASE_DIR', '/app/databases')
            if not os.path.exists(db_dir):
                os.makedirs(db_dir, exist_ok=True)
                logger.info(f"📂 Created database directory: {db_dir}")
            
            # 2. Check database file existence
            main_db_path = os.path.join(db_dir, 'campus_locker.db')
            audit_db_path = os.path.join(db_dir, 'campus_locker_audit.db')
            
            main_db_exists = os.path.exists(main_db_path)
            audit_db_exists = os.path.exists(audit_db_path)
            
            logger.info(f"📊 Database status - Main: {'EXISTS' if main_db_exists else 'MISSING'}, Audit: {'EXISTS' if audit_db_exists else 'MISSING'}")
            
            # 3. Create all tables (this is safe - won't overwrite existing)
            db.create_all()
            logger.info("🛠️ Database tables created/verified")
            
            # NFR-02: Configure SQLite WAL mode for crash safety
            try:
                DatabaseService.configure_sqlite_wal_mode()
                logger.info("✅ SQLite WAL mode configured for crash safety")
            except Exception as e:
                logger.warning(f"⚠️ SQLite WAL mode configuration failed: {str(e)}")
            
            # 4. Validate schema structure
            validation_result = DatabaseService.validate_schema()
            if not validation_result[0]:
                logger.error(f"❌ Schema validation failed: {validation_result[1]}")
                return False, f"Schema validation failed: {validation_result[1]}"
            
            logger.info("✅ Schema validation passed")
            
            # 5. Seed initial data if databases were just created OR if they're empty
            should_seed = False
            
            # Seed if database files were just created
            if not main_db_exists or not audit_db_exists:
                should_seed = True
                logger.info("🆕 New databases detected, will seed initial data")
            
            # Also seed if database exists but has no lockers (empty deployment)
            elif LockerRepository.get_count() == 0:
                should_seed = True
                logger.info("📭 Empty database detected (no lockers), will seed initial data")
            
            if should_seed:
                DatabaseService.seed_initial_data()
                logger.info("🌱 Initial data seeded")
            else:
                existing_locker_count = LockerRepository.get_count()
                logger.info(f"📊 Database has {existing_locker_count} existing lockers, skipping seeding")
            
            # 6. Health check
            health_result = DatabaseService.health_check()
            if not health_result[0]:
                return False, f"Database health check failed: {health_result[1]}"
            
            # 7. Enhanced validation
            detailed_validation = DatabaseService.validate_schema()
            if not detailed_validation[0]:
                logger.warning(f"⚠️ Detailed schema validation issues found: {detailed_validation[1]}")
            
            logger.info("✅ Database initialization completed successfully")
            return True, "Database initialization completed successfully"
            
        except Exception as e:
            error_msg = f"Database initialization failed: {str(e)}"
            logger.error(f"❌ {error_msg}")
            return False, error_msg
    
    @staticmethod
    def validate_schema() -> Tuple[bool, str]:
        """
        Validate that the database schema matches expected structure
        Returns (is_valid, message)
        """
        try:
            # Check main database schema
            main_validation = DatabaseService._validate_main_database()
            if not main_validation[0]:
                return main_validation
            
            # Check audit database schema
            audit_validation = DatabaseService._validate_audit_database()
            if not audit_validation[0]:
                return audit_validation
            
            return True, "All database schemas are valid"
            
        except Exception as e:
            return False, f"Schema validation error: {str(e)}"
    
    @staticmethod
    def _validate_main_database() -> Tuple[bool, str]:
        """Validate main database schema"""
        expected_tables = {
            'locker': ['id', 'location', 'size', 'status'],
            'parcel': ['id', 'locker_id', 'pin_hash', 'otp_expiry', 'recipient_email', 
                      'status', 'deposited_at', 'picked_up_at'],
            'admin_user': ['id', 'username', 'password_hash', 'last_login'],
            'locker_sensor_data': ['id', 'locker_id', 'timestamp', 'has_contents']
        }
        
        try:
            # Check if all expected tables exist with correct columns
            for table_name, expected_columns in expected_tables.items():
                if table_name == 'locker':
                    table_columns = [c.name for c in PersistenceLocker.__table__.columns]
                elif table_name == 'parcel':
                    table_columns = [c.name for c in PersistenceParcel.__table__.columns]
                elif table_name == 'admin_user':
                    table_columns = [c.name for c in AdminUser.__table__.columns]
                elif table_name == 'locker_sensor_data':
                    table_columns = [c.name for c in LockerSensorData.__table__.columns]
                
                # Check that all expected columns exist
                missing_columns = set(expected_columns) - set(table_columns)
                if missing_columns:
                    return False, f"Table '{table_name}' missing columns: {missing_columns}"
            
            return True, "Main database schema valid"
            
        except Exception as e:
            return False, f"Main database validation error: {str(e)}"
    
    @staticmethod
    def _validate_audit_database() -> Tuple[bool, str]:
        """Validate audit database schema"""
        expected_columns = ['id', 'timestamp', 'action', 'details', 'admin_id', 'admin_username']
        
        try:
            # Check audit log table structure
            audit_columns = [c.name for c in AuditLog.__table__.columns]
            
            missing_columns = set(expected_columns) - set(audit_columns)
            if missing_columns:
                return False, f"Audit log table missing columns: {missing_columns}"
            
            # Ensure no extra over-engineered columns exist
            unexpected_columns = set(audit_columns) - set(expected_columns)
            if unexpected_columns:
                logger.warning(f"⚠️ Audit log has unexpected columns (may be legacy): {unexpected_columns}")
            
            return True, "Audit database schema valid"
            
        except Exception as e:
            return False, f"Audit database validation error: {str(e)}"
    
    @staticmethod
    def seed_initial_data():
        """Seed initial data for testing/development"""
        try:
            # Create admin user if none exists, using AdminAuthService
            if AdminAuthService.get_admin_count() == 0:
                logger.info("No admin users found by DatabaseService. Attempting to create default admin.")
                admin_user, message = AdminAuthService.create_admin_user(
                    current_app.config.get('DEFAULT_ADMIN_USERNAME', 'admin'),
                    current_app.config.get('DEFAULT_ADMIN_PASSWORD', 'AdminPass123!'),
                    AdminRole.ADMIN
                )
                if admin_user:
                    logger.info(f"👤 Default admin user '{admin_user.username}' created by DatabaseService.")
                else:
                    logger.warning(f"⚠️ Could not create default admin user via DatabaseService: {message}")
            else:
                logger.info(f"Admin users already exist (Count: {AdminAuthService.get_admin_count()}). DatabaseService skipping default admin creation.")

            # Create lockers using configuration service
            from app.services.locker_configuration_service import LockerConfigurationService
            success, message = LockerConfigurationService.seed_lockers_from_configuration()
            
            if success:
                logger.info(f"🏗️ {message}")
            else:
                logger.error(f"❌ Locker seeding failed: {message}")
            
        except Exception as e:
            logger.error(f"❌ Error seeding initial data: {str(e)}")
    
    @staticmethod
    def health_check() -> Tuple[bool, Dict[str, Any]]:
        """
        Perform comprehensive database health check
        Returns (is_healthy, health_data)
        """
        health_data = {
            'main_database': 'unknown',
            'audit_database': 'unknown',
            'tables': {},
            'record_counts': {},
            'issues': []
        }
        
        try:
            # Test main database connection
            try:
                locker_count = LockerRepository.get_count()
                health_data['main_database'] = 'connected'
                health_data['record_counts']['lockers'] = locker_count
            except Exception as e:
                health_data['main_database'] = 'error'
                health_data['issues'].append(f"Main database error: {str(e)}")
            
            # Test audit database connection
            try:
                audit_count = AuditLogRepository.get_count()
                health_data['audit_database'] = 'connected'
                health_data['record_counts']['audit_logs'] = audit_count
            except Exception as e:
                health_data['audit_database'] = 'error'
                health_data['issues'].append(f"Audit database error: {str(e)}")
            
            # Test other tables
            try:
                health_data['record_counts']['parcels'] = ParcelRepository.get_count()
                health_data['record_counts']['admins'] = AdminAuthService.get_admin_count()
                health_data['record_counts']['sensor_data'] = LockerSensorDataRepository.get_count()
            except Exception as e:
                health_data['issues'].append(f"Table query error: {str(e)}")
            
            # Overall health status
            is_healthy = (
                health_data['main_database'] == 'connected' and 
                health_data['audit_database'] == 'connected' and
                len(health_data['issues']) == 0
            )
            
            return is_healthy, health_data
            
        except Exception as e:
            health_data['issues'].append(f"Health check error: {str(e)}")
            return False, health_data
    
    @staticmethod
    def get_database_statistics() -> Dict[str, Any]:
        """Provide overall database statistics"""
        stats = {
            'total_lockers': 0,
            'occupied_lockers': 0,
            'free_lockers': 0,
            'out_of_service_lockers': 0,
            'total_parcels': 0,
            'deposited_parcels': 0,
            'picked_up_parcels': 0,
            'audit_log_entries': 0,
            'admin_users': 0
        }
        try:
            # Use repositories for counts
            stats['total_lockers'] = LockerRepository.get_count()
            stats['occupied_lockers'] = LockerRepository.get_count_by_status('occupied')
            stats['free_lockers'] = LockerRepository.get_count_by_status('free')
            stats['out_of_service_lockers'] = LockerRepository.get_count_by_status('out_of_service')
            
            stats['total_parcels'] = ParcelRepository.get_count()
            stats['deposited_parcels'] = ParcelRepository.get_count_by_status('deposited')
            stats['picked_up_parcels'] = ParcelRepository.get_count_by_status('picked_up')
            
            # AuditLog and AdminUser counts
            stats['audit_log_entries'] = AuditLogRepository.get_count()
            stats['admin_users'] = AdminAuthService.get_admin_count()
            
            return stats
        except Exception as e:
            logger.error(f"Error getting database statistics: {str(e)}")
            return {'error': str(e), **stats}
    
    @staticmethod
    def backup_databases(backup_dir: str = '/app/backups') -> Tuple[bool, str]:
        """Create backup copies of database files"""
        try:
            # Ensure backup directory exists
            os.makedirs(backup_dir, exist_ok=True)
            
            db_dir = current_app.config.get('DATABASE_DIR', '/app/databases')
            timestamp = datetime.now(dt.UTC).strftime('%Y%m%d_%H%M%S')
            
            backed_up_files = []
            
            for db_file in ['campus_locker.db', 'campus_locker_audit.db']:
                source_path = os.path.join(db_dir, db_file)
                backup_filename = f"{db_file.replace('.db', '')}_{timestamp}.db"
                backup_path = os.path.join(backup_dir, backup_filename)
                
                if os.path.exists(source_path):
                    import shutil
                    shutil.copy2(source_path, backup_path)
                    backed_up_files.append(backup_filename)
            
            return True, f"Backed up files: {', '.join(backed_up_files)}"
            
        except Exception as e:
            return False, f"Backup failed: {str(e)}"
    
    @staticmethod
    def post_initialization_tasks():
        """
        Run tasks that should happen after database is fully initialized
        This includes backup checks and other maintenance tasks
        """
        try:
            # NFR-04: Check and create scheduled backup if needed
            try:
                backup_created, backup_message = DatabaseService.run_scheduled_backup_if_needed()
                if backup_created:
                    logger.info(f"💾 Scheduled backup: {backup_message}")
                else:
                    logger.debug(f"📅 Backup check: {backup_message}")
            except Exception as e:
                logger.warning(f"⚠️ Scheduled backup check failed: {str(e)}")
            
        except Exception as e:
            logger.warning(f"⚠️ Post-initialization tasks failed: {str(e)}")
    
    @staticmethod
    def create_scheduled_backup() -> Tuple[bool, str]:
        """NFR-04: Create scheduled backup based on configurable interval"""
        try:
            # Get database directory
            db_dir = current_app.config.get('DATABASE_DIR', '/app/databases')
            if not os.path.exists(db_dir):
                return False, f"Database directory not found: {db_dir}"
            
            # NFR-04: Create backup directory if needed
            backup_dir = os.path.join(db_dir, 'backups')
            os.makedirs(backup_dir, exist_ok=True)
            
            # Generate timestamp
            timestamp = datetime.now(dt.UTC).strftime('%Y%m%d_%H%M%S')
            
            # NFR-04: Get configurable backup interval for backup naming
            backup_interval_days = current_app.config.get('BACKUP_INTERVAL_DAYS', 7)
            
            # NFR-04: List of database files to backup (main + audit)
            db_files = ['campus_locker.db', 'campus_locker_audit.db']
            backed_up_files = []
            
            for db_file in db_files:
                source_path = os.path.join(db_dir, db_file)
                if os.path.exists(source_path):
                    # NFR-04: Create backup filename with configurable interval reference
                    backup_filename = f"{db_file.replace('.db', '')}_scheduled_{backup_interval_days}day_{timestamp}.db"
                    backup_path = os.path.join(backup_dir, backup_filename)
                    
                    # NFR-04: Copy the database file for data preservation
                    import shutil
                    shutil.copy2(source_path, backup_path)
                    backed_up_files.append(backup_filename)
            
            if backed_up_files:
                backup_list = ', '.join(backed_up_files)
                logger.info(f"💾 Backup created for scheduled_{backup_interval_days}day: {backup_list}")
                return True, f"Backup created: {backup_list}"
            else:
                return False, "No database files found to backup"
                
        except Exception as e:
            backup_interval_days = current_app.config.get('BACKUP_INTERVAL_DAYS', 7)
            error_msg = f"Backup creation failed for scheduled_{backup_interval_days}day: {str(e)}"
            logger.error(error_msg)
            return False, error_msg
    
    @staticmethod
    def should_create_scheduled_backup() -> Tuple[bool, str]:
        """
        NFR-04: Check if a scheduled backup should be created based on configurable interval
        
        Returns:
            Tuple[bool, str]: (should_backup, reason)
        """
        try:
            db_dir = current_app.config.get('DATABASE_DIR', '/app/databases')
            backup_dir = os.path.join(db_dir, 'backups')
            
            # NFR-04: Get configurable backup interval
            backup_interval_days = current_app.config.get('BACKUP_INTERVAL_DAYS', 7)
            
            if not os.path.exists(backup_dir):
                return True, f"No backup directory exists - creating first scheduled backup (interval: {backup_interval_days} days)"
            
            # NFR-04: Look for the most recent scheduled backup with any interval pattern
            scheduled_backups = []
            for backup_file in os.listdir(backup_dir):
                if backup_file.endswith('.db') and '_scheduled_' in backup_file and 'day_' in backup_file:
                    file_path = os.path.join(backup_dir, backup_file)
                    file_time = os.path.getmtime(file_path)
                    scheduled_backups.append((backup_file, file_time))
            
            if not scheduled_backups:
                return True, f"No scheduled backups found - creating first scheduled backup (interval: {backup_interval_days} days)"
            
            # NFR-04: Find the most recent scheduled backup
            most_recent = max(scheduled_backups, key=lambda x: x[1])
            most_recent_time = most_recent[1]
            
            # NFR-04: Check if configured interval has passed
            interval_seconds = backup_interval_days * 24 * 60 * 60
            cutoff_time = datetime.now(dt.UTC).timestamp() - interval_seconds
            
            if most_recent_time < cutoff_time:
                days_since = (datetime.now(dt.UTC).timestamp() - most_recent_time) / (24 * 60 * 60)
                return True, f"Last scheduled backup was {days_since:.1f} days ago (interval: {backup_interval_days} days) - creating new backup"
            else:
                days_since = (datetime.now(dt.UTC).timestamp() - most_recent_time) / (24 * 60 * 60)
                return False, f"Recent scheduled backup exists from {days_since:.1f} days ago (interval: {backup_interval_days} days)"
                
        except Exception as e:
            backup_interval_days = current_app.config.get('BACKUP_INTERVAL_DAYS', 7)
            error_msg = f"Error checking scheduled backup status: {str(e)}"
            logger.error(error_msg)
            return True, f"Error checking backup status - creating backup anyway (interval: {backup_interval_days} days): {str(e)}"
    
    @staticmethod
    def run_scheduled_backup_if_needed() -> Tuple[bool, str]:
        """
        NFR-04: Run scheduled backup if configured interval has passed since last backup
        
        Returns:
            Tuple[bool, str]: (backup_created, message)
        """
        try:
            should_backup, reason = DatabaseService.should_create_scheduled_backup()
            
            if should_backup:
                success, message = DatabaseService.create_scheduled_backup()
                if success:
                    full_message = f"Scheduled backup created successfully. Reason: {reason}. Result: {message}"
                    logger.info(f"📅 {full_message}")
                    return True, full_message
                else:
                    error_message = f"Scheduled backup failed. Reason: {reason}. Error: {message}"
                    logger.error(f"❌ {error_message}")
                    return False, error_message
            else:
                logger.info(f"⏭️ Scheduled backup skipped: {reason}")
                return False, f"Backup not needed: {reason}"
                
        except Exception as e:
            error_msg = f"Critical error in scheduled backup process: {str(e)}"
            logger.error(error_msg)
            return False, error_msg
    
    @staticmethod
    def configure_sqlite_wal_mode():
        """NFR-02: Configure SQLite WAL mode for crash safety and reliability"""
        try:
            # Only configure if WAL mode is enabled in configuration
            wal_enabled = current_app.config.get('ENABLE_SQLITE_WAL_MODE', True)
            if not wal_enabled:
                logger.info("📋 SQLite WAL mode disabled in configuration")
                return
            
            db_dir = current_app.config.get('DATABASE_DIR', '/app/databases')
            sync_mode = current_app.config.get('SQLITE_SYNCHRONOUS_MODE', 'NORMAL')
            
            # NFR-02: Configure main database with WAL mode
            main_db_path = os.path.join(db_dir, 'campus_locker.db')
            if os.path.exists(main_db_path):
                conn = sqlite3.connect(main_db_path)
                cursor = conn.cursor()
                
                # NFR-02: Enable WAL mode for crash safety (max 1 transaction loss)
                cursor.execute("PRAGMA journal_mode=WAL")
                cursor.execute(f"PRAGMA synchronous={sync_mode}")
                cursor.execute("PRAGMA wal_autocheckpoint=1000")
                cursor.execute("PRAGMA temp_store=MEMORY")
                
                # Verify WAL mode is active
                cursor.execute("PRAGMA journal_mode")
                journal_mode = cursor.fetchone()[0]
                
                conn.close()
                logger.info(f"💾 Main database WAL mode: {journal_mode} (sync: {sync_mode})")
            
            # NFR-02: Configure audit database with WAL mode
            audit_db_path = os.path.join(db_dir, 'campus_locker_audit.db')
            if os.path.exists(audit_db_path):
                audit_conn = sqlite3.connect(audit_db_path)
                audit_cursor = audit_conn.cursor()
                
                # NFR-02: Enable WAL mode for audit database crash safety
                audit_cursor.execute("PRAGMA journal_mode=WAL")
                audit_cursor.execute(f"PRAGMA synchronous={sync_mode}")
                audit_cursor.execute("PRAGMA wal_autocheckpoint=1000")
                audit_cursor.execute("PRAGMA temp_store=MEMORY")
                
                # Verify WAL mode is active
                audit_cursor.execute("PRAGMA journal_mode")
                audit_journal_mode = audit_cursor.fetchone()[0]
                
                audit_conn.close()
                logger.info(f"💾 Audit database WAL mode: {audit_journal_mode} (sync: {sync_mode})")
            
            logger.info("✅ NFR-02: SQLite WAL mode configured for crash safety")
            
        except Exception as e:
            error_msg = f"NFR-02: SQLite WAL mode configuration failed: {str(e)}"
            logger.error(error_msg)
            raise Exception(error_msg)


# Utility function for application startup
def initialize_database_on_startup():
    """
    Convenience function to be called during application initialization
    """
    success, message = DatabaseService.initialize_databases()
    if not success:
        logger.critical(f"🚨 CRITICAL: Database initialization failed - {message}")
        raise RuntimeError(f"Database initialization failed: {message}")
    
    logger.info(f"✅ Database startup completed: {message}")
    return success, message 