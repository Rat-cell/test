# create_admin.py (in campus_locker_system root)
from app import create_app, db
import sys

def create_admin_user(username, password):
    app = create_app()
    with app.app_context():
        from app.services.admin_auth_service import AdminAuthService
        from app.business.admin_auth import AdminRole
        
        admin_user, message = AdminAuthService.create_admin_user(username, password, AdminRole.ADMIN)
        
        if admin_user:
            print(f"Admin user {username} created successfully.")
        else:
            print(f"Error creating admin user: {message}")

if __name__ == '__main__':
    if len(sys.argv) != 3:
        print("Usage: python create_admin.py <username> <password>", file=sys.stderr)
        sys.exit(1)
    
    admin_username = sys.argv[1]
    admin_password = sys.argv[2]

    # Password validation will be handled by the AdminAuthService business rules
    # No need for duplicate validation here
            
    create_admin_user(admin_username, admin_password)
