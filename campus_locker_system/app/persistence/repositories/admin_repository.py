from typing import Optional
from app import db
from app.persistence.models import AdminUser as PersistenceAdminUser
from flask import current_app

class AdminRepository:
    @staticmethod
    def get_by_username(username: str) -> Optional[PersistenceAdminUser]:
        """Fetches a persistence admin user by username."""
        try:
            return PersistenceAdminUser.query.filter_by(username=username).first()
        except Exception as e:
            current_app.logger.error(f"Error fetching admin by username '{username}' from repository: {str(e)}")
            return None

    @staticmethod
    def get_by_id(admin_id: int) -> Optional[PersistenceAdminUser]:
        """Fetches a persistence admin user by ID."""
        try:
            return db.session.get(PersistenceAdminUser, admin_id)
        except Exception as e:
            current_app.logger.error(f"Error fetching admin by ID '{admin_id}' from repository: {str(e)}")
            return None

    @staticmethod
    def get_count() -> int:
        """Returns the total count of admin users."""
        try:
            return PersistenceAdminUser.query.count()
        except Exception as e:
            current_app.logger.error(f"Error counting admin users in repository: {str(e)}")
            return 0

    @staticmethod
    def save(persistence_admin: PersistenceAdminUser) -> bool:
        """Saves (adds and commits) a persistence admin user."""
        try:
            db.session.add(persistence_admin)
            db.session.commit()
            return True
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Error saving admin user '{persistence_admin.username}' in repository: {str(e)}")
            return False

    @staticmethod
    def commit_session() -> bool:
        """Commits the current db session. 
           Generally, individual save/update/delete methods should handle their own commit.
           This is kept if there are specific bulk operations managed by a service that need a final commit.
        """
        try:
            db.session.commit()
            return True
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Error committing session via repository: {str(e)}")
            return False 