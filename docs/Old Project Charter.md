# Digital Literacy IV: Software Architecture  
**Campus Locker System - Updated Project Charter (Version 2.2.2, January 2025)**

---

## 1. Project Overview

**Project Status**: Production-Ready Architecture Implementation  
**Project Type**: Graduate-level software architecture demonstration and enterprise parcel management system  
**Project**: A comprehensive browser-based campus locker system implementing hexagonal architecture with automated parcel lifecycle management, secure PIN-based access, dual-database design, and enterprise-grade audit trails.  
**Deployment**: Production-ready Docker containerization with nginx, SSL certificates, automated backups, and comprehensive monitoring.

---

## 2. Stakeholders & Success Metrics

**Key Success Factor (production deployment)**: 
- **Performance**: Sub-25ms response times for locker assignment (87% better than 200ms baseline)
- **Reliability**: Comprehensive test coverage across all functional and non-functional requirements
- **User Experience**: Complete workflows finishing in under 3 minutes with professional error handling
- **Enterprise Readiness**: Comprehensive audit trails, automated backup systems, and operational management capabilities

---

## 3. Scope

**In-scope**  
1. **Complete Web Application**: Deposit, pickup, admin dashboard, and API endpoints (Flask with hexagonal architecture)  
2. **Dual Database Design**: Operational SQLite database + dedicated audit database with automated backups  
3. **Enterprise Email System**: Flask-Mail with professional templates, automated reminders, and delivery tracking  
4. **Advanced Security**: PBKDF2 + bcrypt password hashing, salted SHA-256 PIN storage, comprehensive audit logging  
5. **Automated Operations**: 24-hour reminder system, background processing, locker maintenance workflows  
6. **Comprehensive Testing**: Complete test coverage for all FR/NFR requirements with performance benchmarking  
7. **Production Infrastructure**: Docker deployment, nginx configuration, SSL certificates, automated monitoring  
8. **Professional Documentation**: Structurizr DSL architecture diagrams, DBML database schemas, comprehensive guides  

**Enhanced Beyond Original Scope**  
1. **Hexagonal Architecture**: Clean separation with 6 distinct layers (Presentation, Service, Business, Persistence, Database, Adapters)  
2. **Enterprise Audit System**: Dedicated audit database with comprehensive compliance logging  
3. **Operational Excellence**: Locker maintenance workflows, system status monitoring, administrative oversight  
4. **Advanced Error Handling**: Professional user experience with recovery guidance and clear messaging  
5. **Modern Documentation**: Graduate-level architectural analysis with educational content and visual diagrams  

**Out-of-scope**  
1. Physical locker electronics integration
2. External courier API integration  
3. Payment gateway integration
4. Mobile application development
5. Multi-tenant architecture for multiple campuses
6. Real-time hardware sensor integration
7. Advanced analytics and reporting dashboards

---

### Glossary

| Stakeholder            | Key Concern                    |
|------------------------|--------------------------------|
| Recipient              | Fast, reliable pickup process  |
| Sender/Courier         | Easy deposit workflow          |
| IT Operations          | System reliability and monitoring |
| Campus Facility Team   | Operational management and maintenance |

| Term                   | Meaning                                                    |
|------------------------|------------------------------------------------------------|
| PIN                    | 6-digit cryptographically secure code with salted SHA-256 hash |
| PIN Expiry             | Configurable expiry with regeneration capabilities |
| Sender/Courier         | Person depositing the parcel with email notification       |
| Recipient              | Person picking up delivery with PIN-based access          |
| Audit Trail            | Comprehensive logging in dedicated database for compliance |
| Hexagonal Architecture | Ports and Adapters pattern with clean domain separation    |
| Dual Database Design   | Operational + audit database separation for performance    |

---

## 4. Requirements

### Functional Requirements

