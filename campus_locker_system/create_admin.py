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
        print("Usage: python create_admin.py <username> <password>")
        sys.exit(1)
    
    admin_username = sys.argv[1]
    admin_password = sys.argv[2]
    create_admin_user(admin_username, admin_password)
