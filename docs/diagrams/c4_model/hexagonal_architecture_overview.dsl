workspace "Campus Locker System - Hexagonal Architecture Overview" "Top-level view of hexagonal architecture showing infrastructure adapters and business core boundaries" {

    !identifiers hierarchical

    model {
        # External Actors (Outside the Hexagon)
        webUsers = person "Web Users" "Students and staff using the locker system" "User"
        adminUsers = person "System Administrators" "IT staff managing the system" "Admin"
        emailSystem = softwareSystem "Email System" "External SMTP service (MailHog/Production SMTP)" "External"
        
        # Campus Locker System (The Hexagon)
        campusLockerSystem = softwareSystem "Campus Locker System" "Hexagonal architecture implementation for parcel management" {
            
            # === INFRASTRUCTURE LAYER (Outer Ring of Hexagon) ===
            
            # Primary Adapters (Driving/Input Adapters)
            nginxGateway = container "Nginx Gateway" "HTTP reverse proxy and load balancer - Primary entry adapter" "Nginx, Docker" "PrimaryAdapter" {
                loadBalancer = component "Load Balancer" "Distributes traffic across application instances" "Nginx Upstream"
                sslTerminator = component "SSL Terminator" "Handles HTTPS encryption/decryption" "Nginx SSL Module"
                staticHandler = component "Static File Handler" "Serves CSS, JS, images efficiently" "Nginx Static Module"
                securityGateway = component "Security Gateway" "Security headers, rate limiting, CSRF protection" "Nginx Security"
                healthProxy = component "Health Check Proxy" "Routes health check requests" "Nginx Location"
            }
            
            webAdapter = container "Web Interface Adapter" "HTTP request/response translation for web users" "Flask, Gunicorn, Docker" "PrimaryAdapter"
            
            apiAdapter = container "API Interface Adapter" "REST API adapter for external integrations" "Flask REST, Docker" "PrimaryAdapter"
            
            adminAdapter = container "Admin Interface Adapter" "Administrative interface adapter" "Flask Admin, Docker" "PrimaryAdapter"
            
            # Secondary Adapters (Driven/Output Adapters)
            redisAdapter = container "Redis Cache Adapter" "Session storage and caching infrastructure adapter" "Redis 7, Docker" "SecondaryAdapter" {
                sessionStore = component "Session Store" "Distributed session storage across instances" "Redis Sessions"
                cacheLayer = component "Cache Layer" "Application data caching for performance" "Redis Cache"
                performanceOptimizer = component "Performance Optimizer" "Query result caching and optimization" "Redis Memory"
            }
            
            databaseAdapter = container "Database Persistence Adapter" "Data persistence infrastructure adapter" "SQLite, SQLAlchemy" "SecondaryAdapter"
            
            emailAdapter = container "Email Notification Adapter" "Email delivery infrastructure adapter" "SMTP, Python" "SecondaryAdapter"
            
            auditAdapter = container "Audit Logging Adapter" "Compliance and audit trail infrastructure adapter" "File System, Logging" "SecondaryAdapter"
            
            backupAdapter = container "Backup Infrastructure Adapter" "Data backup and recovery infrastructure" "Shell Scripts, Docker Volumes" "SecondaryAdapter"
            
            # === APPLICATION LAYER (Service Orchestration) ===
            
            applicationServices = container "Application Services Layer" "Orchestrates business operations and coordinates between adapters" "Python Flask Services" "ApplicationLayer" {
                parcelOrchestrator = component "Parcel Orchestrator" "Coordinates parcel lifecycle workflows" "Python Service"
                lockerOrchestrator = component "Locker Orchestrator" "Manages locker allocation and status" "Python Service"
                authOrchestrator = component "Authentication Orchestrator" "Handles login, sessions, and authorization" "Python Service"
                notificationOrchestrator = component "Notification Orchestrator" "Manages email notifications and reminders" "Python Service"
                auditOrchestrator = component "Audit Orchestrator" "Coordinates audit logging and compliance" "Python Service"
                pinOrchestrator = component "PIN Orchestrator" "Manages secure PIN generation and validation" "Python Service"
            }
            
            # === BUSINESS CORE LAYER (Domain Logic - Heart of Hexagon) ===
            
            businessCore = container "Business Domain Core" "Pure business logic - the heart of the hexagonal architecture" "Python Domain Objects" "DomainCore" {
                parcelDomain = component "Parcel Domain" "Core parcel business rules and entities" "Python Domain"
                lockerDomain = component "Locker Domain" "Core locker management logic" "Python Domain"
                securityDomain = component "Security Domain" "PIN generation, validation, and security policies" "Python Domain"
                notificationDomain = component "Notification Domain" "Email notification business rules" "Python Domain"
                auditDomain = component "Audit Domain" "Audit trail and compliance business logic" "Python Domain"
            }
            
            # === DATA LAYER (Infrastructure Boundary) ===
            
            mainDatabase = container "Operational Database" "Primary transactional data storage with WAL mode" "SQLite with WAL" "Database"
            auditDatabase = container "Audit Database" "Tamper-proof audit trail storage" "SQLite" "Database"
        }
        
        # === HEXAGONAL BOUNDARIES - PRIMARY ADAPTERS (Input/Driving) ===
        
        # External users drive the system through primary adapters
        webUsers -> campusLockerSystem.nginxGateway "HTTP/HTTPS requests for parcel operations" "HTTPS"
        adminUsers -> campusLockerSystem.nginxGateway "Admin interface access" "HTTPS"
        
        # Nginx routes to appropriate adapters
        campusLockerSystem.nginxGateway -> campusLockerSystem.webAdapter "Routes web requests" "HTTP Proxy"
        campusLockerSystem.nginxGateway -> campusLockerSystem.apiAdapter "Routes API requests" "HTTP Proxy"
        campusLockerSystem.nginxGateway -> campusLockerSystem.adminAdapter "Routes admin requests" "HTTP Proxy"
        
        # Primary adapters coordinate with application services
        campusLockerSystem.webAdapter -> campusLockerSystem.applicationServices "Translates HTTP to business operations"
        campusLockerSystem.apiAdapter -> campusLockerSystem.applicationServices "Translates REST API to business operations"
        campusLockerSystem.adminAdapter -> campusLockerSystem.applicationServices "Translates admin UI to business operations"
        
        # === HEXAGONAL BOUNDARIES - SECONDARY ADAPTERS (Output/Driven) ===
        
        # Application services drive secondary adapters for infrastructure needs
        campusLockerSystem.applicationServices -> campusLockerSystem.redisAdapter "Session and cache operations"
        campusLockerSystem.applicationServices -> campusLockerSystem.databaseAdapter "Data persistence operations"
        campusLockerSystem.applicationServices -> campusLockerSystem.emailAdapter "Email notification operations"
        campusLockerSystem.applicationServices -> campusLockerSystem.auditAdapter "Audit logging operations"
        campusLockerSystem.applicationServices -> campusLockerSystem.backupAdapter "Backup and recovery operations"
        
        # Application services contain and coordinate business logic
        campusLockerSystem.applicationServices -> campusLockerSystem.businessCore "Executes pure business logic"
        
        # Secondary adapters connect to external infrastructure
        campusLockerSystem.databaseAdapter -> campusLockerSystem.mainDatabase "CRUD operations with ACID compliance"
        campusLockerSystem.databaseAdapter -> campusLockerSystem.auditDatabase "Audit trail persistence"
        campusLockerSystem.emailAdapter -> emailSystem "SMTP email delivery"
        
        # === COMPONENT-LEVEL HEXAGONAL FLOWS ===
        
        # Nginx Gateway Internal Flow
        campusLockerSystem.nginxGateway.loadBalancer -> campusLockerSystem.nginxGateway.sslTerminator "Secure connection handling"
        campusLockerSystem.nginxGateway.sslTerminator -> campusLockerSystem.nginxGateway.securityGateway "Security policy enforcement"
        campusLockerSystem.nginxGateway.securityGateway -> campusLockerSystem.nginxGateway.staticHandler "Static asset optimization"
        campusLockerSystem.nginxGateway.healthProxy -> campusLockerSystem.applicationServices "Health monitoring"
        
        # Redis Adapter Internal Flow
        campusLockerSystem.redisAdapter.sessionStore -> campusLockerSystem.redisAdapter.performanceOptimizer "Session optimization"
        campusLockerSystem.redisAdapter.cacheLayer -> campusLockerSystem.redisAdapter.performanceOptimizer "Cache management"
        
        # Application Services to Business Core Flow
        campusLockerSystem.applicationServices.parcelOrchestrator -> campusLockerSystem.businessCore.parcelDomain "Parcel business operations"
        campusLockerSystem.applicationServices.lockerOrchestrator -> campusLockerSystem.businessCore.lockerDomain "Locker business operations"
        campusLockerSystem.applicationServices.authOrchestrator -> campusLockerSystem.businessCore.securityDomain "Authentication business logic"
        campusLockerSystem.applicationServices.notificationOrchestrator -> campusLockerSystem.businessCore.notificationDomain "Notification business rules"
        campusLockerSystem.applicationServices.auditOrchestrator -> campusLockerSystem.businessCore.auditDomain "Audit business policies"
        campusLockerSystem.applicationServices.pinOrchestrator -> campusLockerSystem.businessCore.securityDomain "PIN security logic"
        
        # Deployment Environment
        production = deploymentEnvironment "Production Hexagonal Deployment" {
            deploymentNode "University Infrastructure" {
                deploymentNode "DMZ Network Zone" {
                    deploymentNode "Load Balancer Cluster" {
                        technology "Nginx, Docker Swarm"
                        instances 2
                        containerInstance campusLockerSystem.nginxGateway
                    }
                }
                deploymentNode "Application Network Zone" {
                    deploymentNode "Application Cluster" {
                        technology "Docker, Python 3.12, Gunicorn"
                        instances 3
                        containerInstance campusLockerSystem.webAdapter
                        containerInstance campusLockerSystem.apiAdapter
                        containerInstance campusLockerSystem.adminAdapter
                        containerInstance campusLockerSystem.applicationServices
                        containerInstance campusLockerSystem.businessCore
                    }
                    deploymentNode "Cache Cluster" {
                        technology "Redis 7, Docker"
                        instances 2
                        containerInstance campusLockerSystem.redisAdapter
                    }
                }
                deploymentNode "Data Network Zone" {
                    deploymentNode "Database Server" {
                        technology "Linux, SQLite WAL Mode"
                        instances 1
                        containerInstance campusLockerSystem.mainDatabase
                        containerInstance campusLockerSystem.auditDatabase
                        containerInstance campusLockerSystem.databaseAdapter
                        containerInstance campusLockerSystem.backupAdapter
                    }
                }
            }
        }
    }

    views {
        # C4 Level 0: System Landscape - Hexagonal Architecture Context
        systemLandscape "C0_SystemLandscape_HexagonalEcosystem" {
            include *
            autolayout lr
            title "C0: System Landscape - Campus Locker System in Hexagonal Architecture Ecosystem"
            description "Highest level view showing the Campus Locker System within the broader university ecosystem, emphasizing hexagonal architecture boundaries"
        }
        
        # C4 Level 1: System Context - Hexagonal Boundaries  
        systemContext campusLockerSystem "C1_SystemContext_CampusLockerSystem" {
            include *
            autolayout tb
            title "C1: System Context - Campus Locker System Hexagonal Boundaries"
            description "System context showing external actors and systems interacting with the hexagonal campus locker system through defined ports"
        }
        
        # C4 Level 2: Container - Hexagonal Architecture Structure
        container campusLockerSystem "C2_Container_HexagonalArchitecture" {
            include *
            autolayout tb
            title "C2: Container View - Hexagonal Architecture with Infrastructure Adapters"
            description "Container-level view showing infrastructure adapters (Nginx, Redis) surrounding the business core with clear hexagonal port boundaries"
        }

        # C4 Level 2: Simplified Hexagonal Pattern View
        container campusLockerSystem "C2_Container_HexagonalPattern_Simplified" {
            include campusLockerSystem.businessCore
            include campusLockerSystem.applicationServices
            include campusLockerSystem.nginxGateway
            include campusLockerSystem.redisAdapter
            include campusLockerSystem.databaseAdapter
            include campusLockerSystem.emailAdapter
            include campusLockerSystem.webAdapter
            include campusLockerSystem.apiAdapter
            include campusLockerSystem.adminAdapter
            include webUsers
            include adminUsers
            include emailSystem
            include campusLockerSystem.mainDatabase
            include campusLockerSystem.auditDatabase
            autolayout tb
            title "C2: Hexagonal Architecture Pattern - Campus Locker System"
            description "Classic hexagonal architecture view showing the business core protected by ports, with nginx and Redis as infrastructure adapters connecting to external systems"
        }
        
        # C4 Level 3: Component Views - Infrastructure Adapters
        component campusLockerSystem.nginxGateway "C3_Component_NginxPrimaryAdapter" {
            include *
            autolayout lr
            title "C3: Component View - Nginx Gateway (Primary HTTP Adapter)"
            description "Detailed internal structure of Nginx serving as the primary HTTP infrastructure adapter in hexagonal architecture"
        }
        
        component campusLockerSystem.redisAdapter "C3_Component_RedisSecondaryAdapter" {
            include *
            autolayout lr
            title "C3: Component View - Redis Cache (Secondary Infrastructure Adapter)"
            description "Detailed internal structure of Redis serving as the caching and session infrastructure adapter in hexagonal architecture"
        }
        
        component campusLockerSystem.applicationServices "C3_Component_ApplicationServicesOrchestration" {
            include *
            autolayout tb
            title "C3: Component View - Application Services (Orchestration Layer)"
            description "Service orchestration layer that coordinates between infrastructure adapters and the pure business domain core"
        }
        
        component campusLockerSystem.businessCore "C3_Component_BusinessDomainCore" {
            include *
            autolayout tb
            title "C3: Component View - Business Domain Core (Pure Logic)"
            description "Heart of the hexagon containing pure business logic with zero infrastructure dependencies - the protected domain core"
        }
        
        # C4 Deployment View - Production Hexagonal Infrastructure
        deployment campusLockerSystem "production" "C4_Deployment_ProductionHexagonalInfrastructure" {
            include *
            autolayout tb
            title "C4: Deployment View - Production Hexagonal Architecture Infrastructure"
            description "Production deployment showing how hexagonal architecture components are distributed across network security zones"
        }
        
        # Dynamic View - Hexagonal Request Flow
        dynamic campusLockerSystem "Dynamic_ParcelDepositFlow_ThroughHexagonalLayers" "Parcel Deposit Request Flow Through Hexagonal Architecture" {
            webUsers -> campusLockerSystem.nginxGateway "1. HTTPS parcel deposit request"
            campusLockerSystem.nginxGateway -> campusLockerSystem.webAdapter "2. Route through primary adapter"
            campusLockerSystem.webAdapter -> campusLockerSystem.applicationServices "3. Translate to business operation"
            campusLockerSystem.applicationServices -> campusLockerSystem.businessCore "4. Execute pure business logic"
            campusLockerSystem.applicationServices -> campusLockerSystem.databaseAdapter "5. Persist via secondary adapter"
            campusLockerSystem.applicationServices -> campusLockerSystem.redisAdapter "6. Cache via secondary adapter"
            campusLockerSystem.applicationServices -> campusLockerSystem.emailAdapter "7. Notify via secondary adapter"
            campusLockerSystem.emailAdapter -> emailSystem "8. External SMTP delivery"
            title "Dynamic View - Parcel Deposit Flow Through Hexagonal Architecture Layers"
            description "Step-by-step flow showing how a parcel deposit request traverses the hexagonal architecture from external users through adapters to business core"
        }

        # Styling for Hexagonal Architecture Visualization
        styles {
            # Hexagonal Architecture Layers
            element "PrimaryAdapter" {
                background #2E8B57
                color #ffffff
                shape Component
            }
            element "SecondaryAdapter" {
                background #4682B4
                color #ffffff  
                shape Component
            }
            element "ApplicationLayer" {
                background #DAA520
                color #ffffff
                shape Component
            }
            element "DomainCore" {
                background #DC143C
                color #ffffff
                shape Component
            }
            element "Database" {
                background #696969
                color #ffffff
                shape Cylinder
            }
            element "External" {
                background #708090
                color #ffffff
                shape Component
            }
            element "User" {
                background #228B22
                color #ffffff
                shape Person
            }
            element "Admin" {
                background #B22222
                color #ffffff
                shape Person
            }
            
            # Relationship Styling
            relationship "Relationship" {
                routing Direct
                thickness 2
            }
        }
    }

    # Configuration for Hexagonal Architecture Visualization  
    configuration {
        scope softwaresystem
    }
} 