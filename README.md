# Campus Locker System

A **graduate-level software architecture demonstration** showcasing hexagonal architecture, comprehensive testing, and modern enterprise development practices through an automated parcel management system.

**Current Status:** Version 2.2.2 - Enhanced diagram organization with specialized swimlane flow categorization, comprehensive cross-functional process documentation, and industry-standard folder structure. Graduate-level documentation with modern Structurizr DSL diagrams, DBML schemas, and comprehensive architecture analysis. Production-ready with 268 tests and sub-25ms performance.

---

## 🚀  **Ready to explore?** 
Start with the [Quick Start Guide](docs/guides/QUICK_START.md) or explore the [System Overview](docs/introduction/ABOUT_PROJECT.md) for comprehensive architecture analysis.

---

## 🏗️ **Project Structure**

```
test/                               # 🏠 Root Project Directory
├── campus_locker_system/           # 🎯 Main Application Directory
│   ├── __pycache__/                # 🐍 Python bytecode cache
│   ├── .github/                    # 📋 GitHub workflows and templates
│   ├── .pytest_cache/              # 🧪 Pytest cache directory
│   ├── app/                        # 🏗️ Core Application (Hexagonal Architecture)
│   │   ├── __init__.py            # 🚀 Flask Application Factory
│   │   ├── config.py              # ⚙️ Configuration Management
│   │   ├── adapters/              # 🔌 Infrastructure Adapters (Email, audit system)
│   │   ├── business/              # 💼 Domain Layer (Core business logic & rules)
│   │   ├── persistence/           # 🗄️ Data Access Layer (Repository pattern & models)
│   │   │   ├── repositories/      # 🏛️ Repository pattern implementations
│   │   │   └── models.py         # 🏗️ SQLAlchemy models
│   │   ├── presentation/          # 🌐 User Interface Layer (Routes, templates, APIs)
│   │   └── services/              # ⚙️ Application Services (Business orchestration)
│   ├── databases/                 # 🗄️ Dual Database Design
│   │   ├── campus_locker.db       # 📊 Main Operational Database
│   │   ├── campus_locker_audit.db # 📋 Audit & Compliance Database
│   │   └── backups/               # 💾 Automated backup storage
│   ├── logs/                      # 📝 Application log files
│   ├── scripts/                   # 🛠️ Automation & deployment scripts
│   ├── tests/                     # 🧪 Comprehensive Test Suite (268 tests)
│   │   ├── test_fr*/              # ⚡ Functional Requirements Tests (FR-01 to FR-09)
│   │   ├── test_nfr*/             # 🎯 Non-Functional Requirements Tests (NFR-01 to NFR-06)
│   │   ├── test_application.py    # 🏗️ Core application testing
│   │   ├── test_presentation.py   # 🌐 UI and route testing
│   │   ├── performance/           # ⚡ Performance benchmarks
│   │   └── conftest.py           # ⚙️ Pytest configuration and fixtures
│   ├── .gitignore                # 🚫 Git exclusion rules
│   ├── create_admin.py           # 👨‍💼 Admin user creation script
│   ├── Dockerfile                # 🐳 Container build instructions
│   ├── docker-compose.yml        # 🐳 Production Docker configuration
│   ├── pytest.ini               # 🧪 Pytest configuration
│   ├── requirements.txt          # 📦 Python dependencies
│   ├── run.py                    # 🚀 Application entry point
│   └── seed_lockers.py           # 🗄️ Locker initialization script
├── docs/                          # 📚 Comprehensive Documentation
│   ├── diagrams/                  # 📊 Architecture Diagrams & Database Schemas
│   │   ├── c4_model/             # C4 Model Architecture Diagrams (Structurizr DSL)
│   │   ├── activity_diagrams/    # Process Flow & Workflow Diagrams (PlantUML)
│   │   │   └── swimlane_flows/   # Activity Diagrams with Detailed Swimlanes
│   │   ├── class_diagrams/       # Object-Oriented Design Diagrams (PlantUML)
│   │   └── database_schemas/     # Database Schema Definitions (DBML)
│   ├── guides/                    # 📖 User & Developer Guides
│   ├── introduction/              # 🎓 Project Overview & Architecture Analysis
│   ├── specifications/            # 📋 Requirements & Technical Specifications
│   └── test_verifications/        # ✅ Test Documentation & Reports
├── scripts/                       # 🛠️ Root-level utility scripts
├── ssl/                           # 🔒 SSL certificates and security configuration
├── venv/                          # 🐍 Python virtual environment
├── .gitignore                     # 🚫 Git exclusion rules
├── CHANGELOG.md                   # 📈 Version History & Release Notes
├── cookies.txt                    # 🍪 HTTP cookies for testing/development
├── docker-compose.yml             # 🐳 Production Docker configuration
├── Makefile                       # 🚀 Production deployment & Docker operations
├── nginx.conf                     # 🌐 Nginx web server configuration
└── README.md                      # 📖 Main Project Documentation
```

