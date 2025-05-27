# Admin & Authentication domain business rules and logic
from dataclasses import dataclass
from typing import Optional
from datetime import datetime, timedelta
from enum import Enum
import bcrypt
import re

class AdminRole(Enum):
    """Admin roles supported by the system"""
    ADMIN = "admin"
    SUPER_ADMIN = "super_admin"
    MAINTENANCE = "maintenance"

@dataclass
class AdminSession:
    """Business object representing an admin session"""
    admin_id: int
    username: str
    role: AdminRole
    login_time: datetime
    last_activity: datetime
    
    def is_expired(self, max_session_duration_hours: int = 8) -> bool:
        """Check if session has expired based on business rules"""
        expiry_time = self.login_time + timedelta(hours=max_session_duration_hours)
        return datetime.utcnow() > expiry_time
    
    def is_inactive(self, max_inactive_minutes: int = 30) -> bool:
        """Check if session is inactive based on business rules"""
        inactive_threshold = self.last_activity + timedelta(minutes=max_inactive_minutes)
        return datetime.utcnow() > inactive_threshold

class AdminUser:
    """Business entity for admin users with authentication logic"""
    
    def __init__(self, id: Optional[int] = None, username: str = "", password_hash: str = "", role: AdminRole = AdminRole.ADMIN):
        self.id = id
        self.username = username
        self.password_hash = password_hash
        self.role = role
        self.created_at = datetime.utcnow() if id is None else None
        self.last_login = None
        
    def set_password(self, password: str) -> None:
        """Set password with business validation and hashing"""
        if not AdminAuthManager.validate_password_strength(password):
            raise ValueError("Password does not meet security requirements")
        
        password_bytes = password.encode('utf-8')
        salt = bcrypt.gensalt()
        self.password_hash = bcrypt.hashpw(password_bytes, salt).decode('utf-8')
    
    def check_password(self, password: str) -> bool:
        """Verify password against stored hash"""
        if not self.password_hash:
            return False
            
        password_bytes = password.encode('utf-8')
        stored_hash_bytes = self.password_hash.encode('utf-8')
        return bcrypt.checkpw(password_bytes, stored_hash_bytes)
    
    def can_perform_action(self, action: str) -> bool:
        """Check if admin can perform specific action based on role"""
        role_permissions = {
            AdminRole.ADMIN: [
                'view_parcels', 'mark_missing', 'reissue_pin', 'manage_lockers',
                'view_audit_logs', 'process_overdue'
            ],
            AdminRole.SUPER_ADMIN: [
                'view_parcels', 'mark_missing', 'reissue_pin', 'manage_lockers',
                'view_audit_logs', 'process_overdue', 'manage_admins', 'system_config'
            ],
            AdminRole.MAINTENANCE: [
                'manage_lockers', 'view_audit_logs'
            ]
        }
        return action in role_permissions.get(self.role, [])
    
    def update_last_login(self) -> None:
        """Update last login timestamp"""
        self.last_login = datetime.utcnow()

class AdminAuthManager:
    """Business logic for admin authentication and authorization"""
    
    # Password requirements as business rules
    MIN_PASSWORD_LENGTH = 8
    REQUIRE_UPPERCASE = True
    REQUIRE_LOWERCASE = True
    REQUIRE_NUMBERS = True
    REQUIRE_SPECIAL_CHARS = False
    
    @staticmethod
    def validate_username(username: str) -> bool:
        """Validate username according to business rules"""
        if not username or len(username) < 3:
            return False
        if len(username) > 50:
            return False
        if not re.match(r'^[a-zA-Z0-9_-]+$', username):
            return False
        return True
    
    @staticmethod
    def validate_password_strength(password: str) -> bool:
        """Validate password strength according to business rules"""
        if not password or len(password) < AdminAuthManager.MIN_PASSWORD_LENGTH:
            return False
        
        if AdminAuthManager.REQUIRE_UPPERCASE and not re.search(r'[A-Z]', password):
            return False
        
        if AdminAuthManager.REQUIRE_LOWERCASE and not re.search(r'[a-z]', password):
            return False
        
        if AdminAuthManager.REQUIRE_NUMBERS and not re.search(r'\d', password):
            return False
        
        if AdminAuthManager.REQUIRE_SPECIAL_CHARS and not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
            return False
        
        return True
    
    @staticmethod
    def create_session(admin_user: AdminUser) -> AdminSession:
        """Create new admin session"""
        return AdminSession(
            admin_id=admin_user.id,
            username=admin_user.username,
            role=admin_user.role,
            login_time=datetime.utcnow(),
            last_activity=datetime.utcnow()
        )
    
    @staticmethod
    def validate_login_attempt(username: str, password: str) -> dict:
        """Validate login attempt and return result details"""
        result = {
            'valid': False,
            'reason': None,
            'username_valid': False,
            'credentials_valid': False
        }
        
        # Username validation
        if not AdminAuthManager.validate_username(username):
            result['reason'] = 'Invalid username format'
            return result
        
        result['username_valid'] = True
        
        # Password format validation (basic check)
        if not password:
            result['reason'] = 'Password required'
            return result
        
        result['credentials_valid'] = True
        result['valid'] = True
        return result
    
    @staticmethod
    def get_failed_login_lockout_duration() -> int:
        """Get lockout duration in minutes for failed login attempts"""
        return 15  # Business rule: 15 minutes lockout
    
    @staticmethod
    def get_max_failed_attempts() -> int:
        """Get maximum failed login attempts before lockout"""
        return 5  # Business rule: 5 failed attempts 