| ID     | Capability                | Requirement Description                                                                 |
|--------|---------------------------|-----------------------------------------------------------------------------------------|
| FR-01  | Assign Locker            | Assign the next free locker large enough for the parcel in ≤ 25 ms                   |
| FR-02  | Generate PIN             | Create a 6-digit PIN and store its salted SHA-256 hash                                 |
| FR-03  | Email Notification System| Comprehensive email system with professional templates and delivery tracking           |
| FR-04  | Automated Reminders      | Fully automatic 24h reminder system with background processing (no admin intervention) |
| FR-05  | Re-issue PIN             | Advanced PIN regeneration with rate limiting, token-based system, and user self-service|
| FR-06  | Admin Management         | Comprehensive admin dashboard with parcel management, system monitoring, and reporting |
| FR-07  | Audit Trail              | Enterprise-grade audit system with dedicated database and comprehensive event logging  |
| FR-08  | Out of Service           | Smart locker maintenance workflows with automated assignment logic                     |
| FR-09  | Enhanced Error Handling  | Professional error handling with user guidance, recovery options, and clear messaging  |

### Non-Functional Quality Attributes

| Attribute     | Target Requirement                                       | Implementation Approach                                  |
|---------------|----------------------------------------------------------|----------------------------------------------------------|
| Performance   | Locker assignment in ≤ 25ms (87% improvement over baseline) | Optimized database queries and hexagonal architecture   |
| Reliability   | System auto-recovery in <10s; minimal transaction loss  | SQLite WAL mode, automated backups, comprehensive testing |
| Security      | Multi-layer encryption for all sensitive data           | PBKDF2, bcrypt, SHA-256, comprehensive audit trails     |
| Backup        | Automated backup system with 7-day retention           | Automated backup service with retention management      |
| Usability     | Accessibility compliance and professional user interface | Focus management, error handling, responsive design     |
| Testing       | Comprehensive test coverage for all requirements        | 268+ tests covering functional and non-functional requirements |

**Additional Quality Targets**:
- **Maintainability**: Hexagonal architecture with clean separation of concerns
- **Scalability**: Repository pattern and service layer for future growth
- **Observability**: Comprehensive logging and audit trail system
- **Operability**: Administrative tools and maintenance workflows
- **Documentation**: Graduate-level architectural analysis and modern diagrams

---

## 5. Architecture

### Style

**Hexagonal Architecture (Ports and Adapters Pattern)**:  
**External World ↔ Presentation ↔ Service ↔ Business ↔ Persistence ↔ Database ↔ Adapters**

### Enhanced Architecture Details

```

                    External World                           
  Web Users  Admin Dashboard  Email System  APIs          

              

        Presentation Layer (Flask Routes & Templates)        
  Routes  Templates  API Endpoints  Error Handlers        

              

         Service Layer (Application Orchestration)          
  Parcel  Admin  Notification  Audit  Database Services  

              

          Business Layer (Domain Logic & Rules)             
  Locker  Parcel  PIN  Admin Auth  Notification Managers 

              

        Persistence Layer (Repository Pattern)              
  Repositories  Models  Data Mappers  Query Builders     

              

          Database Layer (Dual Database Design)             
  Main Database  Audit Database  Backup System            

              

           Adapters Layer (Infrastructure)                  
  Email  Database  Audit  Backup  Monitoring Adapters   

```

### Rationale

**Hexagonal Architecture** provides superior benefits over traditional layered approaches:
- **Testability**: Business logic can be tested in isolation without infrastructure dependencies
- **Flexibility**: Infrastructure components can be replaced without affecting core business rules  
- **Maintainability**: Clear boundaries reduce cognitive load and prevent architectural erosion
- **Evolution**: New features can be added without disrupting existing functionality
- **Domain Focus**: Business rules are the center of the architecture, not an implementation detail

**Dual Database Design** separates operational and audit concerns for:
- **Performance**: Optimized operational queries without audit overhead
- **Compliance**: Dedicated audit trail for regulatory requirements
- **Security**: Audit logs protected from operational data modifications
- **Backup Strategy**: Independent backup policies for different data types

---

