# C4 Level 4: Code Diagrams - Campus Locker System

##  Overview

This document provides **C4 Level 4 (Code) diagrams** for the Campus Locker System using **UML Class Diagrams**. These diagrams show the implementation details of the components defined in our C3 diagrams, representing the actual Python classes that would implement the architecture.

##  Files

- **`campus_locker_code_level.puml`** - PlantUML file with complete class diagrams
- **`C4_LEVEL4_README.md`** - This documentation file

##  Architecture Mapping

### **C3 → C4 Mapping**

The Level 4 diagrams implement the components from our Level 3 diagrams:

| **C3 Component** | **C4 Implementation Classes** |
|------------------|-------------------------------|
| **Web Interface Components** | `HomeController`, `ParcelWebController`, `StatusController`, `TemplateEngine`, `FormValidator`, `ErrorHandler` |
| **Parcel Service Components** | `ParcelController`, `ParcelOrchestrator`, `ParcelValidator`, `ParcelEventHandler`, `NotificationTrigger` |
| **Auth Service Components** | `AuthController`, `SessionManager`, `PasswordValidator`, `LoginAttemptTracker`, `AuthorizationEngine` |

##  Key Design Patterns Demonstrated

### **1. Hexagonal Architecture**
- **Clean dependency flow**: Outer layers depend on inner layers
- **Dependency Inversion**: Abstractions depend on implementations
- **Ports & Adapters**: Clear separation of concerns

### **2. Repository Pattern**
- **BaseRepository**: Abstract base with common operations
- **Specific Repositories**: `ParcelRepository`, `AdminRepository`, `LockerRepository`
- **Entity Mapping**: Clean domain object persistence

### **3. MVC Pattern**
- **Controllers**: Handle HTTP requests (`HomeController`, `ParcelWebController`)
- **Views**: Template rendering (`TemplateEngine`)
- **Models**: Domain entities (`Parcel`, `AdminUser`, `Locker`)

### **4. Domain-Driven Design**
- **Value Objects**: `Dimensions`, `ValidationResult`
- **Entities**: `Parcel`, `AdminUser`, `Locker`
- **Enums**: `ParcelStatus`, `LockerSize`

##  How to Use

