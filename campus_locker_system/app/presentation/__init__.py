from flask import Blueprint

# Use a more descriptive name like 'main_bp' or 'deposit_bp' if only for deposit for now
# For broader use, 'main_bp' is fine. Let's use 'main_bp'.
main_bp = Blueprint('main', __name__, template_folder='templates')

from . import routes # Import routes after blueprint creation to avoid circular imports
