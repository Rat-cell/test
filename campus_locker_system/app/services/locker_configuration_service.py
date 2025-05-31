"""
Locker Configuration Service

This service handles loading, parsing, and applying locker configurations
from various sources (JSON files, environment variables, defaults).

It coordinates between configuration sources and the business logic layer.
"""
import json
import os
import logging
from typing import Dict, List, Tuple, Any
from flask import current_app

from app.business.locker import LockerManager
from app.persistence.models import Locker
from app.persistence.repositories.locker_repository import LockerRepository

logger = logging.getLogger(__name__)


class LockerConfigurationService:
    """Service for managing locker configuration from multiple sources"""
    
    @staticmethod
    def load_locker_configuration() -> Dict[str, Any]:
        """
        Load locker configuration from various sources in priority order:
        1. Environment variable (LOCKER_SIMPLE_CONFIG) 
        2. JSON configuration file (LOCKER_CONFIG_FILE)
        3. Default configuration (generated from business rules)
        
        Returns configuration dictionary
        """
        config = current_app.config
        
        # Priority 1: Simple environment variable configuration
        if config.get('LOCKER_SIMPLE_CONFIG'):
            logger.info("📝 Loading locker configuration from environment variable")
            return LockerConfigurationService._parse_simple_config(
                config['LOCKER_SIMPLE_CONFIG']
            )
        
        # Priority 2: JSON configuration file
        config_file = config.get('LOCKER_CONFIG_FILE')
        if config_file and os.path.exists(config_file):
            logger.info(f"📁 Loading locker configuration from file: {config_file}")
            try:
                with open(config_file, 'r') as f:
                    file_config = json.load(f)
                    
                # Validate using business logic
                is_valid, error_msg = LockerManager.validate_locker_configuration(file_config)
                if not is_valid:
                    logger.warning(f"⚠️ Invalid locker config file {config_file}: {error_msg}")
                    logger.info("🔄 Falling back to default configuration")
                    return LockerManager.generate_default_locker_configuration()
                
                logger.info(f"✅ Successfully loaded {len(file_config.get('lockers', []))} lockers from config file")
                return file_config
                
            except (json.JSONDecodeError, IOError) as e:
                logger.warning(f"⚠️ Error reading locker config file {config_file}: {e}")
                logger.info("🔄 Falling back to default configuration")
        
        # Priority 3: Default configuration
        logger.info("🏗️ Generating default locker configuration")
        return LockerManager.generate_default_locker_configuration()
    
    @staticmethod
    def _parse_simple_config(config_string: str) -> Dict[str, Any]:
        """
        Parse simple environment variable configuration.
        Format: "count:10,size_small:4,size_medium:4,size_large:2,location_prefix:Student Center Floor {floor} Unit {unit}"
        """
        try:
            parts = config_string.split(',')
            config_dict = {}
            
            for part in parts:
                if ':' not in part:
                    continue
                key, value = part.split(':', 1)
                config_dict[key.strip()] = value.strip()
            
            # Parse configuration parameters
            total_count = int(config_dict.get('count', 5))
            size_small = int(config_dict.get('size_small', total_count // 3))
            size_medium = int(config_dict.get('size_medium', total_count // 3))
            size_large = int(config_dict.get('size_large', total_count - size_small - size_medium))
            location_prefix = config_dict.get('location_prefix', 'Building A Floor {floor} Unit {unit}')
            
            # Validate total count matches size distribution
            if size_small + size_medium + size_large != total_count:
                logger.warning(f"Size distribution doesn't match total count, adjusting...")
                size_large = total_count - size_small - size_medium
            
            # Generate lockers
            lockers = []
            locker_id = 1
            
            for size, count in [('small', size_small), ('medium', size_medium), ('large', size_large)]:
                for _ in range(count):
                    floor = ((locker_id - 1) // 5) + 1  # 5 lockers per floor
                    unit = ((locker_id - 1) % 5) + 1    # Unit 1-5
                    
                    location = location_prefix.format(
                        locker_id=locker_id,
                        floor=floor,
                        unit=unit,
                        size=size
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
                    "size_distribution": {
                        "small": size_small,
                        "medium": size_medium, 
                        "large": size_large
                    },
                    "location_prefix": location_prefix,
                    "source": "environment_variable"
                }
            }
            
        except (ValueError, KeyError) as e:
            logger.warning(f"⚠️ Invalid simple locker config '{config_string}': {e}")
            logger.info("🔄 Falling back to default configuration")
            return LockerManager.generate_default_locker_configuration()
    
    @staticmethod
    def seed_lockers_from_configuration() -> Tuple[bool, str]:
        """
        Seed lockers from configuration if database is empty.
        Uses business logic to create and validate lockers.
        
        Returns (success, message)
        """
        try:
            # Check if seeding is enabled
            if not current_app.config.get('ENABLE_DEFAULT_LOCKER_SEEDING', True):
                logger.info("🚫 Locker seeding disabled by configuration")
                return True, "Locker seeding disabled"
            
            # Check if lockers already exist
            existing_count = LockerRepository.get_count()
            if existing_count > 0:
                logger.info(f"📊 Found {existing_count} existing lockers, skipping seeding")
                return True, f"Skipped seeding - {existing_count} lockers already exist"
            
            # Load configuration
            config = LockerConfigurationService.load_locker_configuration()
            
            # Validate configuration using business logic
            is_valid, error_msg = LockerManager.validate_locker_configuration(config)
            if not is_valid:
                logger.error(f"❌ Configuration validation failed: {error_msg}")
                return False, f"Configuration validation failed: {error_msg}"
            
            # Create lockers using business logic
            created_lockers = []
            for locker_config in config.get('lockers', []):
                try:
                    locker = LockerManager.create_locker_from_config(locker_config)
                    LockerRepository.add_to_session(locker)
                    created_lockers.append(locker)
                except Exception as e:
                    logger.error(f"❌ Error creating locker from config {locker_config}: {e}")
                    return False, f"Error creating locker: {e}"
            
            # Commit all lockers
            if not LockerRepository.commit_session():
                logger.error(f"❌ Failed to commit batch of new lockers during seeding.")
                return False, "Database commit error during locker seeding."
            
            source = config.get('metadata', {}).get('source', 'unknown')
            success_msg = f"Successfully created {len(created_lockers)} lockers from {source} configuration"
            logger.info(f"🏗️ {success_msg}")
            
            return True, success_msg
            
        except Exception as e:
            error_msg = f"Locker seeding failed: {str(e)}"
            logger.error(f"❌ {error_msg}")
            return False, error_msg
    
    @staticmethod
    def get_configuration_summary() -> Dict[str, Any]:
        """Get summary of current locker configuration"""
        try:
            config = LockerConfigurationService.load_locker_configuration()
            metadata = config.get('metadata', {})
            
            # Get current database stats
            db_stats = LockerManager.get_locker_utilization_stats()
            
            return {
                'configuration_source': metadata.get('source', 'unknown'),
                'configured_count': metadata.get('total_count', 0),
                'configured_distribution': metadata.get('size_distribution', {}),
                'database_stats': db_stats,
                'seeding_enabled': current_app.config.get('ENABLE_DEFAULT_LOCKER_SEEDING', True),
                'config_file_path': current_app.config.get('LOCKER_CONFIG_FILE'),
                'config_file_exists': os.path.exists(current_app.config.get('LOCKER_CONFIG_FILE', ''))
            }
            
        except Exception as e:
            logger.error(f"Error getting configuration summary: {e}")
            return {'error': str(e)}
    
    @staticmethod
    def validate_external_configuration(config_data: Dict[str, Any]) -> Tuple[bool, str]:
        """
        Validate external configuration data using business rules.
        Useful for validating uploaded config files or API inputs.
        """
        return LockerManager.validate_locker_configuration(config_data)
    
    @staticmethod
    def export_current_configuration() -> Dict[str, Any]:
        """Export current database state as configuration"""
        try:
            lockers = LockerRepository.get_all()
            
            config = {
                "metadata": {
                    "description": "Exported from current database state",
                    "total_count": len(lockers),
                    "exported_at": "runtime"
                },
                "lockers": []
            }
            
            for locker in lockers:
                config["lockers"].append({
                    "id": locker.id,
                    "location": locker.location,
                    "size": locker.size,
                    "status": locker.status
                })
            
            return config
            
        except Exception as e:
            logger.error(f"Error exporting configuration: {e}")
            return {"error": str(e)} 