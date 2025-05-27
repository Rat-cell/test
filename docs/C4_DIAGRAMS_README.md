# Campus Locker System v2.0 - C4 Architecture Diagrams

This directory contains comprehensive C4 architecture diagrams for the Campus Locker System v2.0, created using PlantUML with the C4 model approach.

## 📊 **Diagram Hierarchy (Step by Step)**

### 1. **System Context Diagram** (Level 1 - Highest Level)
- **Shows**: The big picture - who uses the system and what external systems it connects to
- **Audience**: Everyone (business stakeholders, architects, developers)
- **Focus**: System boundaries and external dependencies

### 2. **Container Diagram** (Level 2 - System Decomposition)
- **Shows**: The major containers (applications, databases) that make up the system
- **Audience**: Technical stakeholders, architects, senior developers
- **Focus**: Technology choices and container interactions

### 3. **Component Diagram** (Level 3 - Container Internals)
- **Shows**: The major components within each container
- **Audience**: Architects, developers working on the system
- **Focus**: Component responsibilities and interactions

### 4. **Hexagonal Architecture Diagram** (Level 3 - Alternative View)
- **Shows**: Ports and adapters pattern implementation
- **Audience**: Developers, architects focused on clean architecture
- **Focus**: Domain isolation and dependency inversion

### 5. **Code Diagram** (Level 4 - Implementation Details)
- **Shows**: Actual code structure and file organization
- **Audience**: Developers implementing and maintaining the code
- **Focus**: Code organization and package dependencies

## 🚀 **How to Use These Diagrams**

### Option 1: Online PlantUML Editor
1. Go to [PlantUML Online Server](http://www.plantuml.com/plantuml/uml/)
2. Copy any diagram section from `c4-diagrams.puml`
3. Paste into the editor
4. View the rendered diagram

### Option 2: VS Code Extension
1. Install "PlantUML" extension in VS Code
2. Open `c4-diagrams.puml`
3. Use `Alt+D` to preview diagrams
4. Export as PNG/SVG as needed

### Option 3: Local PlantUML Installation
```bash
# Install PlantUML (requires Java)
brew install plantuml  # macOS
# or download from https://plantuml.com/download

# Generate diagrams
plantuml docs/c4-diagrams.puml
```

### Option 4: Docker PlantUML
```bash
# Generate all diagrams using Docker
docker run --rm -v $(pwd):/data plantuml/plantuml docs/c4-diagrams.puml
```

## 📋 **Available Diagrams**

### 1. **C4_Context_Diagram**
```plantuml
@startuml C4_Context_Diagram
!include https://raw.githubusercontent.com/plantuml-stdlib/C4-PlantUML/master/C4_Context.puml
title Campus Locker System v2.0 - System Context Diagram
...
@enduml
```

**What it shows:**
- Students, delivery personnel, and administrators as users
- Campus Locker System as the main system
- External dependencies: Email service, databases, monitoring

### 2. **C4_Container_Diagram**
```plantuml
@startuml C4_Container_Diagram
!include https://raw.githubusercontent.com/plantuml-stdlib/C4-PlantUML/master/C4_Container.puml
title Campus Locker System v2.0 - Container Diagram
...
@enduml
```

**What it shows:**
- Nginx reverse proxy for security and routing
- Flask web application as the main container
- Redis for caching and session management
- SQLite databases for data persistence
- MailHog for email testing

### 3. **C4_Component_Diagram_WebApp**
```plantuml
@startuml C4_Component_Diagram_WebApp
!include https://raw.githubusercontent.com/plantuml-stdlib/C4-PlantUML/master/C4_Component.puml
title Campus Locker System v2.0 - Web Application Components
...
@enduml
```

**What it shows:**
- **Presentation Layer**: Web routes, API routes, health endpoints
- **Service Layer**: 6 service classes for business operations
- **Business Layer**: 6 domain classes with business logic
- **Persistence Layer**: SQLAlchemy models
- **Adapter Layer**: Database, email, and audit adapters

### 4. **C4_Hexagonal_Architecture**
```plantuml
@startuml C4_Hexagonal_Architecture
!include https://raw.githubusercontent.com/plantuml-stdlib/C4-PlantUML/master/C4_Component.puml
title Campus Locker System v2.0 - Hexagonal Architecture Details
...
@enduml
```

**What it shows:**
- **Primary Ports**: Driving adapters (web, API, health)
- **Application Core**: Use cases and domain entities
- **Secondary Ports**: Driven adapters (persistence, email, audit, cache)
- **External Systems**: Databases, email service, cache
- **Dependency Flow**: Outside-in dependency direction

### 5. **C4_Code_Diagram**
```plantuml
@startuml C4_Code_Diagram
!include https://raw.githubusercontent.com/plantuml-stdlib/C4-PlantUML/master/C4_Component.puml
title Campus Locker System v2.0 - Code Level Implementation
...
@enduml
```

**What it shows:**
- **Actual Files**: routes.py, services.py, domain.py, models.py, etc.
- **Package Structure**: Presentation, Service, Business, Persistence, Adapter layers
- **Dependencies**: Import relationships between files
- **Testing Structure**: Test files and their coverage

## 🏗️ **Architecture Principles Visualized**

### Hexagonal Architecture Benefits
1. **Domain Isolation**: Business logic is protected from external concerns
2. **Testability**: Each layer can be tested independently
3. **Flexibility**: Easy to swap implementations (database, email service, etc.)
4. **Dependency Inversion**: Dependencies point inward toward the domain

### Layer Responsibilities
- **Presentation**: HTTP handling, request/response formatting
- **Service**: Use case orchestration, transaction boundaries
- **Business**: Domain logic, business rules, entities
- **Persistence**: Data access, ORM models
- **Adapter**: External system integration

## 📖 **Reading the Diagrams**

### Symbols and Colors
- **Blue Boxes**: Internal components/containers
- **Gray Boxes**: External systems
- **Green Boxes**: Databases
- **Arrows**: Relationships and data flow
- **Boundaries**: System/container/component boundaries

### Relationship Types
- **Uses**: Component dependency
- **Implements**: Interface implementation
- **Connects to**: External system connection
- **Triggers**: Use case activation

## 🔄 **Keeping Diagrams Updated**

When you modify the system:

1. **Add New Components**: Update the relevant C4 level
2. **Change Dependencies**: Update relationship arrows
3. **New External Systems**: Add to context and container diagrams
4. **Refactor Code**: Update the code diagram structure

## 💡 **Best Practices**

1. **Start High Level**: Always begin with context diagram
2. **Progressive Detail**: Move down levels as needed
3. **Audience Specific**: Choose the right level for your audience
4. **Keep Current**: Update diagrams with code changes
5. **Version Control**: Include diagrams in your repository

## 🎯 **Use Cases for Each Diagram**

### Context Diagram
- Project kickoff presentations
- Stakeholder alignment
- System scope definition
- Integration planning

### Container Diagram
- Architecture reviews
- Technology decisions
- Deployment planning
- DevOps setup

### Component Diagram
- Development planning
- Code organization
- Team responsibilities
- Refactoring decisions

### Hexagonal Architecture
- Architecture training
- Clean code discussions
- Design pattern implementation
- Dependency management

### Code Diagram
- Onboarding new developers
- Code review preparation
- Refactoring planning
- Test coverage analysis

---

**These diagrams provide a complete architectural view of the Campus Locker System v2.0, from high-level context down to implementation details. Use them to understand, communicate, and evolve the system architecture.** 🏗️ 