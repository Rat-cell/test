# create_admin.py (in campus_locker_system root)
from app import create_app, db
from app.persistence.models import AdminUser
import sys

def create_admin_user(username, password):
    app = create_app()
    with app.app_context():
        if AdminUser.query.filter_by(username=username).first():
            print(f"Admin user {username} already exists.")
            return

        new_admin = AdminUser(username=username)
        new_admin.set_password(password) # Use the method from the model
        db.session.add(new_admin)
        db.session.commit()
        print(f"Admin user {username} created successfully.")

if __name__ == '__main__':
    if len(sys.argv) != 3:
        print("Usage: python create_admin.py <username> <password>", file=sys.stderr)
        sys.exit(1)
    
    admin_username = sys.argv[1]
    admin_password = sys.argv[2]

    MIN_ADMIN_PASSWORD_LENGTH = 8
    if len(admin_password) < MIN_ADMIN_PASSWORD_LENGTH:
        print(f"Error: Password must be at least {MIN_ADMIN_PASSWORD_LENGTH} characters long.", file=sys.stderr)
        sys.exit(1)
            
    create_admin_user(admin_username, admin_password)
