workspace "Campus Locker System" "Graduate-level software architecture demonstration using hexagonal architecture pattern" {

    !identifiers hierarchical

    model {
        # External actors
        webUser = person "Web User" "Students and staff who deposit and retrieve parcels" "User"
        adminUser = person "Admin User" "System administrators who manage the locker system" "Admin"
        emailService = softwareSystem "Email Service" "External SMTP service for notifications" "External"
        externalAPIs = softwareSystem "External APIs" "Third-party services and integrations" "External"
        
        # Main Campus Locker System
        campusLockerSystem = softwareSystem "Campus Locker System" "Automated parcel management system with hexagonal architecture" {
            
            # Presentation Layer
            webInterface = container "Web Interface" "Flask-based web application with Jinja2 templates" "Python, Flask, HTML/CSS" "Presentation"
            apiInterface = container "API Interface" "RESTful API endpoints for system integration" "Python, Flask, REST" "Presentation"
            adminDashboard = container "Admin Dashboard" "Administrative interface for system management" "Python, Flask, HTML/CSS" "Presentation"
            
            # Service Layer (Application Services)
            parcelService = container "Parcel Service" "Orchestrates parcel lifecycle operations" "Python" "Service"
            lockerService = container "Locker Service" "Manages locker allocation and status" "Python" "Service"
            authService = container "Authentication Service" "Handles admin authentication and sessions" "Python" "Service"
            notificationService = container "Notification Service" "Manages email notifications and reminders" "Python" "Service"
            auditService = container "Audit Service" "Handles compliance logging and monitoring" "Python" "Service"
            pinService = container "PIN Service" "Manages secure PIN generation and validation" "Python" "Service"
            
            # Business Layer (Domain Logic)
            parcelManager = container "Parcel Manager" "Core parcel business logic and rules" "Python" "Business"
            lockerManager = container "Locker Manager" "Core locker management business logic" "Python" "Business"
            securityManager = container "Security Manager" "Security policies and PIN management logic" "Python" "Business"
            notificationManager = container "Notification Manager" "Email notification business rules" "Python" "Business"
            auditManager = container "Audit Manager" "Audit trail and compliance logic" "Python" "Business"
            
            # Persistence Layer (Repository Pattern)
            parcelRepository = container "Parcel Repository" "Data access layer for parcel operations" "Python, SQLAlchemy" "Repository"
            lockerRepository = container "Locker Repository" "Data access layer for locker operations" "Python, SQLAlchemy" "Repository"
            adminRepository = container "Admin Repository" "Data access layer for admin user operations" "Python, SQLAlchemy" "Repository"
            auditRepository = container "Audit Repository" "Data access layer for audit operations" "Python, SQLAlchemy" "Repository"
            
            # Database Layer
            mainDatabase = container "Main Database" "Primary operational database with ACID compliance" "SQLite with WAL mode" "Database"
            auditDatabase = container "Audit Database" "Separate tamper-proof audit trail database" "SQLite" "Database"
            backupSystem = container "Backup System" "Automated database backup and recovery" "Shell scripts, Cron" "Database"
            
            # Adapter Layer
            emailAdapter = container "Email Adapter" "SMTP adapter for email service integration" "Python, SMTP" "Adapter"
            auditAdapter = container "Audit Adapter" "Logging adapter for audit trail management" "Python, Logging" "Adapter"
            databaseAdapter = container "Database Adapter" "SQLAlchemy adapter for database operations" "Python, SQLAlchemy ORM" "Adapter"
        }
        
        # Relationships - External to Presentation
        webUser -> campusLockerSystem.webInterface "Uses web interface to deposit and retrieve parcels" "HTTPS"
        adminUser -> campusLockerSystem.adminDashboard "Manages system through admin interface" "HTTPS"
        externalAPIs -> campusLockerSystem.apiInterface "Integrates via REST API" "HTTPS/JSON"
        campusLockerSystem.emailAdapter -> emailService "Sends notifications via SMTP" "SMTP"
        
        # Presentation to Service Layer
        campusLockerSystem.webInterface -> campusLockerSystem.parcelService "Orchestrates parcel operations"
        campusLockerSystem.webInterface -> campusLockerSystem.lockerService "Manages locker allocation"
        campusLockerSystem.adminDashboard -> campusLockerSystem.authService "Authenticates admin users"
        campusLockerSystem.adminDashboard -> campusLockerSystem.auditService "Views audit logs"
        campusLockerSystem.apiInterface -> campusLockerSystem.parcelService "Exposes parcel API endpoints"
        campusLockerSystem.apiInterface -> campusLockerSystem.lockerService "Exposes locker API endpoints"
        
        # Service to Business Layer
        campusLockerSystem.parcelService -> campusLockerSystem.parcelManager "Applies parcel business rules"
        campusLockerSystem.lockerService -> campusLockerSystem.lockerManager "Applies locker business rules"
        campusLockerSystem.authService -> campusLockerSystem.securityManager "Validates authentication"
        campusLockerSystem.notificationService -> campusLockerSystem.notificationManager "Processes notification rules"
        campusLockerSystem.auditService -> campusLockerSystem.auditManager "Applies audit policies"
        campusLockerSystem.pinService -> campusLockerSystem.securityManager "Generates and validates PINs"
        
        # Service to Repository Layer (Repository Pattern)
        campusLockerSystem.parcelService -> campusLockerSystem.parcelRepository "Persists parcel data"
        campusLockerSystem.lockerService -> campusLockerSystem.lockerRepository "Persists locker data"
        campusLockerSystem.authService -> campusLockerSystem.adminRepository "Manages admin user data"
        campusLockerSystem.auditService -> campusLockerSystem.auditRepository "Stores audit records"
        
        # Cross-Service Coordination (within Service Layer)
        campusLockerSystem.parcelService -> campusLockerSystem.lockerService "Coordinates locker allocation and release"
        campusLockerSystem.parcelService -> campusLockerSystem.pinService "Requests PIN generation and validation"
        campusLockerSystem.parcelService -> campusLockerSystem.notificationService "Requests email notifications"
        campusLockerSystem.parcelService -> campusLockerSystem.auditService "Requests audit logging"
        
        # Repository to Database Layer
        campusLockerSystem.parcelRepository -> campusLockerSystem.databaseAdapter "Uses ORM for data access"
        campusLockerSystem.lockerRepository -> campusLockerSystem.databaseAdapter "Uses ORM for data access"
        campusLockerSystem.adminRepository -> campusLockerSystem.databaseAdapter "Uses ORM for data access"
        campusLockerSystem.auditRepository -> campusLockerSystem.databaseAdapter "Uses ORM for audit data"
        
        # Database Adapter to Databases
        campusLockerSystem.databaseAdapter -> campusLockerSystem.mainDatabase "Stores operational data"
        campusLockerSystem.databaseAdapter -> campusLockerSystem.auditDatabase "Stores audit trail"
        campusLockerSystem.backupSystem -> campusLockerSystem.mainDatabase "Creates automated backups"
        
        # Service to Adapter Layer
        campusLockerSystem.notificationService -> campusLockerSystem.emailAdapter "Sends email notifications"
        campusLockerSystem.auditService -> campusLockerSystem.auditAdapter "Logs system events"
        
        # Cross-cutting relationships
        campusLockerSystem.auditService -> campusLockerSystem.auditDatabase "Direct audit logging for security"
    }

    views {
        systemLandscape "SystemLandscape" {
            include *
            autolayout lr
            description "System landscape showing the Campus Locker System in context with external users and services"
        }
        
        systemContext campusLockerSystem "SystemContext" {
            include *
            autolayout lr
            description "System context diagram showing external actors and their interactions with the Campus Locker System"
        }
        
        container campusLockerSystem "HexagonalArchitecture" {
            include *
            autolayout tb
            description "Complete hexagonal architecture showing all 6 layers with color-coded components"
        }
        
        container campusLockerSystem "HexagonalCore" {
            include campusLockerSystem.parcelService campusLockerSystem.lockerService campusLockerSystem.authService
            include campusLockerSystem.parcelManager campusLockerSystem.lockerManager campusLockerSystem.securityManager
            include campusLockerSystem.parcelRepository campusLockerSystem.lockerRepository campusLockerSystem.adminRepository
            include campusLockerSystem.databaseAdapter campusLockerSystem.mainDatabase campusLockerSystem.auditDatabase
            autolayout lr
            description "Core hexagonal flow: Service → Business → Repository → Database layers"
        }
        
        container campusLockerSystem "HexagonalWithAdapters" {
            include campusLockerSystem.webInterface campusLockerSystem.apiInterface
            include campusLockerSystem.parcelService campusLockerSystem.notificationService
            include campusLockerSystem.emailAdapter campusLockerSystem.auditAdapter
            include emailService
            autolayout tb
            description "Hexagonal ports and adapters: External interfaces connecting through adapters"
        }
        
        container campusLockerSystem "PresentationLayer" {
            include campusLockerSystem.webInterface campusLockerSystem.apiInterface campusLockerSystem.adminDashboard
            include campusLockerSystem.parcelService campusLockerSystem.lockerService campusLockerSystem.authService campusLockerSystem.notificationService campusLockerSystem.auditService campusLockerSystem.pinService
            autolayout tb
            description "Presentation layer containers and their connections to the service layer"
        }
        
        container campusLockerSystem "ServiceAndBusinessLayers" {
            include campusLockerSystem.parcelService campusLockerSystem.lockerService campusLockerSystem.authService campusLockerSystem.notificationService campusLockerSystem.auditService campusLockerSystem.pinService
            include campusLockerSystem.parcelManager campusLockerSystem.lockerManager campusLockerSystem.securityManager campusLockerSystem.notificationManager campusLockerSystem.auditManager
            include campusLockerSystem.parcelRepository campusLockerSystem.lockerRepository campusLockerSystem.adminRepository campusLockerSystem.auditRepository
            autolayout tb
            description "Service layer orchestrating business logic through repository pattern"
        }
        
        container campusLockerSystem "DataArchitecture" {
            include campusLockerSystem.parcelRepository campusLockerSystem.lockerRepository campusLockerSystem.adminRepository campusLockerSystem.auditRepository
            include campusLockerSystem.databaseAdapter campusLockerSystem.mainDatabase campusLockerSystem.auditDatabase campusLockerSystem.backupSystem
            autolayout tb
            description "Data architecture showing repository pattern and dual database design"
        }
        
        dynamic campusLockerSystem "ParcelDeposit" "Parcel deposit workflow showing hexagonal architecture in action" {
            webUser -> campusLockerSystem.webInterface "Submits deposit form"
            campusLockerSystem.webInterface -> campusLockerSystem.parcelService "Request parcel deposit"
            campusLockerSystem.parcelService -> campusLockerSystem.lockerService "Find available locker"
            campusLockerSystem.lockerService -> campusLockerSystem.lockerManager "Apply locker business rules"
            campusLockerSystem.parcelService -> campusLockerSystem.pinService "Request secure PIN"
            campusLockerSystem.pinService -> campusLockerSystem.securityManager "Generate secure PIN"
            campusLockerSystem.parcelService -> campusLockerSystem.parcelRepository "Create parcel record"
            campusLockerSystem.parcelRepository -> campusLockerSystem.databaseAdapter "Persist data"
            campusLockerSystem.databaseAdapter -> campusLockerSystem.mainDatabase "Store in database"
            campusLockerSystem.parcelService -> campusLockerSystem.auditService "Log deposit event"
            campusLockerSystem.auditService -> campusLockerSystem.auditDatabase "Record audit trail"
            campusLockerSystem.parcelService -> campusLockerSystem.notificationService "Send confirmation"
            campusLockerSystem.notificationService -> campusLockerSystem.emailAdapter "Send email"
            campusLockerSystem.emailAdapter -> emailService "Deliver notification"
            autolayout tb
        }
        
        dynamic campusLockerSystem "ParcelPickup" "Parcel pickup workflow demonstrating security and audit features" {
            webUser -> campusLockerSystem.webInterface "Enters PIN for pickup"
            campusLockerSystem.webInterface -> campusLockerSystem.parcelService "Request parcel pickup"
            campusLockerSystem.parcelService -> campusLockerSystem.pinService "Validate PIN"
            campusLockerSystem.pinService -> campusLockerSystem.securityManager "Validate PIN against hash"
            campusLockerSystem.parcelService -> campusLockerSystem.parcelManager "Verify parcel status"
            campusLockerSystem.parcelService -> campusLockerSystem.parcelRepository "Update parcel status"
            campusLockerSystem.parcelRepository -> campusLockerSystem.databaseAdapter "Persist changes"
            campusLockerSystem.databaseAdapter -> campusLockerSystem.mainDatabase "Update database"
            campusLockerSystem.parcelService -> campusLockerSystem.lockerService "Release locker"
            campusLockerSystem.lockerService -> campusLockerSystem.lockerManager "Apply release business rules"
            campusLockerSystem.parcelService -> campusLockerSystem.auditService "Log pickup event"
            campusLockerSystem.auditService -> campusLockerSystem.auditDatabase "Record audit trail"
            campusLockerSystem.parcelService -> campusLockerSystem.notificationService "Send pickup confirmation"
            campusLockerSystem.notificationService -> campusLockerSystem.emailAdapter "Send email"
            campusLockerSystem.emailAdapter -> emailService "Deliver notification"
            autolayout tb
        }

        styles {
            element "Person" {
                shape person
                background #08427b
                color #ffffff
            }
            element "User" {
                background #1168bd
                color #ffffff
            }
            element "Admin" {
                background #999999
                color #ffffff
            }
            element "Software System" {
                background #1168bd
                color #ffffff
            }
            element "External" {
                background #999999
                color #ffffff
            }
            element "Container" {
                background #438dd5
                color #ffffff
            }
            element "Presentation" {
                background #85BBF0
                color #000000
            }
            element "Service" {
                background #F4D03F
                color #000000
            }
            element "Business" {
                background #82E0AA
                color #000000
            }
            element "Repository" {
                background #F1948A
                color #000000
            }
            element "Database" {
                background #BB8FCE
                color #ffffff
                shape cylinder
            }
            element "Adapter" {
                background #F8C471
                color #000000
            }
            relationship "Relationship" {
                routing orthogonal
            }
        }
        
        themes https://static.structurizr.com/themes/amazon-web-services-2020.04.30/theme.json
    }
    
    configuration {
        scope softwaresystem
    }
} 