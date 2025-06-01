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
            webInterface = container "Web Interface" "Flask-based web application with Jinja2 templates" "Python, Flask, HTML/CSS" "Presentation" {
                homeController = component "Home Controller" "Handles main page requests and navigation" "Python Flask Controller"
                parcelController = component "Parcel Web Controller" "Handles parcel deposit/pickup web forms" "Python Flask Controller"
                statusController = component "Status Controller" "Handles parcel status lookup requests" "Python Flask Controller"
                templateEngine = component "Template Engine" "Renders HTML templates with Jinja2" "Python Jinja2 Templates"
                formValidator = component "Form Validator" "Validates web form inputs" "Python WTForms"
                staticAssetHandler = component "Static Asset Handler" "Serves CSS, JS, and image files" "Python Flask Static Handler"
                errorHandler = component "Error Handler" "Handles application errors gracefully" "Python Flask Error Handler"
            }
            apiInterface = container "API Interface" "RESTful API endpoints for system integration" "Python, Flask, REST" "Presentation"
            adminDashboard = container "Admin Dashboard" "Administrative interface for system management" "Python, Flask, HTML/CSS" "Presentation"
            
            # Service Layer (Application Services)
            parcelService = container "Parcel Service" "Orchestrates parcel lifecycle operations" "Python" "Service" {
                parcelController = component "Parcel Controller" "Handles parcel operation requests" "Python Flask Controller"
                parcelOrchestrator = component "Parcel Orchestrator" "Coordinates complex parcel workflows" "Python Service Class"
                parcelValidator = component "Parcel Validator" "Validates parcel data and business rules" "Python Validator"
                parcelEventHandler = component "Parcel Event Handler" "Handles parcel lifecycle events" "Python Event Handler"
                parcelNotificationTrigger = component "Notification Trigger" "Triggers email notifications" "Python Component"
            }
            lockerService = container "Locker Service" "Manages locker allocation and status" "Python" "Service"
            authService = container "Authentication Service" "Handles admin authentication and sessions" "Python" "Service" {
                authController = component "Auth Controller" "Handles authentication requests" "Python Flask Controller"
                sessionManager = component "Session Manager" "Manages user sessions and tokens" "Python Session Component"
                passwordValidator = component "Password Validator" "Validates and hashes passwords" "Python Security Component"
                loginAttemptTracker = component "Login Attempt Tracker" "Tracks and prevents brute force attacks" "Python Security Component"
                authorizationEngine = component "Authorization Engine" "Handles role-based access control" "Python Authorization Component"
            }
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
        
        # Component-level relationships within Web Interface
        webUser -> campusLockerSystem.webInterface.homeController "Accesses main interface"
        campusLockerSystem.webInterface.homeController -> campusLockerSystem.webInterface.templateEngine "Renders home page"
        campusLockerSystem.webInterface.parcelController -> campusLockerSystem.webInterface.formValidator "Validates form inputs"
        campusLockerSystem.webInterface.parcelController -> campusLockerSystem.webInterface.templateEngine "Renders parcel forms"
        campusLockerSystem.webInterface.parcelController -> campusLockerSystem.parcelService.parcelController "Processes parcel requests"
        campusLockerSystem.webInterface.statusController -> campusLockerSystem.parcelService.parcelController "Queries parcel status"
        campusLockerSystem.webInterface.errorHandler -> campusLockerSystem.webInterface.templateEngine "Renders error pages"
        
        # Component-level relationships within Parcel Service
        campusLockerSystem.parcelService.parcelController -> campusLockerSystem.parcelService.parcelValidator "Validates business rules"
        campusLockerSystem.parcelService.parcelController -> campusLockerSystem.parcelService.parcelOrchestrator "Orchestrates workflow"
        campusLockerSystem.parcelService.parcelOrchestrator -> campusLockerSystem.parcelService.parcelEventHandler "Handles lifecycle events"
        campusLockerSystem.parcelService.parcelOrchestrator -> campusLockerSystem.parcelService.parcelNotificationTrigger "Triggers notifications"
        campusLockerSystem.parcelService.parcelOrchestrator -> campusLockerSystem.parcelManager "Applies business rules"
        campusLockerSystem.parcelService.parcelNotificationTrigger -> campusLockerSystem.notificationService "Requests email sending"
        
        # Component-level relationships within Auth Service
        adminUser -> campusLockerSystem.authService.authController "Submits login credentials"
        campusLockerSystem.authService.authController -> campusLockerSystem.authService.passwordValidator "Validates password"
        campusLockerSystem.authService.authController -> campusLockerSystem.authService.loginAttemptTracker "Tracks login attempts"
        campusLockerSystem.authService.authController -> campusLockerSystem.authService.sessionManager "Creates/manages sessions"
        campusLockerSystem.authService.sessionManager -> campusLockerSystem.authService.authorizationEngine "Checks permissions"
        campusLockerSystem.authService.passwordValidator -> campusLockerSystem.securityManager "Validates against policies"
        
        # Deployment Environment (Production)
        production = deploymentEnvironment "Production" {
            deploymentNode "University Network" {
                deploymentNode "DMZ Zone" {
                    deploymentNode "Load Balancer" {
                        technology "Nginx"
                        instances 2
                    }
                    deploymentNode "Web Server" {
                        technology "Linux, Docker"
                        instances 3
                        containerInstance campusLockerSystem.webInterface
                        containerInstance campusLockerSystem.apiInterface
                        containerInstance campusLockerSystem.adminDashboard
                    }
                }
                deploymentNode "Application Zone" {
                    deploymentNode "Application Server" {
                        technology "Linux, Python 3.9, Docker"
                        instances 2
                        containerInstance campusLockerSystem.parcelService
                        containerInstance campusLockerSystem.lockerService
                        containerInstance campusLockerSystem.authService
                        containerInstance campusLockerSystem.notificationService
                        containerInstance campusLockerSystem.auditService
                        containerInstance campusLockerSystem.pinService
                    }
                }
                deploymentNode "Data Zone" {
                    deploymentNode "Database Server" {
                        technology "Linux, SQLite with WAL mode"
                        instances 1
                        containerInstance campusLockerSystem.mainDatabase
                        containerInstance campusLockerSystem.auditDatabase
                        containerInstance campusLockerSystem.backupSystem
                    }
                }
            }
        }
    }

    views {
        # C4 Level 0: System Landscape
        systemLandscape "C0-SystemLandscape" {
            include *
            autolayout lr
            title "C0: System Landscape - Campus Locker System Ecosystem"
            description "High-level view showing the Campus Locker System in context with external users and services in the broader organizational ecosystem"
        }
        
        # C4 Level 1: System Context
        systemContext campusLockerSystem "C1-SystemContext" {
            include *
            autolayout lr
            title "C1: System Context - Campus Locker System"
            description "System context diagram showing external actors (users and systems) and their interactions with the Campus Locker System"
        }
        
        # C4 Level 2: Container Diagrams
        container campusLockerSystem "C2-Containers-Complete" {
            include *
            autolayout tb
            title "C2: Container Diagram - Complete Hexagonal Architecture"
            description "Complete container view showing all 6 architectural layers: Presentation, Service, Business, Repository, Database, and Adapter layers"
        }
        
        container campusLockerSystem "C2-Containers-PresentationService" {
            include campusLockerSystem.webInterface campusLockerSystem.apiInterface campusLockerSystem.adminDashboard
            include campusLockerSystem.parcelService campusLockerSystem.lockerService campusLockerSystem.authService 
            include campusLockerSystem.notificationService campusLockerSystem.auditService campusLockerSystem.pinService
            autolayout tb
            title "C2: Container Diagram - Presentation and Service Layers"
            description "Container view focusing on the presentation layer (web interfaces) and their connections to the service layer orchestration"
        }
        
        container campusLockerSystem "C2-Containers-ServiceBusiness" {
            include campusLockerSystem.parcelService campusLockerSystem.lockerService campusLockerSystem.authService 
            include campusLockerSystem.notificationService campusLockerSystem.auditService campusLockerSystem.pinService
            include campusLockerSystem.parcelManager campusLockerSystem.lockerManager campusLockerSystem.securityManager 
            include campusLockerSystem.notificationManager campusLockerSystem.auditManager
            autolayout tb
            title "C2: Container Diagram - Service and Business Logic Layers"
            description "Container view showing service layer orchestration and business logic layer with domain rules and policies"
        }
        
        container campusLockerSystem "C2-Containers-DataPersistence" {
            include campusLockerSystem.parcelRepository campusLockerSystem.lockerRepository 
            include campusLockerSystem.adminRepository campusLockerSystem.auditRepository
            include campusLockerSystem.databaseAdapter campusLockerSystem.mainDatabase 
            include campusLockerSystem.auditDatabase campusLockerSystem.backupSystem
            autolayout tb
            title "C2: Container Diagram - Data and Persistence Layers"
            description "Container view focusing on data access layer (repositories), database adapters, and persistent storage with backup systems"
        }
        
        container campusLockerSystem "C2-Containers-ExternalAdapters" {
            include campusLockerSystem.webInterface campusLockerSystem.apiInterface
            include campusLockerSystem.parcelService campusLockerSystem.notificationService
            include campusLockerSystem.emailAdapter campusLockerSystem.auditAdapter
            include emailService
            autolayout tb
            title "C2: Container Diagram - External Integration Adapters"
            description "Container view showing hexagonal ports and adapters pattern for external system integration"
        }
        
        # C4 Level 3: Component Diagrams
        component campusLockerSystem.parcelService "C3-Components-ParcelService" {
            include *
            autolayout tb
            title "C3: Component Diagram - Parcel Service Internal Structure"
            description "Detailed component view of the Parcel Service showing internal modules, handlers, and interfaces with workflow orchestration"
        }
        
        component campusLockerSystem.webInterface "C3-Components-WebInterface" {
            include *
            autolayout tb
            title "C3: Component Diagram - Web Interface Components"
            description "Detailed component view of the Web Interface showing controllers, templates, forms, and routing components with MVC pattern"
        }
        
        component campusLockerSystem.authService "C3-Components-AuthService" {
            include *
            autolayout tb
            title "C3: Component Diagram - Authentication Service"
            description "Detailed component view of the Authentication Service showing security components, session management, and validation logic with security layers"
        }
        
        # Dynamic Diagrams (Workflow/Behavioral Views)
        dynamic campusLockerSystem "Dynamic-ParcelDeposit" "Parcel deposit workflow demonstrating hexagonal architecture flow" {
            webUser -> campusLockerSystem.webInterface "1. Submits deposit form"
            campusLockerSystem.webInterface -> campusLockerSystem.parcelService "2. Request parcel deposit"
            campusLockerSystem.parcelService -> campusLockerSystem.lockerService "3. Find available locker"
            campusLockerSystem.lockerService -> campusLockerSystem.lockerManager "4. Apply locker business rules"
            campusLockerSystem.parcelService -> campusLockerSystem.pinService "5. Request secure PIN"
            campusLockerSystem.pinService -> campusLockerSystem.securityManager "6. Generate secure PIN"
            campusLockerSystem.parcelService -> campusLockerSystem.parcelRepository "7. Create parcel record"
            campusLockerSystem.parcelRepository -> campusLockerSystem.databaseAdapter "8. Persist data"
            campusLockerSystem.databaseAdapter -> campusLockerSystem.mainDatabase "9. Store in database"
            campusLockerSystem.parcelService -> campusLockerSystem.auditService "10. Log deposit event"
            campusLockerSystem.auditService -> campusLockerSystem.auditDatabase "11. Record audit trail"
            campusLockerSystem.parcelService -> campusLockerSystem.notificationService "12. Send confirmation"
            campusLockerSystem.notificationService -> campusLockerSystem.emailAdapter "13. Send email"
            campusLockerSystem.emailAdapter -> emailService "14. Deliver notification"
            autolayout tb
            title "Dynamic Diagram - Parcel Deposit Workflow"
        }
        
        dynamic campusLockerSystem "Dynamic-ParcelPickup" "Parcel pickup workflow demonstrating security and audit features" {
            webUser -> campusLockerSystem.webInterface "1. Enters PIN for pickup"
            campusLockerSystem.webInterface -> campusLockerSystem.parcelService "2. Request parcel pickup"
            campusLockerSystem.parcelService -> campusLockerSystem.pinService "3. Validate PIN"
            campusLockerSystem.pinService -> campusLockerSystem.securityManager "4. Validate PIN against hash"
            campusLockerSystem.parcelService -> campusLockerSystem.parcelManager "5. Verify parcel status"
            campusLockerSystem.parcelService -> campusLockerSystem.parcelRepository "6. Update parcel status"
            campusLockerSystem.parcelRepository -> campusLockerSystem.databaseAdapter "7. Persist changes"
            campusLockerSystem.databaseAdapter -> campusLockerSystem.mainDatabase "8. Update database"
            campusLockerSystem.parcelService -> campusLockerSystem.lockerService "9. Release locker"
            campusLockerSystem.lockerService -> campusLockerSystem.lockerManager "10. Apply release business rules"
            campusLockerSystem.parcelService -> campusLockerSystem.auditService "11. Log pickup event"
            campusLockerSystem.auditService -> campusLockerSystem.auditDatabase "12. Record audit trail"
            campusLockerSystem.parcelService -> campusLockerSystem.notificationService "13. Send pickup confirmation"
            campusLockerSystem.notificationService -> campusLockerSystem.emailAdapter "14. Send email"
            campusLockerSystem.emailAdapter -> emailService "15. Deliver notification"
            autolayout tb
            title "Dynamic Diagram - Parcel Pickup Workflow"
        }

        # Deployment Diagram (Infrastructure View)
        deployment * "Production" "Deployment-Production" {
            include *
            autolayout tb
            title "Deployment Diagram - Production Environment"
            description "Production deployment showing infrastructure, security zones, and operational considerations with university network topology"
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