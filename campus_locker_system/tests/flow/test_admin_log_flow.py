import pytest
from app import db
from app.persistence.models import AuditLog, AdminUser
from app.application.services import log_audit_event
from flask import Flask

@pytest.fixture
def admin_user_fixture(init_database, app):
    with app.app_context():
        admin = AdminUser.query.first()
        if not admin:
            admin = AdminUser(username='testadmin', password_hash='dummyhash')
            db.session.add(admin)
            db.session.commit()
        return admin.id  # Return the admin ID only

def test_admin_login_audit_log(init_database, app, admin_user_fixture):
    with app.app_context():
        admin = db.session.get(AdminUser, admin_user_fixture)  # Query by ID to get attached instance
        # Simulate admin login event
        log_audit_event("ADMIN_LOGIN_SUCCESS", {"admin_username": admin.username, "admin_id": admin.id})
        # Check that the audit log was created
        log_entry = AuditLog.query.filter_by(action="ADMIN_LOGIN_SUCCESS").order_by(AuditLog.timestamp.desc()).first()
        assert log_entry is not None
        assert str(admin.id) in log_entry.details
        assert admin.username in log_entry.details 