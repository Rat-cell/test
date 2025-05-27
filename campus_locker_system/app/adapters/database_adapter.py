"""
Database Adapter - Database persistence interface and implementation

This adapter provides a clean interface to database operations,
abstracting away SQLAlchemy implementation details from the business logic.
"""
from abc import ABC, abstractmethod
from typing import Optional, List, Any, TypeVar, Generic, Tuple
from contextlib import contextmanager
from flask import current_app
from app import db

# Generic type for model classes
ModelType = TypeVar('ModelType')


class DatabaseAdapterInterface(ABC):
    """Interface for database adapters - defines the contract"""
    
    @abstractmethod
    def get_by_id(self, model_class: type, entity_id: int) -> Optional[Any]:
        """Get entity by ID"""
        pass
    
    @abstractmethod
    def save(self, entity: Any) -> Tuple[bool, str]:
        """Save entity to database"""
        pass
    
    @abstractmethod
    def delete(self, entity: Any) -> Tuple[bool, str]:
        """Delete entity from database"""
        pass
    
    @abstractmethod
    def find_all(self, model_class: type) -> List[Any]:
        """Find all entities of a given type"""
        pass
    
    @abstractmethod
    def find_by_criteria(self, model_class: type, **criteria) -> List[Any]:
        """Find entities matching criteria"""
        pass
    
    @abstractmethod
    def find_one_by_criteria(self, model_class: type, **criteria) -> Optional[Any]:
        """Find single entity matching criteria"""
        pass
    
    @abstractmethod
    def commit(self) -> Tuple[bool, str]:
        """Commit current transaction"""
        pass
    
    @abstractmethod
    def rollback(self) -> Tuple[bool, str]:
        """Rollback current transaction"""
        pass
    
    @abstractmethod
    @contextmanager
    def transaction(self):
        """Context manager for database transactions"""
        pass


class SQLAlchemyAdapter(DatabaseAdapterInterface):
    """SQLAlchemy implementation of the database adapter"""
    
    def get_by_id(self, model_class: type, entity_id: int) -> Optional[Any]:
        """Get entity by ID using SQLAlchemy"""
        try:
            return db.session.get(model_class, entity_id)
        except Exception as e:
            current_app.logger.error(f"Error getting {model_class.__name__} by ID {entity_id}: {str(e)}")
            return None
    
    def save(self, entity: Any) -> Tuple[bool, str]:
        """Save entity using SQLAlchemy"""
        try:
            db.session.add(entity)
            return True, "Entity staged for save"
        except Exception as e:
            error_msg = f"Error saving entity {type(entity).__name__}: {str(e)}"
            current_app.logger.error(error_msg)
            return False, error_msg
    
    def delete(self, entity: Any) -> Tuple[bool, str]:
        """Delete entity using SQLAlchemy"""
        try:
            db.session.delete(entity)
            return True, "Entity staged for deletion"
        except Exception as e:
            error_msg = f"Error deleting entity {type(entity).__name__}: {str(e)}"
            current_app.logger.error(error_msg)
            return False, error_msg
    
    def find_all(self, model_class: type) -> List[Any]:
        """Find all entities using SQLAlchemy"""
        try:
            return model_class.query.all()
        except Exception as e:
            current_app.logger.error(f"Error finding all {model_class.__name__}: {str(e)}")
            return []
    
    def find_by_criteria(self, model_class: type, **criteria) -> List[Any]:
        """Find entities by criteria using SQLAlchemy"""
        try:
            query = model_class.query
            for key, value in criteria.items():
                if hasattr(model_class, key):
                    query = query.filter(getattr(model_class, key) == value)
            return query.all()
        except Exception as e:
            current_app.logger.error(f"Error finding {model_class.__name__} by criteria {criteria}: {str(e)}")
            return []
    
    def find_one_by_criteria(self, model_class: type, **criteria) -> Optional[Any]:
        """Find single entity by criteria using SQLAlchemy"""
        try:
            query = model_class.query
            for key, value in criteria.items():
                if hasattr(model_class, key):
                    query = query.filter(getattr(model_class, key) == value)
            return query.first()
        except Exception as e:
            current_app.logger.error(f"Error finding {model_class.__name__} by criteria {criteria}: {str(e)}")
            return None
    
    def commit(self) -> Tuple[bool, str]:
        """Commit transaction using SQLAlchemy"""
        try:
            db.session.commit()
            return True, "Transaction committed successfully"
        except Exception as e:
            error_msg = f"Error committing transaction: {str(e)}"
            current_app.logger.error(error_msg)
            try:
                db.session.rollback()
            except:
                pass  # Rollback might fail if session is corrupted
            return False, error_msg
    
    def rollback(self) -> Tuple[bool, str]:
        """Rollback transaction using SQLAlchemy"""
        try:
            db.session.rollback()
            return True, "Transaction rolled back successfully"
        except Exception as e:
            error_msg = f"Error rolling back transaction: {str(e)}"
            current_app.logger.error(error_msg)
            return False, error_msg
    
    @contextmanager
    def transaction(self):
        """Transaction context manager using SQLAlchemy"""
        try:
            yield
            success, message = self.commit()
            if not success:
                raise Exception(message)
        except Exception as e:
            self.rollback()
            raise e


