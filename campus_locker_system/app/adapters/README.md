# Adapters Layer - External System Interfaces

The adapters layer provides clean interfaces to external systems, following the Hexagonal Architecture pattern. This layer abstracts implementation details from the business logic and services.

## Implemented Adapters

### 1. Email Adapter (`email_adapter.py`)
- **Interface**: `EmailAdapterInterface`
- **Implementations**: 
  - `FlaskMailAdapter` - Production Flask-Mail implementation
  - `MockEmailAdapter` - Testing implementation
- **Purpose**: Abstracts email sending (Flask-Mail) from business logic
- **Usage**: Used by `NotificationService` for sending emails

### 2. Database Adapter (`database_adapter.py`)
- **Interface**: `DatabaseAdapterInterface`
- **Implementations**:
  - `SQLAlchemyAdapter` - Production SQLAlchemy implementation
  - `MockDatabaseAdapter` - Testing implementation
- **Purpose**: Abstracts database operations from business logic
- **Usage**: Repository pattern for data persistence operations

### 3. Audit Adapter (`audit_adapter.py`)
- **Interface**: `AuditAdapterInterface`
- **Implementations**:
  - `SQLAlchemyAuditAdapter` - Production SQLAlchemy implementation
  - `MockAuditAdapter` - Testing implementation
- **Purpose**: Abstracts audit log persistence
- **Usage**: Used by `AuditService` for storing and retrieving audit events

## Adapter Pattern Benefits

1. **Testability**: Mock implementations for unit testing
2. **Flexibility**: Easy to switch implementations (e.g., different email providers)
3. **Clean Architecture**: Business logic doesn't depend on external frameworks
4. **Maintainability**: Clear separation of concerns

## Factory Functions

Each adapter has a factory function that returns the appropriate implementation:
- `create_email_adapter()` - Creates email adapter
- `create_database_adapter()` - Creates database adapter  
- `create_audit_adapter()` - Creates audit adapter

These factories choose between production and test implementations based on configuration.

## Usage Example

```python
from app.adapters import create_email_adapter, EmailMessage

# Get adapter (automatically chooses implementation)
email_adapter = create_email_adapter()

# Use clean interface
message = EmailMessage(
    to="user@example.com",
    subject="Test",
    body="Hello world"
)

success, result = email_adapter.send_email(message)
```

## Future Enhancements

- Add Redis adapter for caching
- Add file storage adapter for attachments
- Add configuration-based adapter selection
- Add monitoring/metrics adapters 