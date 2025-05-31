from typing import Optional, List, Iterable
from app import db
from app.persistence.models import Parcel as PersistenceParcel, Locker as PersistenceLocker # Import Locker for joins if needed later
from flask import current_app
from datetime import datetime

class ParcelRepository:
    @staticmethod
    def get_by_id(parcel_id: int) -> Optional[PersistenceParcel]:
        """Fetches a parcel by its ID."""
        try:
            return db.session.get(PersistenceParcel, parcel_id)
        except Exception as e:
            current_app.logger.error(f"Error fetching parcel by ID '{parcel_id}' from repository: {str(e)}")
            return None

    @staticmethod
    def get_all_by_status(status: str) -> List[PersistenceParcel]:
        """Fetches all parcels with a specific status."""
        try:
            return PersistenceParcel.query.filter_by(status=status).all()
        except Exception as e:
            current_app.logger.error(f"Error fetching parcels by status '{status}': {str(e)}")
            return []
    
    @staticmethod
    def get_all_deposited_for_pin_check() -> List[PersistenceParcel]:
        """Fetches all deposited parcels that might have a PIN (for pickup processing)."""
        try:
            # Parcels relevant for PIN check are those in 'deposited' status.
            # The service layer will iterate and check parcel.pin_hash and verify.
            return PersistenceParcel.query.filter_by(status='deposited').all()
        except Exception as e:
            current_app.logger.error(f"Error fetching deposited parcels for PIN check: {str(e)}")
            return []

    @staticmethod
    def get_all_deposited_older_than(cutoff_datetime: datetime) -> List[PersistenceParcel]:
        """Fetches all deposited parcels whose deposited_at is older than or equal to the cutoff_datetime."""
        try:
            return PersistenceParcel.query.filter(
                PersistenceParcel.status == 'deposited',
                PersistenceParcel.deposited_at.isnot(None),
                PersistenceParcel.deposited_at <= cutoff_datetime
            ).all()
        except Exception as e:
            current_app.logger.error(f"Error fetching deposited parcels older than {cutoff_datetime}: {str(e)}")
            return []

    @staticmethod
    def get_all_deposited_needing_reminder(reminder_cutoff_time: datetime) -> List[PersistenceParcel]:
        """Fetches parcels that are deposited, older than reminder_cutoff_time, and haven't had a reminder sent."""
        try:
            return PersistenceParcel.query.filter(
                PersistenceParcel.status == 'deposited',
                PersistenceParcel.deposited_at <= reminder_cutoff_time,
                PersistenceParcel.reminder_sent_at.is_(None)
            ).all()
        except Exception as e:
            current_app.logger.error(f"Error fetching parcels needing reminder: {str(e)}")
            return []

    @staticmethod
    def get_by_pin_generation_token(token: str) -> Optional[PersistenceParcel]:
        """Fetches a parcel by its PIN generation token."""
        try:
            return PersistenceParcel.query.filter_by(pin_generation_token=token).first()
        except Exception as e:
            current_app.logger.error(f"Error fetching parcel by pin_generation_token '{token[:8]}...': {str(e)}")
            return None

    @staticmethod
    def get_by_email_and_locker_and_status(email: str, locker_id: int, status: str) -> Optional[PersistenceParcel]:
        """Fetches a parcel by recipient email, locker ID, and status."""
        try:
            return PersistenceParcel.query.filter(
                PersistenceParcel.recipient_email.ilike(email), # Case-insensitive email match
                PersistenceParcel.locker_id == locker_id,
                PersistenceParcel.status == status
            ).first()
        except Exception as e:
            current_app.logger.error(f"Error fetching parcel by email '{email}', locker '{locker_id}', status '{status}': {str(e)}")
            return None

    @staticmethod
    def get_all_by_locker_id_and_status(locker_id: int, status: str) -> List[PersistenceParcel]:
        """Fetches all parcels for a given locker_id and status."""
        try:
            return PersistenceParcel.query.filter_by(locker_id=locker_id, status=status).all()
        except Exception as e:
            current_app.logger.error(f"Error fetching parcels by locker_id '{locker_id}' and status '{status}': {str(e)}")
            return []

    @staticmethod
    def get_count() -> int:
        """Returns the total count of parcels."""
        try:
            return PersistenceParcel.query.count()
        except Exception as e:
            current_app.logger.error(f"Error counting all parcels in repository: {str(e)}")
            return 0

    @staticmethod
    def get_count_by_status(status: str) -> int:
        """Returns the count of parcels with a specific status."""
        try:
            return PersistenceParcel.query.filter_by(status=status).count()
        except Exception as e:
            current_app.logger.error(f"Error counting parcels with status '{status}' in repository: {str(e)}")
            return 0

    @staticmethod
    def get_count_by_locker_id_and_status(locker_id: int, status: str) -> int:
        """Returns the count of parcels for a given locker_id and status."""
        try:
            return PersistenceParcel.query.filter_by(locker_id=locker_id, status=status).count()
        except Exception as e:
            current_app.logger.error(f"Error counting parcels for locker_id '{locker_id}' and status '{status}': {str(e)}")
            return 0

    @staticmethod
    def save(persistence_parcel: PersistenceParcel) -> bool:
        """Saves a single parcel instance (adds and commits)."""
        try:
            # Use merge to handle both new and existing objects correctly
            # merge() handles objects that might already be attached to a different session
            db.session.merge(persistence_parcel)
            db.session.commit()
            return True
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Error saving parcel ID '{persistence_parcel.id}' in repository: {str(e)}")
            return False

    @staticmethod
    def add_to_session(persistence_parcel: PersistenceParcel) -> None:
        """Adds a parcel instance to the current session without committing."""
        try:
            db.session.add(persistence_parcel)
        except Exception as e:
            # Not rolling back here as commit is separate
            current_app.logger.error(f"Error adding parcel ID '{persistence_parcel.id}' to session: {str(e)}")
            raise # Re-raise to make the service layer aware of the add failure

    @staticmethod
    def commit_session() -> bool:
        """Commits the current session."""
        try:
            db.session.commit()
            return True
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Error committing parcel session in repository: {str(e)}")
            return False

    @staticmethod
    def save_all(parcels_to_save: Iterable[PersistenceParcel]) -> bool:
        """Adds multiple parcel instances to session and commits."""
        try:
            for parcel in parcels_to_save:
                db.session.add(parcel) # Add or update tracked instances
            db.session.commit()
            return True
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Error bulk saving parcels in repository: {str(e)}")
            return False 