---

## 📚 **Documentation**

| Document | Purpose |
|----------|---------|
| **[📊 Architecture Diagrams](docs/diagrams/)** | Visual system understanding (Structurizr DSL + DBML schemas) |
| **[💻 Development Guide](docs/guides/DEVELOPMENT_GUIDE.md)** | Developer workflows and technical details |
| **[⚡ Functional Requirements](docs/specifications/FUNCTIONAL_REQUIREMENTS.md)** | FR-01 to FR-09 specifications |
| **[🎯 Non-Functional Requirements](docs/specifications/NON_FUNCTIONAL_REQUIREMENTS.md)** | Performance, security, reliability metrics |
| **[🗄️ Database Documentation](docs/specifications/DATABASE_DOCUMENTATION.md)** | Dual database architecture details |
| **[✅ Test Verifications](docs/test_verifications/)** | 268 comprehensive test documentation |
| **[📈 Changelog](CHANGELOG.md)** | Version history and changes |

---

## 🎯 **Key Highlights**

- 🏗️ **Hexagonal Architecture** with clean separation of concerns
- 🔒 **Enterprise Security** (PBKDF2, bcrypt, audit trails)
- 📊 **High Performance** (4-25ms response times, 87-96% better than targets)
- 🛡️ **Comprehensive Testing** (268 tests covering all requirements)
- 🗄️ **Dual Database Design** (operational + audit separation)
- 🐳 **Production Ready** (Docker deployment, automated backups)


---

## 📋 **Latest Changes - Version 2.2.2** *(2025-01-04)*

### 📊 Diagram Organization Enhancement & Swimlane Flow Structure

**🗂️ Professional Diagram Organization**
- Created dedicated `swimlane_flows/` subfolder within `activity_diagrams/` for enhanced organization
- Organized 6 comprehensive swimlane flow diagrams with detailed cross-functional process visualization
- Clear separation between basic activity flows and detailed swimlane process flows
- Industry-standard folder structure following diagram type categorization best practices

**📋 Comprehensive Swimlane Flow Documentation**
- User Flow Diagrams: deposit and pickup processes with detailed security validation
- Administrative Flow Diagrams: login, system status, parcel management, and audit log flows
- Enhanced documentation with clear User Flow vs Administrative Flow distinctions
- Professional PlantUML implementation with cross-functional responsibility boundaries

**📚 Documentation Structure Modernization**
- Updated all project documentation (README.md, ABOUT_PROJECT.md) with new folder structure
- Detailed diagram descriptions with feature highlights and categorization
- Complete file inventory reflecting new organizational structure
- Enhanced navigation experience for different types of process flows

*Previous Version 2.2.1 (2025-01-04):*
### 📚 Documentation Excellence & Architecture Visualization Modernization

**🏗️ Architecture Documentation Revolution**
- Complete ABOUT_PROJECT.md rewrite with graduate-level architectural analysis
- Added beginner-friendly explanations using restaurant, library, and bank analogies
- Enhanced architectural ASCII diagram with all 6 layers (Presentation → Database)
- Detailed quality attributes showing 4-25ms performance (87-96% better than requirements)

**📊 Modern Architecture Visualization with Structurizr DSL**
- Migrated from PlantUML to modern Structurizr DSL for architecture visualization
- Created 10 comprehensive views: System Landscape, Hexagonal Architecture, Core Business Logic
- Color-coded layer visualization with interactive exploration support
- Professional architecture modeling with proper container and component relationships

**🗄️ Database Schema Documentation with DBML**
- Comprehensive DBML schemas for operational and audit databases (verified against actual code)
- dbdiagram.io compatible visualization for professional database documentation
- Complete business rules, constraints, and performance optimization documentation

*See [full changelog](CHANGELOG.md) for complete version history.*