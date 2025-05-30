from functools import wraps
from flask import session, redirect, url_for, flash

def admin_required(f):
    """NFR-03: Security - Authentication decorator to protect admin routes"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        from app.services.admin_auth_service import AdminAuthService
        
        # NFR-03: Security - Validate admin session before allowing access
        is_valid, error_message = AdminAuthService.validate_session()
        if not is_valid:
            print(f"DEBUG: admin_required - session validation failed: {error_message}")
            flash('Please log in to access this page.', 'warning')
            return redirect(url_for('main.admin_login'))
        
        return f(*args, **kwargs)
    return decorated_function
