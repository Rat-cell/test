# Audit service - orchestration layer
from typing import Tuple, Optional, List, Dict, Any
from flask import current_app, session, request
from app.business.audit import AuditManager, AuditEvent, AuditEventCategory, AuditEventSeverity
from app.persistence.repositories.audit_log_repository import AuditLogRepository
from app.persistence.models import AuditLog as AuditLogEntity
import json
from datetime import datetime, timedelta
import datetime as dt

class AuditService:
    """
    FR-07: Audit Trail - Service for comprehensive audit logging of system events
    NFR-03: Security - Security event monitoring and compliance logging
    """
    
    @staticmethod
    def log_event(action: str, details: Optional[Dict[str, Any]] = None):
        """Log a system event using AuditLogRepository.
           NFR-03: Security - Enhanced audit logging for security-sensitive operations.
        """
        try:
            # Attempt to get admin_id and admin_username from session if available
            admin_id = session.get('admin_id')
            admin_username = session.get('admin_username')

            # If details already contain admin_id/username (e.g., passed from a service 
            # that has more direct context), use that, otherwise use session's.
            # This allows services to specify the acting admin if it's not the logged-in one (e.g. system actions)
            final_admin_id = details.pop('admin_id', admin_id) if details else admin_id
            final_admin_username = details.pop('admin_username', admin_username) if details else admin_username

            # Convert details to JSON string if it's a dict
            # The repository and model should handle the dict directly if the DB field supports JSON.
            # Assuming the model's 'details' field is Text or JSON that SQLAlchemy handles.
            # No explicit conversion to json.dumps here if the model/repo handles dicts.

            success = AuditLogRepository.create_and_save_log(
                action=action,
                details=details,
                admin_id=final_admin_id,
                admin_username=final_admin_username
            )
            if not success:
                current_app.logger.error(f"Failed to save audit log event '{action}' via repository.")

        except Exception as e:
            # Fallback logging if AuditService itself fails critically
            current_app.logger.error(f"CRITICAL: AuditService failed to log event '{action}': {str(e)}")
            # Optionally, try a more raw form of logging or raise an alert here

    @staticmethod
    def get_paginated_audit_logs(page: int, per_page: int = 15):
        """
        Retrieves a paginated list of audit logs using AuditLogRepository.
        """
        try:
            return AuditLogRepository.get_paginated_logs(page=page, per_page=per_page)
        except Exception as e:
            current_app.logger.error(f"Error retrieving paginated audit logs from service: {str(e)}")
            return None # Or an empty list/pagination object depending on expected return type
    
    @staticmethod
    def get_audit_logs(
        page: int = 1, 
        per_page: int = 20, 
        action: Optional[str] = None, 
        user_id: Optional[int] = None, 
        start_date: Optional[str] = None, 
        end_date: Optional[str] = None) -> List[AuditLogEntity]:
        """
        Retrieves a paginated list of audit logs, with optional filters.
        Uses AuditLogRepository for data access.
        """
        try:
            actions_filter = None
            if action:
                # First try to treat action as a specific action name
                # Check if it's an exact action by looking for it in all categories
                from app.business.audit import AuditEventClassifier
                if action in AuditEventClassifier.EVENT_CLASSIFICATIONS:
                    # It's a specific action
                    actions_filter = [action]
                else:
                    # Try to treat it as a category name
                    actions_filter = AuditService._get_actions_by_category(action)
                    if not actions_filter: # If action is invalid or has no actions, return empty
                        return []
            
            start_dt: Optional[datetime] = None
            end_dt: Optional[datetime] = None
            if start_date:
                start_dt = datetime.fromisoformat(start_date)
            if end_date:
                end_dt = datetime.fromisoformat(end_date)

            # Severity filtering would require more complex logic if EVENT_CLASSIFICATIONS maps actions to severity
            # For now, severity filter is not directly implemented via repository unless actions_filter covers it.
            # If severity is critical, one might pre-filter actions_filter based on AuditManager.get_critical_events()
            
            return AuditLogRepository.get_logs(
                limit=-1, # No limit from repository, handled by page and per_page
                actions=actions_filter, 
                start_date=start_dt, 
                end_date=end_dt
            )
            
        except Exception as e:
            current_app.logger.error(f"Error retrieving audit logs from service: {str(e)}")
            return []
    
    @staticmethod
    def get_security_events(days: int = 7) -> List[AuditLogEntity]:
        """Get recent security-related audit events using AuditLogRepository."""
        security_actions = AuditService._get_actions_by_category("security_event")
        if not security_actions:
            return []
            
        start_dt = datetime.now(dt.UTC) - timedelta(days=days)
        
        return AuditLogRepository.get_logs(
            limit=-1, # No limit from repository, handled by days
            actions=security_actions,
            start_date=start_dt
        )
    
    @staticmethod
    def get_admin_activity(admin_id: int, days: int = 30) -> List[AuditLogEntity]:
        """Get recent admin activity using AuditLogRepository."""
        start_dt = datetime.now(dt.UTC) - timedelta(days=days)
        
        # The direct like query for admin_id in JSON is hard to replicate cleanly without JSON specific DB functions.
        # The AuditLog model now has admin_id directly. So we can filter by that.
        return AuditLogRepository.get_logs(
            limit=-1, # No limit
            admin_id=admin_id,
            start_date=start_dt
        )
    
    @staticmethod
    def cleanup_old_logs() -> Tuple[int, str]:
        """Clean up old audit logs based on retention policy using AuditLogRepository."""
        retention_policy = AuditManager.get_retention_policy()
        total_deleted_count = 0
        
        try:
            for category_name, retention_days in retention_policy.items():
                cutoff_date = datetime.now(dt.UTC) - timedelta(days=retention_days)
                category_actions = AuditService._get_actions_by_category(category_name)
                
                if category_actions:
                    deleted_for_category = AuditLogRepository.delete_logs_by_actions_and_older_than(
                        actions=category_actions,
                        cutoff_date=cutoff_date
                    )
                    total_deleted_count += deleted_for_category
            
            # No explicit db.session.commit() needed here as repo method handles it.
            
            AuditService.log_event("AUDIT_LOG_CLEANUP", {
                "deleted_count": total_deleted_count,
                "retention_policy": retention_policy
            })
            
            return total_deleted_count, f"Cleaned up {total_deleted_count} old audit logs"
            
        except Exception as e:
            # db.session.rollback() not needed as repo handles it.
            current_app.logger.error(f"Error during audit log cleanup in service: {str(e)}")
            return 0, f"Cleanup failed: {str(e)}"
    
    @staticmethod
    def get_audit_statistics(days: int = 30) -> Dict[str, Any]:
        """Get audit log statistics using AuditLogRepository."""
        start_dt = datetime.now(dt.UTC) - timedelta(days=days)
        now_dt = datetime.now(dt.UTC)

        total_events = AuditLogRepository.get_count_by_daterange(start_date=start_dt, end_date=now_dt)
        
        category_stats = {}
        for category_name in ["user_action", "admin_action", "security_event", "system_action", "error_event"]:
            category_actions = AuditService._get_actions_by_category(category_name)
            if category_actions:
                count = AuditLogRepository.get_count_by_actions_and_daterange(
                    actions=category_actions, 
                    start_date=start_dt, 
                    end_date=now_dt
                )
                category_stats[category_name] = count
        
        critical_actions = AuditManager.get_critical_events() # Assume this returns list of action strings
        critical_count = 0
        if critical_actions:
            critical_count = AuditLogRepository.get_count_by_actions_and_daterange(
                actions=critical_actions, 
                start_date=start_dt, 
                end_date=now_dt
            )
        
        return {
            "total_events": total_events,
            "category_breakdown": category_stats,
            "critical_events": critical_count,
            "period_days": days,
            "start_date": start_dt.isoformat(),
            "end_date": now_dt.isoformat()
        }
    
    @staticmethod
    def _get_user_context() -> Dict[str, Any]:
        """Extract simplified user context from current request/session"""
        context = {}
        
        try:
            # Get admin ID and username from session if available
            if 'admin_id' in session:
                context['admin_id'] = session['admin_id']
                context['admin_username'] = session.get('admin_username', 'UnknownAdmin')
                
        except RuntimeError:
            # Outside request context
            pass
            
        return context
    
    @staticmethod
    def _convert_to_persistence_model(audit_event: AuditEvent) -> AuditLogEntity:
        """Convert business audit event to persistence model"""
        # Serialize details to JSON
        try:
            details_json = json.dumps(audit_event.details)
        except (TypeError, ValueError) as e:
            # Fallback serialization
            details_json = json.dumps({
                "error": "Failed to serialize audit details",
                "original_error": str(e),
                "action": audit_event.action
            })
        
        return AuditLogEntity(
            action=audit_event.action,
            details=details_json,
            timestamp=audit_event.timestamp
        )
    
    @staticmethod
    def _get_actions_by_category(category_name: str) -> List[str]:
        """Get list of actions that belong to a specific category"""
        from app.business.audit import AuditEventClassifier, AuditEventCategory
        
        try:
            target_category = AuditEventCategory(category_name)
        except ValueError:
            return []
        
        return [
            action for action, (category, severity) in AuditEventClassifier.EVENT_CLASSIFICATIONS.items()
            if category == target_category
        ]

# Backward compatibility function
def log_audit_event(action: str, details: Dict[str, Any] = None) -> None:
    """Backward compatibility wrapper for the old log_audit_event function"""
    success, error = AuditService.log_event(action, details)
    if not success:
        current_app.logger.error(f"Audit logging failed: {error}") 