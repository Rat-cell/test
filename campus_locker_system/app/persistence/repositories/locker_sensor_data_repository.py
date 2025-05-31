from app import db
from app.persistence.models import LockerSensorData as PersistenceLockerSensorData
from flask import current_app

class LockerSensorDataRepository:
    @staticmethod
    def get_count() -> int:
        """Returns the total count of locker sensor data entries."""
        try:
            return PersistenceLockerSensorData.query.count()
        except Exception as e:
            current_app.logger.error(f"Error counting locker sensor data in repository: {str(e)}")
            return 0

    # Add other CRUD methods here if LockerSensorData needs them in the future
    # e.g., save, get_by_id, get_by_locker_id, etc. 