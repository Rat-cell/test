from functools import wraps
from flask import session, redirect, url_for, flash

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'admin_id' not in session:
            print("DEBUG: admin_required - not logged in, redirecting to login")
            flash('Please log in to access this page.', 'warning')
            return redirect(url_for('main.admin_login')) # Assuming 'main' is the blueprint name
        return f(*args, **kwargs)
    return decorated_function
