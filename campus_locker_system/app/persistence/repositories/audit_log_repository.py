from typing import Optional, Dict, Any, List
from app import db # For db.session.get if needed, and db.session.commit/rollback
from app.persistence.models import AuditLog as PersistenceAuditLog
from flask import current_app
from datetime import datetime
import json # Import json

class AuditLogRepository:
    @staticmethod
    def save_log(log_entry: PersistenceAuditLog) -> bool:
        """Saves a single audit log entry instance (adds and commits)."""
        try:
            db.session.add(log_entry)
            db.session.commit()
            return True
        except Exception as e:
            db.session.rollback()
            # Use a generic logger here as AuditService might not be available/working
            current_app.logger.error(f"Error saving audit log in repository: {str(e)}")
            return False

    @staticmethod
    def create_and_save_log(action: str, details: Optional[Dict[str, Any]] = None, 
                              admin_id: Optional[int] = None, admin_username: Optional[str] = None) -> bool:
        """Creates a new AuditLog entry and saves it using the repository.
           This combines creation and saving for convenience.
        """
        try:
            details_json = None
            if details is not None:
                try:
                    details_json = json.dumps(details)
                except TypeError as te:
                    current_app.logger.error(f"AuditLog details serialization error for action '{action}': {str(te)}. Storing as raw string.")
                    details_json = str(details) # Fallback to string representation

            log_entry = PersistenceAuditLog(
                timestamp=datetime.utcnow(),
                action=action,
                details=details_json, # Pass the JSON string
                admin_id=admin_id,
                admin_username=admin_username
            )
            return AuditLogRepository.save_log(log_entry)
        except Exception as e:
            current_app.logger.error(f"Error creating and saving audit log for action '{action}': {str(e)}")
            return False

    @staticmethod
    def get_paginated_logs(page: int, per_page: int):
        """Fetches paginated audit logs, ordered by timestamp descending."""
        try:
            return PersistenceAuditLog.query.order_by(PersistenceAuditLog.timestamp.desc()).paginate(page=page, per_page=per_page, error_out=False)
        except Exception as e:
            current_app.logger.error(f"Error fetching paginated audit logs: {str(e)}")
            return None # Or an empty pagination object

    @staticmethod
    def get_count() -> int:
        """Returns the total count of audit log entries."""
        try:
            return PersistenceAuditLog.query.count()
        except Exception as e:
            current_app.logger.error(f"Error counting audit logs in repository: {str(e)}")
            return 0

    @staticmethod
    def get_logs(limit: int, actions: Optional[List[str]] = None, 
                   start_date: Optional[datetime] = None, end_date: Optional[datetime] = None, 
                   admin_id: Optional[int] = None, order_desc: bool = True) -> List[PersistenceAuditLog]:
        """Retrieves audit logs with optional filtering and ordering."""
        try:
            query = PersistenceAuditLog.query

            if actions:
                query = query.filter(PersistenceAuditLog.action.in_(actions))
            if start_date:
                query = query.filter(PersistenceAuditLog.timestamp >= start_date)
            if end_date:
                query = query.filter(PersistenceAuditLog.timestamp <= end_date)
            if admin_id is not None:
                query = query.filter(PersistenceAuditLog.admin_id == admin_id)
            
            if order_desc:
                query = query.order_by(PersistenceAuditLog.timestamp.desc())
            else:
                query = query.order_by(PersistenceAuditLog.timestamp.asc())
            
            if limit > 0: # Apply limit if positive
                query = query.limit(limit)
            
            return query.all()
        except Exception as e:
            current_app.logger.error(f"Error retrieving logs from repository: {str(e)}")
            return []

    @staticmethod
    def delete_logs_by_actions_and_older_than(actions: List[str], cutoff_date: datetime) -> int:
        """Deletes logs matching actions and older than cutoff_date. Returns count of deleted logs."""
        try:
            deleted_count = PersistenceAuditLog.query.filter(
                PersistenceAuditLog.action.in_(actions),
                PersistenceAuditLog.timestamp < cutoff_date
            ).delete(synchronize_session=False)
            db.session.commit()
            return deleted_count if deleted_count is not None else 0
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Error deleting old audit logs (actions: {actions}): {str(e)}")
            return 0

    @staticmethod
    def get_count_by_daterange(start_date: datetime, end_date: Optional[datetime] = None) -> int:
        """Counts audit logs within a daterange."""
        try:
            query = PersistenceAuditLog.query.filter(PersistenceAuditLog.timestamp >= start_date)
            if end_date:
                query = query.filter(PersistenceAuditLog.timestamp <= end_date)
            return query.count()
        except Exception as e:
            current_app.logger.error(f"Error counting audit logs by daterange: {str(e)}")
            return 0

    @staticmethod
    def get_count_by_actions_and_daterange(actions: List[str], start_date: datetime, end_date: Optional[datetime] = None) -> int:
        """Counts audit logs by actions and daterange."""
        try:
            query = PersistenceAuditLog.query.filter(PersistenceAuditLog.action.in_(actions))
            query = query.filter(PersistenceAuditLog.timestamp >= start_date)
            if end_date:
                query = query.filter(PersistenceAuditLog.timestamp <= end_date)
            return query.count()
        except Exception as e:
            current_app.logger.error(f"Error counting audit logs by actions and daterange: {str(e)}")
            return 0 