# Campus Locker System

A **graduate-level software architecture demonstration** showcasing hexagonal architecture, comprehensive testing, and modern enterprise development practices through an automated parcel management system.

**Current Status:** Version 2.3.0 - Enhanced backup system reliability with WAL checkpoint handling, robust JSON configuration system with overwrite protection, and isolated test infrastructure. Enterprise-grade data safety with client-ready deployment capabilities. Production-ready with comprehensive testing framework and sub-25ms performance.

---

## **Ready to explore?** 
Start with the [Quick Start Guide](docs/guides/QUICK_START.md) or explore the [System Overview](docs/introduction/ABOUT_PROJECT.md) for comprehensive architecture analysis.

---

## **Project Structure**

```
test/                               # Root Project Directory
 campus_locker_system/           # Main Application Directory
    __pycache__/                # Python bytecode cache
    .github/                    # GitHub workflows and templates
    .pytest_cache/              # Pytest cache directory
    app/                        # Core Application (Hexagonal Architecture)
       __init__.py            # Flask Application Factory
       config.py              # Configuration Management
       adapters/              # Infrastructure Adapters (Email, audit system)
       business/              # Domain Layer (Core business logic & rules)
       persistence/           # Data Access Layer (Repository pattern & models)
          repositories/      # Repository pattern implementations
          models.py         # SQLAlchemy models
       presentation/          # User Interface Layer (Routes, templates, APIs)
       services/              # Application Services (Business orchestration)
    databases/                 # Dual Database Design
       campus_locker.db       # Main Operational Database
       campus_locker_audit.db # Audit & Compliance Database
       backups/               # Automated backup storage
    logs/                      # Application log files
    scripts/                   # Automation & deployment scripts
    tests/                     # Comprehensive Test Suite (268 tests)
       test_fr*/              # Functional Requirements Tests (FR-01 to FR-09)
       test_nfr*/             # Non-Functional Requirements Tests (NFR-01 to NFR-06)
       test_application.py    # Core application testing
       test_presentation.py   # UI and route testing
       performance/           # Performance benchmarks
       conftest.py           # Pytest configuration and fixtures
    .gitignore                # Git exclusion rules
    create_admin.py           # Admin user creation script
    Dockerfile                # Container build instructions
    docker-compose.yml        # Production Docker configuration
    pytest.ini               # Pytest configuration
    requirements.txt          # Python dependencies
    run.py                    # Application entry point
    seed_lockers.py           # Locker initialization script
 docs/                          # Comprehensive Documentation
    diagrams/                  # Architecture Diagrams & Database Schemas
       c4_model/             # C4 Model Architecture Diagrams (Structurizr DSL)
       activity_diagrams/    # Process Flow & Workflow Diagrams (PlantUML)
          swimlane_flows/   # Activity Diagrams with Detailed Swimlanes
       class_diagrams/       # Object-Oriented Design Diagrams (PlantUML)
       database_schemas/     # Database Schema Definitions (DBML)
    guides/                    # User & Developer Guides
    introduction/              # Project Overview & Architecture Analysis
    specifications/            # Requirements & Technical Specifications
 scripts/                       # Root-level utility scripts
 ssl/                           # SSL certificates and security configuration
 venv/                          # Python virtual environment
 .gitignore                     # Git exclusion rules
 CHANGELOG.md                   # Version History & Release Notes
 cookies.txt                    # HTTP cookies for testing/development
 docker-compose.yml             # Production Docker configuration
 Makefile                       # Production deployment & Docker operations
 nginx.conf                     # Nginx web server configuration
 README.md                      # Main Project Documentation
```

---

## **Documentation**

| Document | Purpose |
|----------|---------|
| **[Architecture Diagrams](docs/diagrams/)** | Visual system understanding (Structurizr DSL + DBML schemas) |
| **[Development Guide](docs/guides/DEVELOPMENT_GUIDE.md)** | Developer workflows and technical details |
| **[Functional Requirements](docs/specifications/FUNCTIONAL_REQUIREMENTS.md)** | FR-01 to FR-09 specifications |
| **[Non-Functional Requirements](docs/specifications/NON_FUNCTIONAL_REQUIREMENTS.md)** | Performance, security, reliability metrics |
| **[Database Documentation](docs/specifications/DATABASE_DOCUMENTATION.md)** | Dual database architecture details |
| **[Changelog](CHANGELOG.md)** | Version history and changes |

---

## **Key Highlights**

- **Hexagonal Architecture** with clean separation of concerns
- **Enterprise Security** (PBKDF2, bcrypt, audit trails)
- **High Performance** (4-25ms response times, 87-96% better than targets)
- **Comprehensive Testing** (268 tests covering all requirements)
- **Dual Database Design** (operational + audit separation)
- **Production Ready** (Docker deployment, automated backups)


---

## **Latest Changes - Version 2.3.0** *(2025-06-22)*

### Backup System Enhancement & JSON Configuration Excellence

**Backup System Reliability Enhancement**
- WAL Checkpoint Implementation: Added SQLite WAL checkpoint handling for complete backup data integrity
- DatabaseService Enhancement: Improved backup methods with proper WAL synchronization
- Backup Data Completeness: Resolved issues where recent transactions weren't included in backups
- Production Backup Safety: All backup operations now guarantee complete data preservation

**JSON Configuration System & Overwrite Protection**
- Client Configuration Workflow: Robust JSON-based locker configuration for client deployments
- Overwrite Protection: Advanced conflict detection preventing duplicate locker IDs and data corruption
- Safety-First Design: Comprehensive validation with clear error messages and automatic backup creation
- Client Deployment Ready: Production-ready configuration system for campus-specific locker layouts

**Test Infrastructure Excellence**
- NFR-02 Test Isolation: Complete test isolation preventing interference with production database
- Test Configuration Framework: Added configuration flags for robust test separation
- Comprehensive Test Documentation: Detailed test suite documentation with execution guides
- Test Safety Measures: All tests operate in isolated environments protecting production data

*Previous Version 2.2.2 (2025-06-01):*
### Documentation Excellence & Architecture Visualization Modernization

**Architecture Documentation Revolution**
- Complete ABOUT_PROJECT.md rewrite with graduate-level architectural analysis
- Added beginner-friendly explanations using restaurant, library, and bank analogies
- Enhanced architectural ASCII diagram with all 6 layers (Presentation → Database)
- Detailed quality attributes showing 4-25ms performance (87-96% better than requirements)

**Modern Architecture Visualization with Structurizr DSL**
- Migrated from PlantUML to modern Structurizr DSL for architecture visualization
- Created 10 comprehensive views: System Landscape, Hexagonal Architecture, Core Business Logic
- Color-coded layer visualization with interactive exploration support
- Professional architecture modeling with proper container and component relationships

**Database Schema Documentation with DBML**
- Comprehensive DBML schemas for operational and audit databases (verified against actual code)
- dbdiagram.io compatible visualization for professional database documentation
- Complete business rules, constraints, and performance optimization documentation

*See [full changelog](CHANGELOG.md) for complete version history.*