class MockDatabaseAdapter(DatabaseAdapterInterface):
    """Mock database adapter for testing - stores data in memory"""
    
    def __init__(self):
        self.data = {}  # Store by (model_class, id)
        self.next_id = 1
        self.committed = False
    
    def get_by_id(self, model_class: type, entity_id: int) -> Optional[Any]:
        """Mock get by ID"""
        return self.data.get((model_class.__name__, entity_id))
    
    def save(self, entity: Any) -> Tuple[bool, str]:
        """Mock save"""
        # Assign ID if not set
        if not hasattr(entity, 'id') or entity.id is None:
            entity.id = self.next_id
            self.next_id += 1
        
        self.data[(type(entity).__name__, entity.id)] = entity
        return True, "Mock entity saved"
    
    def delete(self, entity: Any) -> Tuple[bool, str]:
        """Mock delete"""
        key = (type(entity).__name__, entity.id)
        if key in self.data:
            del self.data[key]
            return True, "Mock entity deleted"
        return False, "Entity not found"
    
    def find_all(self, model_class: type) -> List[Any]:
        """Mock find all"""
        return [entity for (cls_name, _), entity in self.data.items() 
                if cls_name == model_class.__name__]
    
    def find_by_criteria(self, model_class: type, **criteria) -> List[Any]:
        """Mock find by criteria"""
        results = []
        for entity in self.find_all(model_class):
            match = True
            for key, value in criteria.items():
                if not hasattr(entity, key) or getattr(entity, key) != value:
                    match = False
                    break
            if match:
                results.append(entity)
        return results
    
    def find_one_by_criteria(self, model_class: type, **criteria) -> Optional[Any]:
        """Mock find one by criteria"""
        results = self.find_by_criteria(model_class, **criteria)
        return results[0] if results else None
    
    def commit(self) -> Tuple[bool, str]:
        """Mock commit"""
        self.committed = True
        return True, "Mock transaction committed"
    
    def rollback(self) -> Tuple[bool, str]:
        """Mock rollback"""
        self.committed = False
        return True, "Mock transaction rolled back"
    
    @contextmanager
    def transaction(self):
        """Mock transaction context"""
        try:
            yield
            self.commit()
        except Exception as e:
            self.rollback()
            raise e


# Factory function to create appropriate adapter
def create_database_adapter() -> DatabaseAdapterInterface:
    """Factory to create the appropriate database adapter based on configuration"""
    try:
        # Check if we're in testing mode
        if hasattr(current_app, 'testing') and current_app.testing:
            return MockDatabaseAdapter()
        else:
            return SQLAlchemyAdapter()
    except RuntimeError:
        # Working outside of application context - default to production adapter
        return SQLAlchemyAdapter() 