"""
Database Service - Database initialization, validation, and health checking

This service ensures the database schema is correct on startup and provides
database management utilities.
"""
import os
import sqlite3
from datetime import datetime
from typing import Tuple, Dict, List, Any
from flask import current_app
from app import db
from app.persistence.models import AdminUser, AuditLog, LockerSensorData
from app.business.locker import Locker
from app.business.parcel import Parcel
import logging

logger = logging.getLogger(__name__)

class DatabaseService:
    """Service for database initialization, validation, and management"""
    
    @staticmethod
    def initialize_databases() -> Tuple[bool, str]:
        """
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
            elif Locker.query.count() == 0:
                should_seed = True
                logger.info("📭 Empty database detected, will seed initial data")
            
            if should_seed:
                DatabaseService.seed_initial_data()
                logger.info("🌱 Initial data seeded")
            else:
                existing_count = Locker.query.count()
                logger.info(f"📊 Database has {existing_count} existing lockers, skipping seeding")
            
            # 6. Health check
            health_result = DatabaseService.health_check()
            if not health_result[0]:
                return False, f"Database health check failed: {health_result[1]}"
            
            logger.info("🎉 Database initialization completed successfully")
            return True, "Database initialized successfully"
            
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
                    table_columns = [c.name for c in Locker.__table__.columns]
                elif table_name == 'parcel':
                    table_columns = [c.name for c in Parcel.__table__.columns]
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
            # Create admin user if none exists
            if AdminUser.query.count() == 0:
                admin_user = AdminUser(username='admin')
                admin_user.set_password('admin123')  # TODO: Change in production
                db.session.add(admin_user)
                logger.info("👤 Created default admin user")
            
            # Create lockers using configuration service
            from app.services.locker_configuration_service import LockerConfigurationService
            success, message = LockerConfigurationService.seed_lockers_from_configuration()
            
            if success:
                logger.info(f"🏗️ {message}")
            else:
                logger.error(f"❌ Locker seeding failed: {message}")
                # Don't raise exception - admin user creation should still succeed
            
            db.session.commit()
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"❌ Error seeding initial data: {str(e)}")
            raise
    
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
                locker_count = Locker.query.count()
                health_data['main_database'] = 'connected'
                health_data['record_counts']['lockers'] = locker_count
            except Exception as e:
                health_data['main_database'] = 'error'
                health_data['issues'].append(f"Main database error: {str(e)}")
            
            # Test audit database connection
            try:
                audit_count = AuditLog.query.count()
                health_data['audit_database'] = 'connected'
                health_data['record_counts']['audit_logs'] = audit_count
            except Exception as e:
                health_data['audit_database'] = 'error'
                health_data['issues'].append(f"Audit database error: {str(e)}")
            
            # Test other tables
            try:
                health_data['record_counts']['parcels'] = Parcel.query.count()
                health_data['record_counts']['admins'] = AdminUser.query.count()
                health_data['record_counts']['sensor_data'] = LockerSensorData.query.count()
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
        """Get comprehensive database statistics"""
        try:
            stats = {
                'record_counts': {
                    'lockers': Locker.query.count(),
                    'parcels': Parcel.query.count(),
                    'admin_users': AdminUser.query.count(),
                    'audit_logs': AuditLog.query.count(),
                    'sensor_data': LockerSensorData.query.count()
                },
                'locker_status_breakdown': {},
                'parcel_status_breakdown': {},
                'database_files': {}
            }
            
            # Locker status breakdown
            from sqlalchemy import func
            locker_statuses = db.session.query(
                Locker.status, 
                func.count(Locker.status)
            ).group_by(Locker.status).all()
            
            stats['locker_status_breakdown'] = {status: count for status, count in locker_statuses}
            
            # Parcel status breakdown
            parcel_statuses = db.session.query(
                Parcel.status, 
                func.count(Parcel.status)
            ).group_by(Parcel.status).all()
            
            stats['parcel_status_breakdown'] = {status: count for status, count in parcel_statuses}
            
            # Database file sizes
            db_dir = current_app.config.get('DATABASE_DIR', '/app/databases')
            for db_file in ['campus_locker.db', 'campus_locker_audit.db']:
                file_path = os.path.join(db_dir, db_file)
                if os.path.exists(file_path):
                    size_bytes = os.path.getsize(file_path)
                    stats['database_files'][db_file] = {
                        'size_bytes': size_bytes,
                        'size_mb': round(size_bytes / (1024 * 1024), 2)
                    }
            
            return stats
            
        except Exception as e:
            logger.error(f"Error getting database statistics: {str(e)}")
            return {'error': str(e)}
    
    @staticmethod
    def backup_databases(backup_dir: str = '/app/backups') -> Tuple[bool, str]:
        """Create backup copies of database files"""
        try:
            # Ensure backup directory exists
            os.makedirs(backup_dir, exist_ok=True)
            
            db_dir = current_app.config.get('DATABASE_DIR', '/app/databases')
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            
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