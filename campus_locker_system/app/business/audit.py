# Audit Logging domain business rules and logic
from dataclasses import dataclass
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
from enum import Enum
import json

class AuditEventCategory(Enum):
    """Categories of audit events for business classification"""
    USER_ACTION = "user_action"
    ADMIN_ACTION = "admin_action" 
    SYSTEM_ACTION = "system_action"
    SECURITY_EVENT = "security_event"
    ERROR_EVENT = "error_event"

class AuditEventSeverity(Enum):
    """Severity levels for audit events"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

@dataclass
class AuditEvent:
    """Business object representing an audit event"""
    action: str
    details: Dict[str, Any]
    category: AuditEventCategory
    severity: AuditEventSeverity
    timestamp: datetime
    session_id: Optional[str] = None
    user_id: Optional[int] = None
    admin_id: Optional[int] = None
    ip_address: Optional[str] = None
    
    def __post_init__(self):
        """Validate audit event after creation"""
        if not self.action:
            raise ValueError("Audit event action cannot be empty")
        if not isinstance(self.details, dict):
            raise ValueError("Audit event details must be a dictionary")

class AuditEventClassifier:
    """Business logic for classifying audit events"""
    
    # Event classification rules
    EVENT_CLASSIFICATIONS = {
        # User Actions
        "USER_DEPOSIT": (AuditEventCategory.USER_ACTION, AuditEventSeverity.LOW),
        "USER_PICKUP": (AuditEventCategory.USER_ACTION, AuditEventSeverity.LOW),
        "USER_PICKUP_FAIL": (AuditEventCategory.USER_ACTION, AuditEventSeverity.MEDIUM),
        "USER_DEPOSIT_RETRACTED": (AuditEventCategory.USER_ACTION, AuditEventSeverity.MEDIUM),
        "USER_PICKUP_DISPUTED": (AuditEventCategory.USER_ACTION, AuditEventSeverity.HIGH),
        "PARCEL_REPORTED_MISSING_BY_RECIPIENT": (AuditEventCategory.USER_ACTION, AuditEventSeverity.HIGH),
        
        # Admin Actions
        "ADMIN_LOGIN_SUCCESS": (AuditEventCategory.ADMIN_ACTION, AuditEventSeverity.MEDIUM),
        "ADMIN_LOGIN_FAIL": (AuditEventCategory.SECURITY_EVENT, AuditEventSeverity.HIGH),
        "ADMIN_LOGOUT": (AuditEventCategory.ADMIN_ACTION, AuditEventSeverity.LOW),
        "ADMIN_LOCKER_STATUS_CHANGED": (AuditEventCategory.ADMIN_ACTION, AuditEventSeverity.MEDIUM),
        "ADMIN_MARKED_PARCEL_MISSING": (AuditEventCategory.ADMIN_ACTION, AuditEventSeverity.HIGH),
        "ADMIN_PERMISSION_DENIED": (AuditEventCategory.SECURITY_EVENT, AuditEventSeverity.HIGH),
        "ADMIN_USER_CREATED": (AuditEventCategory.ADMIN_ACTION, AuditEventSeverity.HIGH),
        
        # System Actions
        "PARCEL_MARKED_RETURN_TO_SENDER": (AuditEventCategory.SYSTEM_ACTION, AuditEventSeverity.MEDIUM),
        "LOCKER_MARKED_EMPTIED_AFTER_RETURN": (AuditEventCategory.SYSTEM_ACTION, AuditEventSeverity.LOW),
        "NOTIFICATION_SENT": (AuditEventCategory.SYSTEM_ACTION, AuditEventSeverity.LOW),
        
        # Security Events
        "USER_PICKUP_FAIL_INVALID_PIN": (AuditEventCategory.SECURITY_EVENT, AuditEventSeverity.HIGH),
        "USER_PICKUP_FAIL_PIN_EXPIRED": (AuditEventCategory.SECURITY_EVENT, AuditEventSeverity.MEDIUM),
        
        # Error Events
        "PROCESS_OVERDUE_FAIL": (AuditEventCategory.ERROR_EVENT, AuditEventSeverity.MEDIUM),
        "PROCESS_OVERDUE_PARCEL_ERROR": (AuditEventCategory.ERROR_EVENT, AuditEventSeverity.HIGH),
        "PROCESS_OVERDUE_BATCH_COMMIT_ERROR": (AuditEventCategory.ERROR_EVENT, AuditEventSeverity.CRITICAL),
        "MARK_LOCKER_EMPTIED_FAIL": (AuditEventCategory.ERROR_EVENT, AuditEventSeverity.MEDIUM),
        "MARK_LOCKER_EMPTIED_ERROR": (AuditEventCategory.ERROR_EVENT, AuditEventSeverity.HIGH),
    }
    
    @staticmethod
    def classify_event(action: str) -> tuple[AuditEventCategory, AuditEventSeverity]:
        """Classify an audit event based on its action"""
        # Check for exact matches first
        if action in AuditEventClassifier.EVENT_CLASSIFICATIONS:
            return AuditEventClassifier.EVENT_CLASSIFICATIONS[action]
        
        # Pattern-based classification for dynamic events
        action_upper = action.upper()
        
        if any(pattern in action_upper for pattern in ["LOGIN", "LOGOUT", "AUTH", "PERMISSION"]):
            return (AuditEventCategory.SECURITY_EVENT, AuditEventSeverity.HIGH)
        elif any(pattern in action_upper for pattern in ["ADMIN_", "ADMIN "]):
            return (AuditEventCategory.ADMIN_ACTION, AuditEventSeverity.MEDIUM)
        elif any(pattern in action_upper for pattern in ["USER_", "USER "]):
            return (AuditEventCategory.USER_ACTION, AuditEventSeverity.LOW)
        elif any(pattern in action_upper for pattern in ["ERROR", "FAIL", "EXCEPTION"]):
            return (AuditEventCategory.ERROR_EVENT, AuditEventSeverity.HIGH)
        elif any(pattern in action_upper for pattern in ["SYSTEM", "PROCESS", "BATCH"]):
            return (AuditEventCategory.SYSTEM_ACTION, AuditEventSeverity.MEDIUM)
        else:
            # Default classification
            return (AuditEventCategory.USER_ACTION, AuditEventSeverity.LOW)

class AuditEventValidator:
    """Business logic for validating audit events"""
    
    MAX_ACTION_LENGTH = 255
    MAX_DETAILS_SIZE = 10000  # Characters
    REQUIRED_FIELDS_BY_CATEGORY = {
        AuditEventCategory.USER_ACTION: [],
        AuditEventCategory.ADMIN_ACTION: ["admin_id"],
        AuditEventCategory.SECURITY_EVENT: [],
        AuditEventCategory.SYSTEM_ACTION: [],
        AuditEventCategory.ERROR_EVENT: ["error"],
    }
    
    @staticmethod
    def validate_action(action: str) -> bool:
        """Validate audit action format"""
        if not action or not isinstance(action, str):
            return False
        if len(action) > AuditEventValidator.MAX_ACTION_LENGTH:
            return False
        # Action should be alphanumeric with underscores and spaces
        return action.replace('_', '').replace(' ', '').replace('-', '').isalnum()
    
    @staticmethod
    def validate_details(details: Dict[str, Any]) -> tuple[bool, Optional[str]]:
        """Validate audit details"""
        if not isinstance(details, dict):
            return False, "Details must be a dictionary"
        
        # Check serialization
        try:
            serialized = json.dumps(details)
            if len(serialized) > AuditEventValidator.MAX_DETAILS_SIZE:
                return False, "Details too large when serialized"
        except (TypeError, ValueError) as e:
            return False, f"Details not JSON serializable: {str(e)}"
        
        return True, None
    
    @staticmethod
    def validate_required_fields(event: AuditEvent) -> tuple[bool, Optional[str]]:
        """Validate required fields based on event category"""
        required_fields = AuditEventValidator.REQUIRED_FIELDS_BY_CATEGORY.get(event.category, [])
        
        for field in required_fields:
            if field not in event.details:
                return False, f"Required field '{field}' missing for {event.category.value} events"
        
        return True, None

class AuditManager:
    """Business logic for audit event management"""
    
    @staticmethod
    def create_audit_event(action: str, details: Dict[str, Any] = None, 
                          user_context: Dict[str, Any] = None) -> AuditEvent:
        """Create a new audit event with proper classification and validation"""
        if details is None:
            details = {}
        if user_context is None:
            user_context = {}
        
        # Validate action
        if not AuditEventValidator.validate_action(action):
            raise ValueError(f"Invalid audit action: {action}")
        
        # Validate details
        is_valid, error_msg = AuditEventValidator.validate_details(details)
        if not is_valid:
            raise ValueError(f"Invalid audit details: {error_msg}")
        
        # Classify event
        category, severity = AuditEventClassifier.classify_event(action)
        
        # Create event
        event = AuditEvent(
            action=action,
            details=details,
            category=category,
            severity=severity,
            timestamp=datetime.utcnow(),
            session_id=user_context.get('session_id'),
            user_id=user_context.get('user_id'),
            admin_id=user_context.get('admin_id'),
            ip_address=user_context.get('ip_address')
        )
        
        # Validate required fields
        is_valid, error_msg = AuditEventValidator.validate_required_fields(event)
        if not is_valid:
            # For missing required fields, add a warning to details instead of failing
            event.details['_validation_warning'] = error_msg
        
        return event
    
    @staticmethod
    def get_retention_policy() -> Dict[str, int]:
        """Get audit log retention policy in days"""
        return {
            AuditEventCategory.USER_ACTION.value: 90,     # 3 months
            AuditEventCategory.ADMIN_ACTION.value: 365,   # 1 year  
            AuditEventCategory.SECURITY_EVENT.value: 730, # 2 years
            AuditEventCategory.SYSTEM_ACTION.value: 30,   # 1 month
            AuditEventCategory.ERROR_EVENT.value: 180,    # 6 months
        }
    
    @staticmethod
    def should_retain_event(event: AuditEvent) -> bool:
        """Check if an audit event should be retained based on retention policy"""
        retention_policy = AuditManager.get_retention_policy()
        retention_days = retention_policy.get(event.category.value, 90)  # Default 90 days
        
        cutoff_date = datetime.utcnow() - timedelta(days=retention_days)
        return event.timestamp > cutoff_date
    
    @staticmethod
    def get_critical_events() -> List[str]:
        """Get list of actions that are considered critical events"""
        return [
            action for action, (category, severity) in AuditEventClassifier.EVENT_CLASSIFICATIONS.items()
            if severity == AuditEventSeverity.CRITICAL
        ] 