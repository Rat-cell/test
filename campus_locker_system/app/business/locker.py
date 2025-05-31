from flask import current_app
import json
import os
import logging

# Import the Locker model from its new location if LockerManager needs to type hint with it or instantiate.
# For now, LockerManager mostly deals with locker properties (size, status) or configuration data.
# The create_locker_from_config method does return a Locker instance, so the import is needed.
from app.persistence.models import Locker

logger = logging.getLogger(__name__)

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
        """
        Find an available locker of the preferred size
        FR-08: Out of Service - Skips out_of_service lockers during assignment
        NFR-01: Performance - Single optimized query for sub-200ms assignment
        """
        if not LockerManager.is_valid_size(preferred_size):
            return None
        
        # FR-08: Look for free locker of preferred size (excludes out_of_service)
        # NFR-01: Performance - Optimized single query with indexed filtering
        from app.persistence.repositories.locker_repository import LockerRepository
        locker = LockerRepository.find_available_locker_by_size(preferred_size)
        
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
        from app.persistence.repositories.locker_repository import LockerRepository
        locker = LockerRepository.get_by_id(locker_id)
        return locker is not None and locker.status == 'free'
    
    @staticmethod
    def get_available_lockers_by_size(size: str):
        """Get all available lockers of a specific size"""
        if not LockerManager.is_valid_size(size):
            return []
        
        from app.persistence.repositories.locker_repository import LockerRepository
        # Assuming a new repository method get_all_by_size_and_status will be added
        return LockerRepository.get_all_by_size_and_status(size=size, status='free')
    
    @staticmethod
    def get_locker_utilization_stats():
        """Get locker utilization statistics"""
        from app.persistence.repositories.locker_repository import LockerRepository
        total_lockers = LockerRepository.get_count()
        occupied_lockers = LockerRepository.get_count_by_status('occupied')
        out_of_service_lockers = LockerRepository.get_count_by_status('out_of_service')
        
        return {
            'total': total_lockers,
            'occupied': occupied_lockers,
            'available': total_lockers - occupied_lockers - out_of_service_lockers,
            'out_of_service': out_of_service_lockers,
            'utilization_rate': (occupied_lockers / total_lockers * 100) if total_lockers > 0 else 0
        }
    
    @staticmethod
    def validate_locker_configuration(config: dict) -> tuple[bool, str]:
        """
        Validate locker configuration structure and business rules
        Returns (is_valid, error_message)
        """
        try:
            if not isinstance(config, dict):
                return False, "Configuration must be a JSON object"
            
            if "lockers" not in config:
                return False, "Configuration must contain 'lockers' array"
            
            if not isinstance(config["lockers"], list):
                return False, "'lockers' must be an array"
            
            for i, locker in enumerate(config["lockers"]):
                if not isinstance(locker, dict):
                    return False, f"Locker {i} must be an object"
                
                # Check required fields
                required_fields = ['location', 'size']
                for field in required_fields:
                    if field not in locker:
                        return False, f"Locker {i} missing required field '{field}'"
                
                # Validate size using business rules
                if not LockerManager.is_valid_size(locker['size']):
                    return False, f"Locker {i} has invalid size '{locker['size']}'. Must be one of: {LockerManager.VALID_SIZES}"
                
                # Validate status if provided
                if 'status' in locker and not LockerManager.is_valid_status(locker['status']):
                    return False, f"Locker {i} has invalid status '{locker['status']}'. Must be one of: {LockerManager.VALID_STATUSES}"
                
                # Set default status if not provided
                if 'status' not in locker:
                    locker['status'] = 'free'
            
            return True, "Configuration is valid"
            
        except Exception as e:
            return False, f"Configuration validation error: {str(e)}"
    
    @staticmethod
    def create_locker_from_config(locker_config: dict) -> Locker:
        """
        Create a Locker instance from configuration data
        Business logic for locker creation
        """
        # Apply business defaults
        status = locker_config.get('status', 'free')
        
        # Validate business rules
        if not LockerManager.is_valid_size(locker_config['size']):
            raise ValueError(f"Invalid locker size: {locker_config['size']}")
        
        if not LockerManager.is_valid_status(status):
            raise ValueError(f"Invalid locker status: {status}")
        
        return Locker(
            location=locker_config['location'],
            size=locker_config['size'],
            status=status
        )
    
    @staticmethod
    def generate_default_locker_configuration() -> dict:
        """
        Generate default locker configuration using business rules and app config
        """
        config = current_app.config
        total_count = config.get('DEFAULT_LOCKER_COUNT', 5)
        location_pattern = config.get('DEFAULT_LOCATION_PATTERN', 'Building A, Floor {floor}, Row {row}')
        size_distribution = config.get('DEFAULT_SIZE_DISTRIBUTION', {
            'small': 40, 'medium': 40, 'large': 20
        })
        
        # Calculate how many of each size to create
        small_count = int(total_count * size_distribution['small'] / 100)
        medium_count = int(total_count * size_distribution['medium'] / 100)
        large_count = total_count - small_count - medium_count  # Remainder goes to large
        
        lockers = []
        locker_id = 1
        
        # Create lockers by size
        for size, count in [('small', small_count), ('medium', medium_count), ('large', large_count)]:
            for _ in range(count):
                # Simple floor/row calculation
                floor = ((locker_id - 1) // 3) + 1
                row = ((locker_id - 1) % 3) + 1
                
                location = location_pattern.format(
                    locker_id=locker_id,
                    floor=floor,
                    row=row
                )
                
                lockers.append({
                    "id": locker_id,
                    "location": location,
                    "size": size,
                    "status": "free"
                })
                locker_id += 1
        
        return {
            "lockers": lockers,
            "metadata": {
                "total_count": total_count,
                "size_distribution": size_distribution,
                "location_pattern": location_pattern,
                "source": "default_generation"
            }
        } 