from app import db
from flask import current_app

class Locker(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    size = db.Column(db.String(50), nullable=False)  # e.g., 'small', 'medium', 'large'
    # Possible statuses: 'free', 'occupied', 'out_of_service', 'disputed_contents', 'awaiting_collection'
    status = db.Column(db.String(50), nullable=False, default='free')
    parcels = db.relationship('Parcel', backref='locker', lazy=True)

    def __repr__(self):
        return f'<Locker {self.id} ({self.size}) - {self.status}>'


class LockerManager:
    """Business logic for locker management"""
    
    # Valid locker sizes
    VALID_SIZES = ['small', 'medium', 'large']
    
    # Valid locker statuses
    VALID_STATUSES = [
        'free', 'occupied', 'out_of_service', 
        'disputed_contents', 'awaiting_collection'
    ]
    
    @staticmethod
    def is_valid_size(size: str) -> bool:
        """Validate locker size"""
        return size in LockerManager.VALID_SIZES
    
    @staticmethod
    def is_valid_status(status: str) -> bool:
        """Validate locker status"""
        return status in LockerManager.VALID_STATUSES
    
    @staticmethod
    def find_available_locker(preferred_size: str):
        """Find an available locker of the preferred size"""
        if not LockerManager.is_valid_size(preferred_size):
            return None
        
        # Look for free locker of preferred size
        locker = Locker.query.filter_by(
            size=preferred_size, 
            status='free'
        ).first()
        
        return locker
    
    @staticmethod
    def can_transition_status(current_status: str, new_status: str) -> bool:
        """Business rules for locker status transitions"""
        valid_transitions = {
            'free': ['occupied', 'out_of_service'],
            'occupied': ['free', 'out_of_service', 'disputed_contents', 'awaiting_collection'],
            'out_of_service': ['free'],
            'disputed_contents': ['out_of_service', 'free'],
            'awaiting_collection': ['free', 'out_of_service']
        }
        
        return new_status in valid_transitions.get(current_status, [])
    
    @staticmethod
    def get_locker_dimensions(size: str) -> dict:
        """Get locker dimensions from configuration"""
        dimensions = current_app.config.get('LOCKER_SIZE_DIMENSIONS', {})
        return dimensions.get(size, {'height': 0, 'width': 0, 'depth': 0})
    
    @staticmethod
    def is_locker_available(locker_id: int) -> bool:
        """Check if specific locker is available"""
        locker = db.session.get(Locker, locker_id)
        return locker is not None and locker.status == 'free'
    
    @staticmethod
    def get_available_lockers_by_size(size: str):
        """Get all available lockers of a specific size"""
        if not LockerManager.is_valid_size(size):
            return []
        
        return Locker.query.filter_by(
            size=size, 
            status='free'
        ).all()
    
    @staticmethod
    def get_locker_utilization_stats():
        """Get locker utilization statistics"""
        total_lockers = Locker.query.count()
        occupied_lockers = Locker.query.filter_by(status='occupied').count()
        out_of_service_lockers = Locker.query.filter_by(status='out_of_service').count()
        
        return {
            'total': total_lockers,
            'occupied': occupied_lockers,
            'available': total_lockers - occupied_lockers - out_of_service_lockers,
            'out_of_service': out_of_service_lockers,
            'utilization_rate': (occupied_lockers / total_lockers * 100) if total_lockers > 0 else 0
        } 