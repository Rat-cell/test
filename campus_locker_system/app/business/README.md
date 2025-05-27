# Business Layer

This layer contains the domain models and business rules for the campus locker system.

## Domains

### 1. Parcel Management (`parcel.py`)
- Core parcel business entity
- Status transitions and validation
- Relationships with lockers

### 2. Locker Management (`locker.py`) 
- Locker business entity
- Status management and validation
- Size and capacity rules

### 3. PIN Management (`pin.py`)
- PIN generation and verification
- Expiry time calculation
- Security hashing logic

### 4. Notification Management (`notification.py`) 
- Email template management
- Notification type definitions  
- Email validation business rules
- Template formatting logic

### 5. Admin & Auth Management (`admin_auth.py`)
- Admin user business entity
- Authentication and authorization logic
- Session management business rules
- Role-based permissions
- Password strength validation

### 6. Audit Logging Management (`audit.py`)
- Audit event business entity
- Event classification and severity rules
- Audit validation and retention policies
- Event categorization logic
- Compliance and security tracking

## Business Rules

Each domain encapsulates specific business logic and validation rules:

- **Parcel**: Status transitions, deposit/pickup workflows, expiry handling
- **Locker**: Size validation, status changes, availability logic
- **PIN**: Security requirements, expiry calculations, hashing strategies
- **Notification**: Template validation, delivery rules, notification types
- **Admin & Auth**: Authentication flows, session management, permission checks
- **Audit**: Event classification, retention policies, security compliance

## Architecture Principles

- Domain entities are pure business objects with no external dependencies
- Business rules are centralized within each domain
- Validation logic is embedded in the business entities
- Cross-domain interactions are managed by the service layer

## Architecture

The business layer is independent of:
- Database implementation
- External services
- User interface
- Framework specifics

All business entities are pure Python classes with no external dependencies. 