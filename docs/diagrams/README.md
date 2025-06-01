# Campus Locker System - Diagrams Documentation

This directory contains all architectural and design diagrams for the Campus Locker System, organized by diagram type for better maintainability and navigation.

## 📁 Directory Structure

```
docs/diagrams/
├── README.md                    # This documentation file
├── c4_model/                   # C4 Model Architecture Diagrams
├── activity_diagrams/          # Process Flow Diagrams
│   └── swimlane_flows/         # Activity Diagrams with Swimlanes
├── class_diagrams/             # Object-Oriented Design Diagrams
└── database_schemas/           # Database Schema Definitions
```

## 🏗️ C4 Model (`c4_model/`)

Contains architectural diagrams following the official C4 model methodology:

### Files:
- **`campus_locker_architecture.dsl`** - Main C4 model definition file
  - C0: System Landscape
  - C1: System Context 
  - C2: Container Diagrams (multiple views)
  - C3: Component Diagrams
- **`campus_locker_code_level.puml`** - C4 Level 4 code diagrams
- **`C4_LEVEL4_README.md`** - Usage instructions for Level 4 diagrams

### Viewing C4 Diagrams:
1. **Online**: Use [Structurizr Express](https://structurizr.com/express) to load the `.dsl` file
2. **VS Code**: Install the "C4 DSL Extension" 
3. **CLI**: Use Structurizr CLI with Docker

### Diagram Levels:
- **C0 - System Landscape**: High-level system context
- **C1 - System Context**: System boundaries and external dependencies
- **C2 - Containers**: Application architecture and technology choices
- **C3 - Components**: Internal component structure and relationships
- **C4 - Code**: Detailed class diagrams and implementation structure

## 🔄 Activity Diagrams (`activity_diagrams/`)

Process flow diagrams showing user journeys and system workflows:

### Core Activity Flows:
- **`activity_parcel_flows.puml`** - User parcel deposit and pickup workflows
  - Parcel deposit process
  - Parcel pickup process with PIN validation
  - Status checking functionality
  - Background system monitoring
- **`activity_admin_flows.puml`** - Administrative management workflows
  - Admin authentication and authorization
  - Dashboard operations and system management
  - User management and audit log review
  - System configuration and maintenance

### Swimlane Flows (`swimlane_flows/`)

Detailed process flows with swimlanes showing cross-functional interactions:

#### User Flow Diagrams:
- **`activity_deposit_flow_with_lanes.puml`** - Parcel deposit with detailed swimlanes
  - User/Customer interactions
  - Web Application processing
  - Database Service operations
  - Email Service notifications
  - Locker Hardware integration
  - Audit & Monitoring logging

- **`activity_pickup_flow_with_lanes.puml`** - Parcel pickup with security focus
  - User/Customer pickup process
  - Security Service PIN validation
  - Brute force protection mechanisms
  - Hardware integration and unlocking
  - Comprehensive error handling

#### Administrative Flow Diagrams:
- **`admin_login_flow_with_lanes.puml`** - Admin authentication with 2FA
  - Admin User authentication steps
  - Authentication Service validation
  - Session Service management
  - 2FA and security mechanisms
  - Comprehensive audit logging

- **`admin_system_status_flow_with_lanes.puml`** - Real-time system monitoring
  - Admin User dashboard interactions
  - Metrics Service data collection
  - Service availability checking
  - Real-time status updates
  - System alert management

- **`admin_manage_parcels_flow_with_lanes.puml`** - Comprehensive parcel management
  - Search and filter capabilities
  - Multiple parcel action handling
  - Email notification processes
  - Hardware integration for parcel operations
  - Complete audit trail logging

- **`admin_audit_logs_flow_with_lanes.puml`** - Advanced audit log management
  - Audit log filtering and search
  - Real-time monitoring capabilities
  - Compliance reporting features
  - Export and analysis tools
  - Advanced search functionality

### Swimlane Features:
- ✅ Cross-functional process visualization
- ✅ Clear responsibility boundaries between services
- ✅ Detailed error handling and exception flows
- ✅ Security and validation checkpoints
- ✅ Real-time monitoring and audit logging
- ✅ Hardware integration touchpoints

## 🏛️ Class Diagrams (`class_diagrams/`)

Object-oriented design diagrams showing system structure:

### Files:
- **`campus_locker_class_diagram.puml`** - Complete system class diagram
  - Domain entities (User, Parcel, Locker, AuditLog)
  - Value objects and enums
  - Service layer architecture
  - Data transfer objects (DTOs)
  - Repository interfaces
  - Comprehensive relationships and dependencies

### Design Patterns:
- **Repository Pattern**: Data access abstraction
- **Service Layer Pattern**: Business logic separation
- **DTO Pattern**: Data transfer objects for API boundaries
- **Value Object Pattern**: Immutable data containers

## 🗄️ Database Schemas (`database_schemas/`)

Database design and schema definitions:

### Files:
- **`main_database_schema.dbml`** - Core application database schema
  - User tables and authentication
  - Parcel management tables
  - Locker inventory and status
  - System configuration tables
- **`audit_database_schema.dbml`** - Audit and logging database schema
  - Audit trail tables
  - Security event logging
  - System monitoring data
  - Performance metrics storage

### Viewing Database Schemas:
- **Online**: [dbdiagram.io](https://dbdiagram.io/) - Load `.dbml` files directly
- **VS Code**: Database Markup Language (DBML) extension
- **CLI**: DBML CLI tools for export to SQL

## 🛠️ Tools and Rendering

### PlantUML Files (`.puml`)
- **Online**: [PlantUML Online Server](http://www.plantuml.com/plantuml/)
- **VS Code**: PlantUML extension
- **IntelliJ**: PlantUML integration plugin
- **CLI**: PlantUML JAR file

### C4 DSL Files (`.dsl`)
- **Online**: [Structurizr Express](https://structurizr.com/express)
- **VS Code**: C4 DSL Extension
- **CLI**: Structurizr CLI

### Database Markup Language (`.dbml`)
- **Online**: [dbdiagram.io](https://dbdiagram.io/)
- **VS Code**: DBML extension
- **CLI**: DBML CLI tools

## 📋 Diagram Standards

### Style Guidelines:
- ✅ Clean white background for readability
- ✅ Consistent color coding across diagrams
- ✅ Proper UML relationship notation
- ✅ Comprehensive notes and documentation
- ✅ Professional layout and organization

### Relationship Notation:
- `||--o{` : One-to-many association
- `||--||` : One-to-one association  
- `*--` : Composition (strong ownership)
- `o--` : Aggregation (weak ownership)
- `-->` : Dependency
- `..>` : Implementation/Interface usage
- `<|--` : Inheritance/Extension

## 🔄 Maintenance

### Adding New Diagrams:
1. Place in appropriate subfolder based on diagram type
2. Follow naming convention: `descriptive_name_diagram_type.puml`
3. Update this README with new diagram descriptions
4. Ensure consistent styling with existing diagrams

### File Naming Convention:
- Use lowercase with underscores: `my_new_diagram.puml`
- Include diagram type in name: `user_journey_activity.puml`
- Be descriptive: `authentication_sequence.puml`

### Subfolder Guidelines:
- **`c4_model/`**: C4 methodology files (.dsl, Level 4 .puml, documentation)
- **`activity_diagrams/`**: Process flow and workflow diagrams (.puml)
- **`class_diagrams/`**: Object-oriented design diagrams (.puml)
- **`database_schemas/`**: Database schema definitions (.dbml)

## 📊 Current File Inventory

```
docs/diagrams/
├── README.md
├── activity_diagrams/
│   ├── swimlane_flows/
│   │   ├── activity_deposit_flow_with_lanes.puml
│   │   ├── activity_pickup_flow_with_lanes.puml
│   │   ├── admin_audit_logs_flow_with_lanes.puml
│   │   ├── admin_login_flow_with_lanes.puml
│   │   ├── admin_manage_parcels_flow_with_lanes.puml
│   │   └── admin_system_status_flow_with_lanes.puml
│   ├── activity_admin_flows.puml
│   └── activity_parcel_flows.puml
├── c4_model/
│   ├── C4_LEVEL4_README.md
│   ├── campus_locker_architecture.dsl
│   └── campus_locker_code_level.puml
├── class_diagrams/
│   └── deposit_flow_class_diagram.puml
└── database_schemas/
    ├── audit_database_schema.dbml
    └── main_database_schema.dbml
```

## 📚 Related Documentation

- **Main README**: `../../README.md`
- **Architecture Overview**: `../README.md`
- **C4 Model Details**: `c4_model/C4_LEVEL4_README.md`

---

**Last Updated**: December 2024  
**Maintained By**: Architecture Team  
**Contact**: For questions about diagrams, refer to the project documentation or team lead. 