### **Option 1: Online PlantUML Editor**
1. Visit [PlantUML Online](http://www.plantuml.com/plantuml/uml/)
2. Copy contents of `campus_locker_code_level.puml`
3. Paste and generate diagram
4. Export as PNG/SVG/PDF

### **Option 2: Local PlantUML**
```bash
# Install PlantUML (requires Java)
wget https://github.com/plantuml/plantuml/releases/latest/download/plantuml.jar

# Generate diagram
java -jar plantuml.jar campus_locker_code_level.puml

# Or with specific format
java -jar plantuml.jar -tpng campus_locker_code_level.puml
java -jar plantuml.jar -tsvg campus_locker_code_level.puml
```

### **Option 3: VS Code Integration**
```bash
# Install PlantUML extension
code --install-extension plantuml.plantuml

# Open .puml file in VS Code
# Use Ctrl+Shift+P → "PlantUML: Preview Current Diagram"
```

### **Option 4: Python Integration**
```bash
# Install plantuml Python package
pip install plantuml

# Generate from Python
from plantuml import PlantUML
server = PlantUML(url='http://www.plantuml.com/plantuml/img/')
with open('campus_locker_code_level.puml', 'r') as f:
    diagram = server.processes(f.read())
```

##  Diagram Structure

### **Package Organization**

1. **Presentation Layer** - Web controllers and UI components
2. **Service Layer** - Application services and orchestration
3. **Business Layer** - Domain models and business logic
4. **Repository Layer** - Data access abstractions
5. **Data Types** - Value objects and enums

### **Class Details**

Each class includes:
- **Attributes**: Private (-) and public (+) fields with types
- **Methods**: Public operations, constructors, and private helpers
- **Relationships**: Dependencies, inheritance, and associations
- **Types**: Python-specific type hints (str, bool, datetime, etc.)

##  Relationships Explained

### **Dependency Direction (Hexagonal Architecture)**
```
Presentation → Service → Business → Repository
    ↓           ↓         ↓         ↓
   Web       Parcel    Domain    Data
Interface  Controller  Models   Access
```

### **Key Relationships**
- **Composition**: Controllers contain orchestrators
- **Inheritance**: Repositories extend BaseRepository
- **Association**: Entities reference value objects
- **Dependency**: Services depend on repositories

##  Implementation Insights

### **Real Python Implementation**

The classes represent realistic Python Flask implementation:

```python
# Example: ParcelController (from diagram)
class ParcelController:
    def __init__(self, orchestrator: ParcelOrchestrator):
        self.orchestrator = orchestrator
        self.validator = ParcelValidator()
        self.logger = logging.getLogger(__name__)
    
    def deposit_parcel(self, request: DepositRequest) -> DepositResponse:
        # Validate → Orchestrate → Return
        validation = self.validator.validate_deposit_request(request)
        if not validation.is_valid:
            return DepositResponse(success=False, errors=validation.errors)
        
        result = self.orchestrator.orchestrate_deposit(request)
        self.logger.info(f"Parcel deposited: {result.tracking_id}")
        return DepositResponse(success=True, tracking_id=result.tracking_id)
```

### **Technology Stack**
- **Web Framework**: Flask (controllers, routing)
- **Templates**: Jinja2 (template engine)
- **ORM**: SQLAlchemy (repository pattern)
- **Security**: bcrypt (password hashing)
- **Validation**: WTForms (form validation)
- **Logging**: Python logging (audit trails)

##  Scalability Considerations

### **Design Decisions**
1. **Microservice Ready**: Service layer can be extracted to separate services
2. **Database Agnostic**: Repository pattern abstracts data access
3. **Event-Driven**: Event handlers enable async processing
4. **Caching Friendly**: Clear read/write separation
5. **Testing Friendly**: Dependency injection enables mocking

### **Performance Patterns**
- **Lazy Loading**: Repository methods load data on demand
- **Caching**: Session and permission caching in auth service
- **Async Events**: Event handlers for non-blocking notifications
- **Connection Pooling**: Database session management

##  Testing Strategy

### **Unit Testing**
Each class can be unit tested independently:
```python
def test_parcel_validator():
    validator = ParcelValidator(business_rules=mock_rules)
    result = validator.validate_deposit_request(valid_request)
    assert result.is_valid == True

def test_parcel_repository():
    repo = ParcelRepository(db_session=mock_session)
    parcel = repo.save(test_parcel)
    assert parcel.parcel_id is not None
```

### **Integration Testing**
Test component interactions:
```python
def test_parcel_deposit_flow():
    controller = ParcelController(orchestrator=real_orchestrator)
    response = controller.deposit_parcel(deposit_request)
    assert response.success == True
    assert response.tracking_id is not None
```

##  Comparison with C3 Level

| **Aspect** | **C3 (Component)** | **C4 (Code)** |
|------------|-------------------|---------------|
| **Audience** | Architects, Senior Developers | Developers, Implementers |
| **Detail Level** | Component responsibilities | Class methods and attributes |
| **Stability** | Changes with architecture | Changes with implementation |
| **Purpose** | Design communication | Implementation guidance |

##  Further Reading

### **Design Patterns**
- [Repository Pattern](https://martinfowler.com/eaaCatalog/repository.html)
- [MVC Pattern](https://en.wikipedia.org/wiki/Model%E2%80%93view%E2%80%93controller)
- [Hexagonal Architecture](https://alistair.cockburn.us/hexagonal-architecture/)
- [Domain-Driven Design](https://martinfowler.com/bliki/DomainDrivenDesign.html)

### **Python Implementation**
- [Flask Documentation](https://flask.palletsprojects.com/)
- [SQLAlchemy ORM](https://docs.sqlalchemy.org/en/14/orm/)
- [PlantUML Documentation](https://plantuml.com/)

---

** Pro Tip**: Use this Level 4 diagram as a **coding guide** when implementing the actual Python classes. The detailed method signatures and relationships provide a clear roadmap for development!

##  Next Steps

1. **Review the PlantUML diagram** to understand class structure
2. **Generate visual diagrams** using your preferred tool
3. **Use as implementation guide** for actual Python coding
4. **Update diagrams** as implementation evolves
5. **Integrate with documentation** for complete architectural coverage 