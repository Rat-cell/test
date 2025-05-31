# Campus Locker System

A **graduate-level software architecture demonstration** showcasing hexagonal architecture, comprehensive testing, and modern enterprise development practices through an automated parcel management system.

**Current Status:** Version 2.2.1 - Graduate-level documentation with modern Structurizr DSL diagrams, DBML schemas, and comprehensive architecture analysis. Production-ready with 268 tests and sub-25ms performance.

---

## 🚀  **Ready to explore?** 
Start with the [Quick Start Guide](docs/guides/QUICK_START.md) or explore the [System Overview](docs/introduction/ABOUT_PROJECT.md) for comprehensive architecture analysis.

---

## 🏗️ **Project Structure**

```
test/                               # 🏠 Root Project Directory
├── campus_locker_system/           # 🎯 Main Application Directory
│   ├── app/                        # Core Application (Hexagonal Architecture)
│   │   ├── __init__.py            # 🚀 Flask Application Factory
│   │   ├── config.py              # ⚙️ Configuration Management
│   │   ├── presentation/          # 🌐 Web Interface Layer (Flask routes & templates)
│   │   ├── services/              # ⚙️ Application Services (Business orchestration)
│   │   ├── business/              # 💼 Domain Business Logic (Core rules & validation)
│   │   ├── persistence/           # 🗄️ Data Access Layer (Repository pattern & models)
│   │   └── adapters/              # 🔌 External System Adapters (Email, notifications)
│   ├── tests/                     # 🧪 Comprehensive Test Suite (268 tests)
│   │   ├── test_fr*/              # ⚡ Functional Requirements Tests (FR-01 to FR-09)
│   │   ├── test_nfr*/             # 🎯 Non-Functional Requirements Tests (NFR-01 to NFR-06)
│   │   └── test_*.py              # 🔍 Unit, Integration & Performance Tests
│   ├── databases/                 # 🗄️ Dual Database Design
│   │   ├── campus_locker.db       # 📊 Main Operational Database
│   │   └── campus_locker_audit.db # 📋 Audit & Compliance Database
│   ├── scripts/                   # 🛠️ Automation & Deployment Scripts
│   ├── nginx/                     # 🌐 Web Server Configuration
│   │   └── nginx.conf             # ⚙️ Nginx Reverse Proxy Setup
│   ├── docker-compose.yml         # 🐳 Production Docker Configuration
│   ├── Dockerfile                 # 🐳 Container Build Instructions
│   ├── Makefile                   # 🛠️ Build & Deployment Automation
│   ├── requirements.txt           # 📦 Python Dependencies
│   └── .gitignore                 # 🚫 Git Exclusion Rules
├── docs/                          # 📚 Comprehensive Documentation
│   ├── diagrams/                  # 📊 Architecture Diagrams (Structurizr DSL + DBML)
│   ├── guides/                    # 📖 User & Developer Guides
│   ├── introduction/              # 🎓 Project Overview & Architecture Analysis
│   ├── specifications/            # 📋 Requirements & Technical Specifications
│   └── test_verifications/        # ✅ Test Documentation & Verification Reports
├── README.md                      # 📖 Main Project Documentation
└── CHANGELOG.md                   # 📈 Version History & Release Notes
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

## 📋 **Latest Changes - Version 2.2.1** *(2025-01-04)*

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

**📖 Documentation Structure Modernization**
- Streamlined README.md with clear navigation to specialized resources
- Eliminated documentation redundancy while maintaining comprehensive coverage
- Professional cross-references and graduate-level learning progression

*See [full changelog](CHANGELOG.md) for complete version history.*