## 6. Constraints & Risks

### Constraints

| Constraint                    | Implementation Approach                                   |
|-------------------------------|-----------------------------------------------------------|
| Simulated locker hardware     | LockerAdapter with realistic simulation and testing      |
| Production-ready deployment   | Docker containerization with nginx and SSL certificates  |
| Modern Python compatibility   | Python 3.12+ with timezone-aware datetime handling      |
| Campus-scale deployment       | SQLite-based design optimized for institutional use      |

### Risks

| Risk                          | Mitigation Strategy                                       | Likelihood |
|-------------------------------|-----------------------------------------------------------|------------|
| Database performance issues   | Dual database design, SQLite WAL mode, query optimization| Medium     |
| Concurrent access problems    | Repository pattern with proper transaction handling      | Low        |
| Email delivery failures       | Comprehensive error handling and retry mechanisms        | Medium     |
| Security vulnerabilities     | Multi-layer security, audit trails, comprehensive testing| Low        |
| System maintenance complexity | Automated monitoring, backup systems, admin tools        | Low        |
| Architectural drift          | Hexagonal architecture with clear boundaries and testing | Low        |

**Additional Risk Considerations**:
- **Scale limitations**: SQLite-based design suitable for campus-scale but may need migration for larger deployments
- **Email dependency**: System relies on email for notifications (mitigated with comprehensive error handling)

---

## 7. Appendices

### 7.1 Activity Diagrams

**Purpose**: Describe the end-to-end flow of parcel deposit and pickup processes across the hexagonal architecture layers.

**Included Diagrams**:
- **Basic Activity Flows**: 
  - `activity_parcel_flows.puml` - High-level parcel lifecycle workflows showing major decision points and process steps
  - `activity_admin_flows.puml` - Administrative workflow processes and management operations
- **Detailed Swimlane Flows** (`docs/diagrams/activity_diagrams/swimlane_flows/`):
  - `activity_deposit_flow_with_lanes.puml` - User deposit flow with security validation and locker assignment
  - `activity_pickup_flow_with_lanes.puml` - Recipient pickup flow with PIN verification and audit logging
  - `admin_login_flow_with_lanes.puml` - Administrative login flow with 2FA and comprehensive audit logging
  - `admin_system_status_flow_with_lanes.puml` - System status monitoring flow with real-time metrics collection
  - `admin_manage_parcels_flow_with_lanes.puml` - Parcel management flow with search capabilities and operational controls
  - `admin_audit_logs_flow_with_lanes.puml` - Audit log management flow with filtering and compliance reporting

**Alignment**: All activity diagrams align with the hexagonal architecture pattern, showing clear separation between presentation, service, business, persistence, and adapter layers during process execution.

### 7.2 Class Diagrams

**Purpose**: Illustrate the object-oriented design structure and relationships within the hexagonal architecture implementation.

**Included Diagrams** (`docs/diagrams/class_diagrams/`):
- `campus_locker_class_diagram.puml` - Complete system class structure showing domain models, repositories, services, and their relationships
- `deposit_flow_class_diagram.puml` - Focused class interactions during the parcel deposit process

**Coverage Areas**:
- **Domain Models**: Core business entities (Locker, Parcel, PIN, AuditLog) with their attributes and business methods
- **Repository Pattern**: Data access layer abstractions and their concrete implementations
- **Service Layer**: Application service classes and their orchestration responsibilities
- **Business Logic**: Domain managers and their encapsulated business rules
- **Adapter Interfaces**: Ports and adapters pattern implementation showing infrastructure abstractions

**Design Patterns Illustrated**: Repository pattern, Service layer pattern, Domain-driven design entities, Dependency injection patterns, and Adapter pattern implementations.

### 7.3 C4 Level 1 – System Context Diagram

**Scope**: Highest level view showing the Campus Locker System in its organizational environment.

**Diagram File**: `campus_locker_architecture.dsl` (System Landscape view in Structurizr DSL)

