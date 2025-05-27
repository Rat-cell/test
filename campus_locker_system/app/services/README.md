# Services Layer

This layer orchestrates business operations and coordinates between the business layer and infrastructure adapters.

## Service Modules

### 1. Parcel Service (`parcel_service.py`)
- Parcel lifecycle management
- Locker assignment orchestration
- Deposit and pickup workflows
- Overdue parcel processing

### 2. Locker Service (`locker_service.py`)
- Locker status management
- Administrative operations
- Status transition validation

### 3. PIN Service (`pin_service.py`)
- PIN reissue workflows
- Recipient PIN regeneration
- Admin PIN management

### 4. Notification Service (`notification_service.py`)
- Email notification orchestration
- Template application and sending
- Notification audit logging
- Delivery validation

### 5. Admin Auth Service (`admin_auth_service.py`)
- Admin authentication workflows
- Session management and validation
- Permission checking and authorization
- Admin user creation and management

### 6. Audit Service (`audit_service.py`)
- Audit event logging orchestration
- Event classification and validation
- Audit log retrieval and filtering
- Retention policy management
- Security event monitoring

## Architecture

Services coordinate between:
- **Business Layer**: Domain models and business rules
- **Persistence Layer**: Database operations and data access
- **Infrastructure**: External services (email, notifications)

## Design Principles

- Services orchestrate complex workflows
- Each service is responsible for one domain area
- Services handle transaction boundaries
- Error handling and logging is centralized
- Services return structured results (object, message) format

## Responsibilities

- **Orchestration**: Coordinate complex operations across domains
- **Transaction Management**: Ensure data consistency
- **External Integration**: Interface with infrastructure services
- **Error Handling**: Manage exceptions and rollbacks
- **Audit Logging**: Track important system events 