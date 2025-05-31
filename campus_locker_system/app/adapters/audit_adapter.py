"""
Audit Adapter - Audit logging persistence interface and implementation

This adapter provided a clean interface for storing audit events,
abstracting away database implementation details from the audit service.
This file now primarily contains the MockAuditAdapter for testing purposes,
_as the SQLAlchemy-based persistence is handled by AuditLogRepository._
"""
from abc import ABC, abstractmethod
from typing import List, Optional, Tuple, Dict, Any
from datetime import datetime, timedelta # timedelta is not used directly here anymore but kept for context
import datetime as dt
from flask import current_app # current_app is not used by MockAuditAdapter but good to keep for file context
# from app.persistence.models import AuditLog # Not needed by MockAuditAdapter
# import json # Not needed by MockAuditAdapter


class AuditAdapterInterface(ABC):
    """Interface for audit adapters - defines the contract
       Still used by MockAuditAdapter.
    """
    
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
        pass # pragma: no cover


# SQLAlchemyAuditAdapter class has been removed as its functionality is now in AuditLogRepository.
# The _classify_event_category and _classify_event_severity methods were part of it and are also removed.


class MockAuditAdapter(AuditAdapterInterface):
    """Mock audit adapter for testing - stores events in memory"""
    
    def __init__(self):
        self.audit_events: List[Dict[str, Any]] = [] # Type hint for clarity
        self.next_id: int = 1 # Type hint
    
    def store_audit_event(self, action: str, details: Dict[str, Any]) -> Tuple[bool, str]:
        """Mock store audit event"""
        event: Dict[str, Any] = { # Type hint
            'id': self.next_id,
            'action': action,
            'details': details,
            'timestamp': datetime.now(dt.UTC)
        }
        self.audit_events.append(event)
        self.next_id += 1
        return True, f"Mock audit event '{action}' stored"
    
    def get_audit_logs(self, limit: Optional[int] = None, offset: int = 0) -> List[Dict[str, Any]]:
        """Mock get audit logs"""
        sorted_events = sorted(self.audit_events, key=lambda x: x['timestamp'], reverse=True)
        
        if offset:
            sorted_events = sorted_events[offset:]
        if limit is not None and limit >= 0: # Ensure limit is not None and non-negative
            sorted_events = sorted_events[:limit]
        return sorted_events
    
    def get_logs_by_action(self, action: str, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """Mock get logs filtered by action type"""
        filtered_events = [event for event in self.audit_events if event['action'] == action]
        sorted_events = sorted(filtered_events, key=lambda x: x['timestamp'], reverse=True)
        if limit is not None and limit >= 0:
            sorted_events = sorted_events[:limit]
        return sorted_events
    
    def get_logs_by_timerange(self, start_time: datetime, end_time: datetime) -> List[Dict[str, Any]]:
        """Mock get logs within a time range"""
        filtered_events = [event for event in self.audit_events if start_time <= event['timestamp'] <= end_time]
        return sorted(filtered_events, key=lambda x: x['timestamp'], reverse=True)
    
    def cleanup_old_logs(self, retention_days: int) -> Tuple[int, str]:
        """Mock clean up old logs based on retention policy"""
        cutoff_date = datetime.now(dt.UTC) - timedelta(days=retention_days)
        original_count = len(self.audit_events)
        self.audit_events = [event for event in self.audit_events if event['timestamp'] >= cutoff_date]
        deleted_count = original_count - len(self.audit_events)
        return deleted_count, f"Mock cleaned up {deleted_count} audit logs older than {retention_days} days"
    
    def get_audit_statistics(self) -> Dict[str, Any]:
        """Mock get audit statistics"""
        total_logs = len(self.audit_events)
        recent_logs_24h = 0
        if total_logs > 0:
            last_24h = datetime.now(dt.UTC) - timedelta(hours=24)
            recent_logs_24h = len([event for event in self.audit_events if event['timestamp'] >= last_24h])
        
        action_counts_dict: Dict[str, int] = {}
        for event in self.audit_events:
            action_counts_dict[event['action']] = action_counts_dict.get(event['action'], 0) + 1
        
        top_actions = sorted(action_counts_dict.items(), key=lambda item: item[1], reverse=True)[:10]
        
        oldest_log_date = min(event['timestamp'] for event in self.audit_events) if self.audit_events else None
        newest_log_date = max(event['timestamp'] for event in self.audit_events) if self.audit_events else None
        
        return {
            'total_logs': total_logs,
            'recent_logs_24h': recent_logs_24h,
            'top_actions': [{'action': action, 'count': count} for action, count in top_actions],
            'oldest_log_date': oldest_log_date,
            'newest_log_date': newest_log_date
        }

    def clear_events(self):
        """Clears all mock events. Useful for test setup."""
        self.audit_events = []
        self.next_id = 1

# create_audit_adapter function has been removed as SQLAlchemyAuditAdapter is removed.
# Application should use AuditService which relies on AuditLogRepository.
# For testing, MockAuditAdapter can be instantiated directly. 