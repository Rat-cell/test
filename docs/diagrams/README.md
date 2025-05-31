# Campus Locker System - Architecture Diagrams

This directory contains comprehensive architectural documentation for the Campus Locker System using modern, industry-standard diagramming approaches.

## 📁 **File Overview**

### 🏗️ **Architecture Diagrams**
- **`campus_locker_architecture.dsl`** - Complete system architecture using [Structurizr DSL](https://structurizr.com/dsl)

### 🗄️ **Database Schemas**
- **`main_database_schema.dbml`** - Operational database schema for [dbdiagram.io](https://dbdiagram.io/)
- **`audit_database_schema.dbml`** - Audit trail database schema for [dbdiagram.io](https://dbdiagram.io/)

## 🏗️ **System Architecture (Structurizr DSL)**

The main architecture model creates multiple views of our hexagonal architecture:

### **Available Views**
1. **System Landscape** - Complete system in context
2. **System Context** - External interactions  
3. **Hexagonal Architecture** - All containers by layer
4. **Hexagonal Core** - Core business flow
5. **Hexagonal With Adapters** - External interfaces and adapters
6. **Presentation Layer** - UI and API components
7. **Service & Business Layers** - Core application logic
8. **Data Architecture** - Repository pattern and databases
9. **Parcel Deposit Workflow** - Dynamic sequence view
10. **Parcel Pickup Workflow** - Security and audit flow

### **Hexagonal Architecture Implementation**

```
┌─────────────────┬─────────────────┬─────────────────┐
│  Presentation   │    Service      │    Business     │
│  Layer          │    Layer        │    Layer        │
├─────────────────┼─────────────────┼─────────────────┤
│ • Web Interface │ • Parcel Svc    │ • Parcel Mgr    │
│ • API Interface │ • Locker Svc    │ • Locker Mgr    │
│ • Admin Dash    │ • Auth Svc      │ • Security Mgr  │
└─────────────────┴─────────────────┴─────────────────┘
┌─────────────────┬─────────────────┬─────────────────┐
│  Repository     │    Database     │    Adapter      │
│  Layer          │    Layer        │    Layer        │
├─────────────────┼─────────────────┼─────────────────┤
│ • Parcel Repo   │ • Main DB       │ • Email Adapter │
│ • Locker Repo   │ • Audit DB      │ • Audit Adapter │
│ • Admin Repo    │ • Backup Sys    │ • DB Adapter    │
└─────────────────┴─────────────────┴─────────────────┘
```

## 🗄️ **Database Architecture (DBML)**

### **Dual Database Design**

The system uses **two separate databases** for operational and audit data:

#### **Main Database** (`main_database_schema.dbml`)
- 🏗️ **4 Tables**: locker, parcel, admin_user, locker_sensor_data
- 🔗 **Relationships**: Foreign keys and business constraints
- 📈 **Performance**: Strategic indexing for 4-25ms response times
- 🔒 **Security**: Advanced PIN management with email-based generation

#### **Audit Database** (`audit_database_schema.dbml`)  
- 📋 **1 Table**: audit_log (immutable trail)
- 🛡️ **Security**: Tamper-proof compliance logging
- 📊 **Rich Context**: JSON details for forensic analysis
- 🎯 **Monitoring**: Security and operational event tracking

## 🚀 **How to Use**

### **Structurizr DSL Architecture**

#### **Option 1: Online Editor (Quick)**
1. Visit https://structurizr.com/dsl
2. Copy contents of `campus_locker_architecture.dsl`
3. Paste and render - select different views from dropdown

#### **Option 2: Structurizr Lite (Recommended)**
```bash
# Download and run locally
wget https://github.com/structurizr/lite/releases/latest/download/structurizr-lite.war
java -jar structurizr-lite.war

# Or use Docker
docker run -it --rm -p 8080:8080 -v $(pwd):/usr/local/structurizr structurizr/lite
```

#### **Option 3: Export to Other Formats**
```bash
# Download CLI
wget https://github.com/structurizr/cli/releases/latest/download/structurizr-cli.zip

# Export options
./structurizr-cli export -workspace campus_locker_architecture.dsl -format plantuml
./structurizr-cli export -workspace campus_locker_architecture.dsl -format mermaid
./structurizr-cli export -workspace campus_locker_architecture.dsl -format plantuml/c4plantuml
```

### **DBML Database Schemas**

#### **Interactive Database Diagrams**
1. Visit https://dbdiagram.io/
2. Create new diagram
3. Copy contents of either:
   - `main_database_schema.dbml` - Operational database
   - `audit_database_schema.dbml` - Audit database
4. Paste and view interactive schema with relationships

## 🎨 **Visual Features**

### **Architecture Diagrams**
- 🎨 **Color-coded layers** for hexagonal architecture
- 📊 **Multiple view types** (static structure + dynamic workflows)
- 🔄 **Export capabilities** to PNG, SVG, PlantUML, Mermaid
- 🎯 **Professional styling** with AWS themes

### **Database Diagrams**  
- 🔗 **Interactive relationships** and foreign keys
- 📝 **Comprehensive documentation** in field notes
- 🔍 **Business rules** and constraints visualized
- 📈 **Performance indexes** and optimization notes

## 🎓 **Educational Value**

These diagrams demonstrate **graduate-level software architecture**:

### **Architectural Patterns**
- 🏗️ **Hexagonal Architecture** - Clean separation of concerns
- 🔄 **Repository Pattern** - Data access abstraction  
- 🎯 **Service Orchestration** - Business operation coordination
- 🔌 **Adapter Pattern** - External system integration
- 📊 **Domain-Driven Design** - Rich business models

### **Database Design**
- 🗄️ **Dual-database architecture** - Operational vs audit separation
- 🔒 **Advanced security** - Multi-layered PIN security, audit trails
- 📈 **Performance optimization** - Strategic indexing, nullable fields
- 🎯 **Real-world complexity** - Comprehensive business rules

### **System Design**
- 🔐 **Security by design** - Authentication, authorization, audit
- 📊 **Performance engineering** - Sub-25ms response times
- 🎯 **Scalability patterns** - Clean architecture for growth
- 📋 **Compliance features** - Audit trails, data retention

## 📚 **Further Reading**

### **Architecture Resources**
- [Structurizr DSL Documentation](https://structurizr.com/dsl)
- [C4 Model](https://c4model.com/)
- [Hexagonal Architecture](https://alistair.cockburn.us/hexagonal-architecture/)
- [Domain-Driven Design](https://martinfowler.com/bliki/DomainDrivenDesign.html)
- [Repository Pattern](https://martinfowler.com/eaaCatalog/repository.html)

### **Database Resources**
- [dbdiagram.io Documentation](https://docs.dbdiagram.io/)
- [Database Design Patterns](https://en.wikipedia.org/wiki/Database_design)
- [SQLite Performance](https://www.sqlite.org/performance.html)

---

**💡 Pro Tip**: Use the architecture and database diagrams together to understand both the logical structure (hexagonal architecture) and physical data design (dual databases) of a production-ready system! 