**Elements**:
- **Campus Locker System**: The software system being documented
- **External Actors**: Recipients, Senders/Couriers, System Administrators, Campus Facility Staff
- **External Systems**: Email service infrastructure, backup systems, monitoring tools
- **Interactions**: High-level data flows and communication channels between actors and the system

**Purpose**: Provides stakeholders with an understanding of how the system fits within the broader campus infrastructure ecosystem.

### 7.4 C4 Level 2 – Container Diagram

**Scope**: Major structural building blocks of the Campus Locker System and their interactions.

**Diagram File**: `campus_locker_architecture.dsl` (Container view in Structurizr DSL)

**Containers**:
- **Web Application**: Flask-based hexagonal architecture implementation handling user interactions
- **Operational Database**: SQLite database storing active parcel and locker data
- **Audit Database**: Dedicated SQLite database for compliance and audit trail storage
- **Email System**: Flask-Mail integration for notification delivery
- **Admin Dashboard**: Administrative interface for system management and monitoring
- **Background Scheduler**: Automated reminder processing and maintenance tasks

**Technology Stack**: Shows the specific technologies used for each container and the protocols for inter-container communication.

### 7.5 C4 Level 3 – Component Diagram

**Scope**: Internal structure of the Web Application container showing hexagonal architecture implementation.

**Diagram Files**: 
- `hexagonal_architecture_overview.dsl` (Hexagonal architecture component view in Structurizr DSL)
- `campus_locker_architecture.dsl` (Component view in Structurizr DSL)

**Components by Layer**:
- **Presentation Layer**: Routes, Templates, API Endpoints, Error Handlers
- **Service Layer**: Parcel Service, Admin Service, Notification Service, Audit Service, Database Service
- **Business Layer**: Locker Manager, Parcel Manager, PIN Manager, Admin Auth Manager, Notification Manager
- **Persistence Layer**: Repository implementations, Data Models, Query Builders, Data Mappers
- **Adapter Layer**: Email Adapter, Database Adapter, Audit Adapter, Backup Adapter

**Relationships**: Shows dependencies between components and how the ports and adapters pattern maintains clean separation of concerns.

### 7.6 C4 Level 4 – Code Diagrams

**Scope**: Detailed implementation patterns and design decisions at the code level.

**Diagram File**: `campus_locker_code_level.puml` (Detailed code-level PlantUML diagram)

**Focus Areas**:
- **Repository Pattern Implementation**: Concrete examples of data access abstraction
- **Service Orchestration**: How application services coordinate business operations
- **Domain Logic Encapsulation**: Business rule implementation within domain managers
- **Dependency Injection**: How components receive their dependencies through constructor injection
- **Error Handling Patterns**: Exception management and user-friendly error responses

**Documentation Format**: Combines UML class diagrams with code snippets showing actual implementation patterns used throughout the system.

### 7.7 Database Schema Documentation

**Purpose**: Professional database documentation with detailed schema definitions.

**Schema Files** (`docs/diagrams/database_schemas/`):
- `main_database_schema.dbml` - Operational database schema (parcels, lockers, user data)
- `audit_database_schema.dbml` - Audit database schema (compliance and audit trail)

**Compatibility**: DBML format compatible with dbdiagram.io and other modern database documentation tools.

### 7.8 Technology Stack

### Core Application Framework

| Technology | Version | Purpose | Justification |
|------------|---------|---------|---------------|
| **Python** | 3.12+ | Primary programming language | Modern language features, extensive ecosystem, excellent for rapid development and maintainability |
| **Flask** | 3.0.0 | Web framework | Lightweight, flexible, excellent for hexagonal architecture implementation with clean separation of concerns |
| **SQLAlchemy** | 3.1.1 | Object-Relational Mapping | Provides abstraction for repository pattern, supports multiple databases, excellent for domain modeling |

### Database & Persistence

