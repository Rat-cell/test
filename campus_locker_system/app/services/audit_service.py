# Audit service - orchestration layer
from typing import Tuple, Optional, List, Dict, Any
from flask import current_app, session, request
from app.business.audit import AuditManager, AuditEvent, AuditEventCategory, AuditEventSeverity
from app.persistence.models import AuditLog
from app.adapters.audit_adapter import create_audit_adapter
import json

class AuditService:
    """Service layer for audit logging orchestration"""
    
    @staticmethod
    def log_event(action: str, details: Dict[str, Any] = None) -> Tuple[bool, Optional[str]]:
        """Log an audit event using business rules"""
        try:
            # Get user context
            user_context = AuditService._get_user_context()
            
            # Create audit event using business logic
            audit_event = AuditManager.create_audit_event(action, details, user_context)
            
            # Use audit adapter to store the event
            audit_adapter = create_audit_adapter()
            success, message = audit_adapter.store_audit_event(
                action=audit_event.action,
                details=audit_event.details
            )
            
            if not success:
                current_app.logger.error(f"AUDIT LOGGING ERROR: {message}")
                return False, message
            
            # Log critical events to application logger
            if audit_event.severity == AuditEventSeverity.CRITICAL:
                current_app.logger.critical(f"CRITICAL AUDIT EVENT: {action} - {details}")
            
            return True, None
            
        except ValueError as e:
            # Business validation error
            current_app.logger.error(f"AUDIT EVENT VALIDATION ERROR: {str(e)} for action '{action}'")
            return False, str(e)
        except Exception as e:
            # Unexpected error
            current_app.logger.error(f"AUDIT LOGGING ERROR: Failed to log audit event for action '{action}'. Error: {e}")
            return False, f"Failed to log audit event: {str(e)}"
    
    @staticmethod
    def get_audit_logs(limit: int = 100, category: Optional[str] = None, 
                      severity: Optional[str] = None, start_date: Optional[str] = None,
                      end_date: Optional[str] = None) -> List[AuditLog]:
        """Retrieve audit logs with filtering"""
        try:
            # Use audit adapter for basic retrieval
            audit_adapter = create_audit_adapter()
            
            # For now, use the adapter's simple methods
            # Future enhancement: add filtering to adapter interface
            if start_date and end_date:
                from datetime import datetime
                start_dt = datetime.fromisoformat(start_date)
                end_dt = datetime.fromisoformat(end_date)
                logs = audit_adapter.get_logs_by_timerange(start_dt, end_dt)
            else:
                logs = audit_adapter.get_audit_logs(limit=limit)
            
            # Apply additional filtering in memory for now
            # TODO: Move this filtering logic to the adapter layer
            if category:
                category_actions = AuditService._get_actions_by_category(category)
                if category_actions:
                    logs = [log for log in logs if getattr(log, 'action', log.get('action', '')) in category_actions]
            
            return logs[:limit] if logs else []
            
        except Exception as e:
            current_app.logger.error(f"Error retrieving audit logs: {str(e)}")
            return []
    
    @staticmethod
    def get_security_events(days: int = 7) -> List[AuditLog]:
        """Get recent security-related audit events"""
        from datetime import datetime, timedelta
        
        # Get security event actions
        security_actions = AuditService._get_actions_by_category("security_event")
        
        start_date = datetime.utcnow() - timedelta(days=days)
        
        logs = AuditLog.query.filter(
            AuditLog.action.in_(security_actions),
            AuditLog.timestamp >= start_date
        ).order_by(AuditLog.timestamp.desc()).all()
        
        return logs
    
    @staticmethod
    def get_admin_activity(admin_id: int, days: int = 30) -> List[AuditLog]:
        """Get recent admin activity"""
        from datetime import datetime, timedelta
        
        start_date = datetime.utcnow() - timedelta(days=days)
        
        # Look for admin_id in the details JSON
        logs = AuditLog.query.filter(
            AuditLog.timestamp >= start_date,
            AuditLog.details.like(f'%"admin_id": {admin_id}%')
        ).order_by(AuditLog.timestamp.desc()).all()
        
        return logs
    
    @staticmethod
    def cleanup_old_logs() -> Tuple[int, str]:
        """Clean up old audit logs based on retention policy"""
        from datetime import datetime, timedelta
        
        retention_policy = AuditManager.get_retention_policy()
        deleted_count = 0
        
        try:
            for category_name, retention_days in retention_policy.items():
                cutoff_date = datetime.utcnow() - timedelta(days=retention_days)
                
                # Get actions for this category
                category_actions = AuditService._get_actions_by_category(category_name)
                
                if category_actions:
                    # Delete old logs for this category
                    result = AuditLog.query.filter(
                        AuditLog.action.in_(category_actions),
                        AuditLog.timestamp < cutoff_date
                    ).delete(synchronize_session=False)
                    
                    deleted_count += result
            
            db.session.commit()
            
            # Log the cleanup
            AuditService.log_event("AUDIT_LOG_CLEANUP", {
                "deleted_count": deleted_count,
                "retention_policy": retention_policy
            })
            
            return deleted_count, f"Cleaned up {deleted_count} old audit logs"
            
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Error during audit log cleanup: {str(e)}")
            return 0, f"Cleanup failed: {str(e)}"
    
    @staticmethod
    def get_audit_statistics(days: int = 30) -> Dict[str, Any]:
        """Get audit log statistics"""
        from datetime import datetime, timedelta
        
        start_date = datetime.utcnow() - timedelta(days=days)
        
        # Total events
        total_events = AuditLog.query.filter(AuditLog.timestamp >= start_date).count()
        
        # Events by category (approximate based on action patterns)
        category_stats = {}
        for category_name in ["user_action", "admin_action", "security_event", "system_action", "error_event"]:
            category_actions = AuditService._get_actions_by_category(category_name)
            if category_actions:
                count = AuditLog.query.filter(
                    AuditLog.action.in_(category_actions),
                    AuditLog.timestamp >= start_date
                ).count()
                category_stats[category_name] = count
        
        # Recent critical events
        critical_actions = AuditManager.get_critical_events()
        critical_count = AuditLog.query.filter(
            AuditLog.action.in_(critical_actions),
            AuditLog.timestamp >= start_date
        ).count()
        
        return {
            "total_events": total_events,
            "category_breakdown": category_stats,
            "critical_events": critical_count,
            "period_days": days,
            "start_date": start_date.isoformat(),
            "end_date": datetime.utcnow().isoformat()
        }
    
    @staticmethod
    def _get_user_context() -> Dict[str, Any]:
        """Extract user context from current request/session"""
        context = {}
        
        try:
            # Get admin ID from session if available
            if 'admin_id' in session:
                context['admin_id'] = session['admin_id']
        except RuntimeError:
            # Working outside of request context (e.g., in tests)
            pass
        
        try:
            # Get IP address from request if available
            if request:
                context['ip_address'] = request.remote_addr
                context['session_id'] = session.get('_id', 'unknown')
        except RuntimeError:
            # Working outside of request context (e.g., in tests)
            pass
        
        return context
    
    @staticmethod
    def _convert_to_persistence_model(audit_event: AuditEvent) -> AuditLog:
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
        
        return AuditLog(
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