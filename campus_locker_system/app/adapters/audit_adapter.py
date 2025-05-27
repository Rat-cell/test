"""
Audit Adapter - Audit logging persistence interface and implementation

This adapter provides a clean interface for storing audit events,
abstracting away database implementation details from the audit service.
"""
from abc import ABC, abstractmethod
from typing import List, Optional, Tuple, Dict, Any
from datetime import datetime, timedelta
from flask import current_app
from app.persistence.models import AuditLog
import json


class AuditAdapterInterface(ABC):
    """Interface for audit adapters - defines the contract"""
    
    @abstractmethod
    def store_audit_event(self, action: str, details: Dict[str, Any]) -> Tuple[bool, str]:
        """Store an audit event"""
        pass
    
    @abstractmethod
    def get_audit_logs(self, limit: Optional[int] = None, offset: int = 0) -> List[Any]:
        """Retrieve audit logs with pagination"""
        pass
    
    @abstractmethod
    def get_logs_by_action(self, action: str, limit: Optional[int] = None) -> List[Any]:
        """Get logs filtered by action type"""
        pass
    
    @abstractmethod
    def get_logs_by_timerange(self, start_time: datetime, end_time: datetime) -> List[Any]:
        """Get logs within a time range"""
        pass
    
    @abstractmethod
    def cleanup_old_logs(self, retention_days: int) -> Tuple[int, str]:
        """Clean up old logs based on retention policy"""
        pass
    
    @abstractmethod
    def get_audit_statistics(self) -> Dict[str, Any]:
        """Get audit statistics"""
        pass


class SQLAlchemyAuditAdapter(AuditAdapterInterface):
    """SQLAlchemy implementation of the audit adapter"""
    
    def store_audit_event(self, action: str, details: Dict[str, Any]) -> Tuple[bool, str]:
        """Store audit event using SQLAlchemy"""
        try:
            from app import db  # Import here to avoid circular imports
            
            # Serialize details to JSON
            details_json = json.dumps(details) if details else "{}"
            
            # Create audit log entry
            audit_log = AuditLog(
                action=action,
                details=details_json,
                timestamp=datetime.utcnow()
            )
            
            # Save to database
            db.session.add(audit_log)
            db.session.commit()
            
            return True, f"Audit event '{action}' stored successfully"
            
        except Exception as e:
            try:
                from app import db
                db.session.rollback()
            except:
                pass
            error_msg = f"Error storing audit event '{action}': {str(e)}"
            current_app.logger.error(error_msg)
            return False, error_msg
    
    def get_audit_logs(self, limit: Optional[int] = None, offset: int = 0) -> List[AuditLog]:
        """Get audit logs with pagination"""
        try:
            query = AuditLog.query.order_by(AuditLog.timestamp.desc())
            
            if offset:
                query = query.offset(offset)
            
            if limit:
                query = query.limit(limit)
            
            return query.all()
            
        except Exception as e:
            current_app.logger.error(f"Error retrieving audit logs: {str(e)}")
            return []
    
    def get_logs_by_action(self, action: str, limit: Optional[int] = None) -> List[AuditLog]:
        """Get logs filtered by action type"""
        try:
            query = AuditLog.query.filter_by(action=action).order_by(AuditLog.timestamp.desc())
            
            if limit:
                query = query.limit(limit)
            
            return query.all()
            
        except Exception as e:
            current_app.logger.error(f"Error retrieving logs for action '{action}': {str(e)}")
            return []
    
    def get_logs_by_timerange(self, start_time: datetime, end_time: datetime) -> List[AuditLog]:
        """Get logs within a time range"""
        try:
            return AuditLog.query.filter(
                AuditLog.timestamp >= start_time,
                AuditLog.timestamp <= end_time
            ).order_by(AuditLog.timestamp.desc()).all()
            
        except Exception as e:
            current_app.logger.error(f"Error retrieving logs for timerange: {str(e)}")
            return []
    
    def cleanup_old_logs(self, retention_days: int) -> Tuple[int, str]:
        """Clean up old logs based on retention policy"""
        try:
            from app import db  # Import here to avoid circular imports
            
            cutoff_date = datetime.utcnow() - timedelta(days=retention_days)
            
            # Count logs to be deleted
            old_logs_count = AuditLog.query.filter(AuditLog.timestamp < cutoff_date).count()
            
            # Delete old logs
            deleted = AuditLog.query.filter(AuditLog.timestamp < cutoff_date).delete()
            db.session.commit()
            
            return deleted, f"Cleaned up {deleted} audit logs older than {retention_days} days"
            
        except Exception as e:
            try:
                from app import db
                db.session.rollback()
            except:
                pass
            error_msg = f"Error cleaning up old audit logs: {str(e)}"
            current_app.logger.error(error_msg)
            return 0, error_msg
    
    def get_audit_statistics(self) -> Dict[str, Any]:
        """Get audit statistics"""
        try:
            from app import db  # Import here to avoid circular imports
            
            total_logs = AuditLog.query.count()
            
            # Get logs from last 24 hours
            last_24h = datetime.utcnow() - timedelta(hours=24)
            recent_logs = AuditLog.query.filter(AuditLog.timestamp >= last_24h).count()
            
            # Get most common actions (top 10)
            from sqlalchemy import func
            action_counts = db.session.query(
                AuditLog.action,
                func.count(AuditLog.action).label('count')
            ).group_by(AuditLog.action).order_by(func.count(AuditLog.action).desc()).limit(10).all()
            
            # Get oldest and newest log timestamps
            oldest_log = AuditLog.query.order_by(AuditLog.timestamp.asc()).first()
            newest_log = AuditLog.query.order_by(AuditLog.timestamp.desc()).first()
            
            return {
                'total_logs': total_logs,
                'recent_logs_24h': recent_logs,
                'top_actions': [{'action': action, 'count': count} for action, count in action_counts],
                'oldest_log_date': oldest_log.timestamp if oldest_log else None,
                'newest_log_date': newest_log.timestamp if newest_log else None
            }
            
        except Exception as e:
            current_app.logger.error(f"Error getting audit statistics: {str(e)}")
            return {
                'total_logs': 0,
                'recent_logs_24h': 0,
                'top_actions': [],
                'oldest_log_date': None,
                'newest_log_date': None,
                'error': str(e)
            }