| Technology | Purpose | Justification |
|------------|---------|---------------|
| **SQLite** | Primary database | Zero-configuration, file-based, perfect for campus-scale deployment, supports WAL mode for reliability |
| **Dual Database Design** | Operational + Audit separation | Performance optimization and compliance requirements, independent backup strategies |

### Security & Authentication

| Technology | Version | Purpose | Justification |
|------------|---------|---------|---------------|
| **bcrypt** | 4.1.2 | Password hashing | Industry-standard adaptive hashing, resistant to rainbow table attacks |
| **SHA-256** | Built-in | PIN hashing | Cryptographically secure with salt, fast verification for user experience |
| **PBKDF2** | Built-in | Additional key derivation | Extra security layer for sensitive operations, configurable iteration counts |

### Communication & Notifications

| Technology | Version | Purpose | Justification |
|------------|---------|---------|---------------|
| **Flask-Mail** | 0.10.0 | Email notifications | Professional email templates, reliable delivery, easy integration with Flask |
| **SMTP** | Standard | Email transport | Universal email protocol, supports various email providers |

### Testing & Quality Assurance

| Technology | Version | Purpose | Justification |
|------------|---------|---------|---------------|
| **pytest** | 8.3.3 | Testing framework | Comprehensive testing capabilities, excellent fixtures, supports all test types |
| **pytest-cov** | 4.1.0 | Coverage reporting | Ensures comprehensive test coverage across all requirements |
| **pytest-flask** | 1.3.0 | Flask testing integration | Specialized Flask testing utilities for web application testing |

### Code Quality & Security

| Technology | Version | Purpose | Justification |
|------------|---------|---------|---------------|
| **flake8** | 7.0.0 | Code linting | Maintains code quality standards, catches potential issues early |
| **black** | 23.12.1 | Code formatting | Consistent code style, reduces formatting debates, improves readability |
| **isort** | 5.13.2 | Import sorting | Organized imports, consistent style across modules |
| **safety** | 3.0.1 | Security scanning | Identifies known security vulnerabilities in dependencies |
| **bandit** | 1.7.5 | Security analysis | Static security analysis for Python code, catches security issues |

### Production Infrastructure

| Technology | Purpose | Justification |
|------------|---------|---------------|
| **Docker** | Containerization | Consistent deployment environments, easy scaling, infrastructure as code |
| **Redis** | Caching and session storage | High-performance in-memory data store, distributed session management, application caching |
| **nginx** | Web server/reverse proxy | High performance, SSL termination, static file serving, production-ready |
| **Gunicorn** | WSGI server | Production-grade Python application server, excellent for Flask applications |
| **SSL/TLS** | Security encryption | Secure communications, data protection in transit, industry requirement |

### Development & Documentation

| Technology | Purpose | Justification |
|------------|---------|---------------|
| **Git** | Version control | Distributed version control for code collaboration, change tracking, and release management |
| **venv** | Python virtual environment | Isolated Python environment, dependency management, resolves macOS security restrictions |
| **Structurizr DSL** | Architecture diagrams | Modern architecture modeling, multiple view support, version control friendly |
| **PlantUML** | Process and class diagrams | Wide tool support, text-based diagrams, easy version control |
| **DBML** | Database documentation | Professional database schema documentation, tool-agnostic format |

### Architecture Alignment

**Technology choices support hexagonal architecture**:
- **Flask**: Lightweight framework allows clean implementation of ports and adapters pattern
- **SQLAlchemy**: Enables repository pattern with proper domain model abstraction
- **Dependency structure**: Technologies chosen to support loose coupling and testability
- **Testing stack**: Comprehensive testing enables confident refactoring and evolution
- **Security layers**: Multiple security technologies create defense-in-depth approach

**Rationale for Technology Selection**:
- **Simplicity over complexity**: Chosen proven, stable technologies over cutting-edge options
- **Educational value**: Technologies demonstrate enterprise patterns while remaining approachable
- **Production readiness**: All technologies suitable for real-world deployment
- **Maintainability**: Technology stack supports long-term maintenance and evolution

