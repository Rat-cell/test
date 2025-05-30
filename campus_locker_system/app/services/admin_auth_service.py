# Admin Authentication service - orchestration layer
from typing import Tuple, Optional, Dict, Any
from flask import current_app, session
from app import db
from app.business.admin_auth import AdminUser as BusinessAdminUser, AdminAuthManager, AdminSession, AdminRole
from app.persistence.models import AdminUser as PersistenceAdminUser
from app.services.audit_service import AuditService
from datetime import datetime
from werkzeug.security import check_password_hash

class AdminAuthService:
    """NFR-03: Security - Secure admin authentication with bcrypt hashing and audit logging"""
    
    @staticmethod
    def authenticate_admin(username: str, password: str) -> Tuple[Optional[BusinessAdminUser], str]:
        """NFR-03: Security - Secure admin authentication with password verification and audit logging"""
        try:
            # Validate login attempt format
            validation_result = AdminAuthManager.validate_login_attempt(username, password)
            if not validation_result['valid']:
                AuditService.log_event("ADMIN_LOGIN_FAIL", {
                    "username_attempted": username,
                    "reason": validation_result['reason']
                })
                return None, validation_result['reason']
            
            # Query persistence layer
            persistence_admin = PersistenceAdminUser.query.filter_by(username=username).first()
            
            if not persistence_admin:
                AuditService.log_event("ADMIN_LOGIN_FAIL", {
                    "username_attempted": username,
                    "reason": "User not found"
                })
                return None, "Invalid credentials"
            
            # Convert to business entity
            business_admin = AdminAuthService._convert_to_business_entity(persistence_admin)
            
            # Verify password
            if not business_admin.check_password(password):
                AuditService.log_event("ADMIN_LOGIN_FAIL", {
                    "username_attempted": username,
                    "reason": "Invalid password"
                })
                return None, "Invalid credentials"
            
            # Update last login
            business_admin.update_last_login()
            persistence_admin.last_login = business_admin.last_login
            db.session.commit()
            
            # Login successful - set session
            session['admin_id'] = business_admin.id
            session['admin_username'] = business_admin.username
            session.permanent = True
            
            # FR-07: Audit Trail - Record admin override action with timestamp and admin identity
            AuditService.log_event("ADMIN_LOGIN_SUCCESS", {
                "admin_id": business_admin.id,
                "admin_username": business_admin.username,
                "login_time": datetime.utcnow().isoformat()
            })
            
            return business_admin, "Authentication successful"
            
        except Exception as e:
            current_app.logger.error(f"Error during admin authentication: {str(e)}")
            # NFR-03: Security - Log authentication errors for security investigation
            AuditService.log_event("ADMIN_LOGIN_ERROR", details={
                "attempted_username": username,
                "error": str(e)
            })
            return None, "Authentication system error."
    
    @staticmethod
    def create_session(admin_user: BusinessAdminUser) -> AdminSession:
        """Create and store admin session"""
        admin_session = AdminAuthManager.create_session(admin_user)
        
        # Store session in Flask session
        session['admin_id'] = admin_session.admin_id
        session['admin_username'] = admin_session.username
        session['admin_role'] = admin_session.role.value
        session['login_time'] = admin_session.login_time.isoformat()
        session['last_activity'] = admin_session.last_activity.isoformat()
        
        return admin_session
    
    @staticmethod
    def get_current_session() -> Optional[AdminSession]:
        """Get current admin session from Flask session"""
        try:
            if 'admin_id' not in session:
                return None
            
            return AdminSession(
                admin_id=session['admin_id'],
                username=session['admin_username'],
                role=AdminRole(session['admin_role']),
                login_time=datetime.fromisoformat(session['login_time']),
                last_activity=datetime.fromisoformat(session['last_activity'])
            )
        except (KeyError, ValueError) as e:
            current_app.logger.warning(f"Invalid session data: {str(e)}")
            return None
    
    @staticmethod
    def validate_session() -> Tuple[bool, Optional[str]]:
        """Validate current session and return status"""
        admin_session = AdminAuthService.get_current_session()
        
        if not admin_session:
            return False, "No active session"
        
        if admin_session.is_expired():
            AdminAuthService.logout()
            return False, "Session expired"
        
        if admin_session.is_inactive():
            AdminAuthService.logout()
            return False, "Session inactive"
        
        # Update last activity
        AdminAuthService.update_session_activity()
        return True, None
    
    @staticmethod
    def update_session_activity() -> None:
        """Update last activity timestamp in session"""
        if 'admin_id' in session:
            session['last_activity'] = datetime.utcnow().isoformat()
    
    @staticmethod
    def logout() -> None:
        """Logout admin and clear session"""
        admin_id = session.get('admin_id')
        if admin_id:
            AuditService.log_event("ADMIN_LOGOUT", {"admin_id": admin_id})
        
        # Clear all admin-related session data
        session.pop('admin_id', None)
        session.pop('admin_username', None)
        session.pop('admin_role', None)
        session.pop('login_time', None)
        session.pop('last_activity', None)
    
    @staticmethod
    def check_permission(action: str) -> Tuple[bool, Optional[str]]:
        """Check if current admin has permission for action"""
        admin_session = AdminAuthService.get_current_session()
        
        if not admin_session:
            return False, "Not authenticated"
        
        # Get admin business entity to check permissions
        persistence_admin = db.session.get(PersistenceAdminUser, admin_session.admin_id)
        if not persistence_admin:
            return False, "Admin user not found"
        
        business_admin = AdminAuthService._convert_to_business_entity(persistence_admin)
        
        if not business_admin.can_perform_action(action):
            AuditService.log_event("ADMIN_PERMISSION_DENIED", {
                "admin_id": admin_session.admin_id,
                "action_attempted": action,
                "admin_role": admin_session.role.value
            })
            return False, f"Insufficient permissions for action: {action}"
        
        return True, None
    
    @staticmethod
    def create_admin_user(username: str, password: str, role: AdminRole = AdminRole.ADMIN) -> Tuple[Optional[BusinessAdminUser], str]:
        """Create new admin user"""
        try:
            # Validate username
            if not AdminAuthManager.validate_username(username):
                return None, "Invalid username format"
            
            # Check if username already exists
            if PersistenceAdminUser.query.filter_by(username=username).first():
                return None, "Username already exists"
            
            # Create business entity
            business_admin = BusinessAdminUser(username=username, role=role)
            business_admin.set_password(password)  # Will validate password strength
            
            # Create persistence entity
            persistence_admin = PersistenceAdminUser(
                username=business_admin.username,
                password_hash=business_admin.password_hash
            )
            
            db.session.add(persistence_admin)
            db.session.commit()
            
            # Update business entity with generated ID
            business_admin.id = persistence_admin.id
            
            AuditService.log_event("ADMIN_USER_CREATED", {
                "admin_id": business_admin.id,
                "username": business_admin.username,
                "role": business_admin.role.value,
                "created_by": session.get('admin_id', 'system')
            })
            
            return business_admin, "Admin user created successfully"
            
        except ValueError as e:
            return None, str(e)
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Error creating admin user: {str(e)}")
            return None, "Error creating admin user"
    
    @staticmethod
    def _convert_to_business_entity(persistence_admin: PersistenceAdminUser) -> BusinessAdminUser:
        """Convert persistence model to business entity"""
        # Default role handling for existing admins without roles
        role = AdminRole.ADMIN  # Default for backward compatibility
        
        return BusinessAdminUser(
            id=persistence_admin.id,
            username=persistence_admin.username,
            password_hash=persistence_admin.password_hash,
            role=role
        ) 