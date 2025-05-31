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

### 2. Audit Adapter (`audit_adapter.py`)
- **Interface**: `AuditAdapterInterface` (Primarily for `MockAuditAdapter`)
- **Implementations**:
  - `SQLAlchemyAuditAdapter` - _Removed. Persistence handled by `AuditLogRepository`._
  - `MockAuditAdapter` - Testing implementation (still available)
- **Purpose**: Abstracts audit log persistence (primarily for testing via `MockAuditAdapter`)
- **Usage**: _`AuditService` now uses `AuditLogRepository` for persistence. `MockAuditAdapter` is for tests._

## Adapter Pattern Benefits

1. **Testability**: Mock implementations for unit testing
2. **Flexibility**: Easy to switch implementations (e.g., different email providers)
3. **Clean Architecture**: Business logic doesn't depend on external frameworks
4. **Maintainability**: Clear separation of concerns

## Factory Functions

Each remaining adapter has a factory function that returns the appropriate implementation:
- `create_email_adapter()` - Creates email adapter

These factories choose between production and test implementations based on configuration.

## Usage Example (Email Adapter)

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
- Add configuration-based adapter selection for remaining adapters
- Add monitoring/metrics adapters 