class MockAuditAdapter(AuditAdapterInterface):
    """Mock audit adapter for testing - stores events in memory"""
    
    def __init__(self):
        self.audit_events = []
        self.next_id = 1
    
    def store_audit_event(self, action: str, details: Dict[str, Any]) -> Tuple[bool, str]:
        """Mock store audit event"""
        event = {
            'id': self.next_id,
            'action': action,
            'details': details,
            'timestamp': datetime.utcnow()
        }
        self.audit_events.append(event)
        self.next_id += 1
        return True, f"Mock audit event '{action}' stored"
    
    def get_audit_logs(self, limit: Optional[int] = None, offset: int = 0) -> List[Dict[str, Any]]:
        """Mock get audit logs"""
        # Sort by timestamp descending
        sorted_events = sorted(self.audit_events, key=lambda x: x['timestamp'], reverse=True)
        
        # Apply offset and limit
        if offset:
            sorted_events = sorted_events[offset:]
        if limit:
            sorted_events = sorted_events[:limit]
        
        return sorted_events
    
    def get_logs_by_action(self, action: str, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """Mock get logs by action"""
        filtered = [event for event in self.audit_events if event['action'] == action]
        filtered.sort(key=lambda x: x['timestamp'], reverse=True)
        
        if limit:
            filtered = filtered[:limit]
        
        return filtered
    
    def get_logs_by_timerange(self, start_time: datetime, end_time: datetime) -> List[Dict[str, Any]]:
        """Mock get logs by timerange"""
        filtered = [
            event for event in self.audit_events 
            if start_time <= event['timestamp'] <= end_time
        ]
        filtered.sort(key=lambda x: x['timestamp'], reverse=True)
        return filtered
    
    def cleanup_old_logs(self, retention_days: int) -> Tuple[int, str]:
        """Mock cleanup old logs"""
        cutoff_date = datetime.utcnow() - timedelta(days=retention_days)
        original_count = len(self.audit_events)
        
        # Remove old events
        self.audit_events = [
            event for event in self.audit_events 
            if event['timestamp'] >= cutoff_date
        ]
        
        deleted_count = original_count - len(self.audit_events)
        return deleted_count, f"Mock cleaned up {deleted_count} events"
    
    def get_audit_statistics(self) -> Dict[str, Any]:
        """Mock get audit statistics"""
        if not self.audit_events:
            return {
                'total_logs': 0,
                'recent_logs_24h': 0,
                'top_actions': [],
                'oldest_log_date': None,
                'newest_log_date': None
            }
        
        # Count by action
        action_counts = {}
        last_24h = datetime.utcnow() - timedelta(hours=24)
        recent_count = 0
        
        for event in self.audit_events:
            action = event['action']
            action_counts[action] = action_counts.get(action, 0) + 1
            
            if event['timestamp'] >= last_24h:
                recent_count += 1
        
        # Sort by count
        top_actions = [
            {'action': action, 'count': count} 
            for action, count in sorted(action_counts.items(), key=lambda x: x[1], reverse=True)[:10]
        ]
        
        # Get oldest and newest
        timestamps = [event['timestamp'] for event in self.audit_events]
        
        return {
            'total_logs': len(self.audit_events),
            'recent_logs_24h': recent_count,
            'top_actions': top_actions,
            'oldest_log_date': min(timestamps) if timestamps else None,
            'newest_log_date': max(timestamps) if timestamps else None
        }
    
    def clear_events(self):
        """Clear stored events (for testing)"""
        self.audit_events.clear()
        self.next_id = 1


# Factory function to create appropriate adapter
def create_audit_adapter() -> AuditAdapterInterface:
    """Factory to create the appropriate audit adapter based on configuration"""
    # For now, always use SQLAlchemy adapter to maintain compatibility with existing tests
    # In a future version, we can add a specific config flag to enable mock adapters
    return SQLAlchemyAuditAdapter() 