from typing import Optional, List
from app import db
from app.persistence.models import Locker as PersistenceLocker # Assuming your model is named Locker
from flask import current_app

class LockerRepository:
    @staticmethod
    def get_by_id(locker_id: int) -> Optional[PersistenceLocker]:
        """Fetches a persistence locker by ID."""
        try:
            return db.session.get(PersistenceLocker, locker_id)
        except Exception as e:
            current_app.logger.error(f"Error fetching locker by ID '{locker_id}' from repository: {str(e)}")
            return None

    @staticmethod
    def get_all() -> List[PersistenceLocker]:
        """Fetches all persistence lockers."""
        try:
            return PersistenceLocker.query.all()
        except Exception as e:
            current_app.logger.error(f"Error fetching all lockers from repository: {str(e)}")
            return []

    @staticmethod
    def get_count() -> int:
        """Returns the total count of lockers."""
        try:
            return PersistenceLocker.query.count()
        except Exception as e:
            current_app.logger.error(f"Error counting lockers in repository: {str(e)}")
            return 0

    @staticmethod
    def save(persistence_locker: PersistenceLocker) -> bool:
        """Saves (adds and commits) a persistence locker."""
        # This simple save assumes add & commit. For updates on existing objects,
        # if it's already tracked by the session, a commit might be enough.
        # SQLAlchemy's session.add() can handle both new and existing (for merging state).
        try:
            db.session.add(persistence_locker)
            db.session.commit()
            return True
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Error saving locker ID '{persistence_locker.id}' in repository: {str(e)}")
            return False

    @staticmethod
    def find_available_locker_by_size(size: str) -> Optional[PersistenceLocker]:
        """Finds an available locker of a specific size."""
        # Note: This is a more complex query that was previously in LockerManager.
        # It's being moved here to centralize DB access. 
        # The business logic of *what defines* available might still partially reside in LockerManager
        # or be passed as criteria to this repository method.
        try:
            # Assuming 'free' is the status for available lockers.
            # This might need adjustment based on actual Locker model and status values.
            return PersistenceLocker.query.filter_by(size=size, status='free').first()
        except Exception as e:
            current_app.logger.error(f"Error finding available locker of size '{size}': {str(e)}")
            return None

    @staticmethod
    def get_count_by_status(status: str) -> int:
        """Returns the total count of lockers with a specific status."""
        try:
            return PersistenceLocker.query.filter_by(status=status).count()
        except Exception as e:
            current_app.logger.error(f"Error counting lockers with status '{status}' in repository: {str(e)}")
            return 0

    @staticmethod
    def get_all_by_size_and_status(size: str, status: str) -> List[PersistenceLocker]:
        """Fetches all lockers matching a specific size and status."""
        try:
            return PersistenceLocker.query.filter_by(size=size, status=status).all()
        except Exception as e:
            current_app.logger.error(f"Error fetching lockers by size '{size}' and status '{status}': {str(e)}")
            return []

    @staticmethod
    def add_to_session(persistence_locker: PersistenceLocker) -> None:
        """Adds a locker instance to the current session without committing."""
        try:
            db.session.add(persistence_locker)
        except Exception as e:
            current_app.logger.error(f"Error adding locker ID '{persistence_locker.id}' to session: {str(e)}")
            raise

    @staticmethod
    def commit_session() -> bool:
        """Commits the current db session for locker operations."""
        try:
            db.session.commit()
            return True
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Error committing session via LockerRepository: {str(e)}")
            return False 