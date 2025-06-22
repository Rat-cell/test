#  Database Documentation

##  **Overview**

The Campus Locker System uses a **dual-database architecture** for data separation and audit trail maintenance:

1. **Main Database** (`campus_locker.db`) - Core business data
2. **Audit Database** (`campus_locker_audit.db`) - Administrative audit trail

Both databases are **SQLite** and stored in the persistent `databases/` directory to survive deployments.

##  **Database Architecture**

### **Persistent Storage Location**
```
databases/
 campus_locker.db              # Main business database
 campus_locker_audit.db        # Audit trail database  
 lockers-hwr.json              # Locker configuration (15 HWR lockers)
 campus_locker_backup_*.db     # Automatic safety backups
```

##  **Main Database Schema (campus_locker.db)**

### **Entity Relationship Diagram (ERD)**

```
        
     LOCKER               PARCEL             ADMIN_USER    
        
 id (PK)          id (PK)              id (PK)         
 location            locker_id (FK)       username        
 size                pin_hash             password_hash   
 status              otp_expiry           last_login      
    recipient_email     
                       status          
    deposited_at    
 LOCKER_SENSOR       picked_up_at    
     _DATA           pin_generation_*
   
 id (PK)            
 locker_id (FK)  
 timestamp       
 has_contents    

```

### **Table Definitions**

#### **1. LOCKER Table**
```sql
CREATE TABLE locker (
    id INTEGER PRIMARY KEY,
    location VARCHAR(100) NOT NULL,     -- "HWR Locker 1", "HWR Locker 2", etc.
    size VARCHAR(50) NOT NULL,          -- "small", "medium", "large"
    status VARCHAR(50) NOT NULL         -- "free", "occupied", "out_of_service"
);
```

**Current Data**: 15 HWR lockers (5 small, 5 medium, 5 large)

#### **2. PARCEL Table**
```sql
CREATE TABLE parcel (
    id INTEGER PRIMARY KEY,
    locker_id INTEGER NOT NULL,                    -- FK to locker.id
    pin_hash VARCHAR(128),                         -- Hashed access PIN
    otp_expiry DATETIME,                          -- PIN expiration time
    recipient_email VARCHAR(120) NOT NULL,        -- Recipient contact
    status VARCHAR(50) NOT NULL,                  -- "deposited", "picked_up", "expired"
    deposited_at DATETIME NOT NULL,               -- When parcel was stored
    picked_up_at DATETIME,                        -- When parcel was retrieved
    pin_generation_token VARCHAR(128),            -- Token for PIN regeneration
    pin_generation_token_expiry DATETIME,         -- Token expiration
    pin_generation_count INTEGER NOT NULL,        -- Number of PIN regenerations
    last_pin_generation DATETIME,                 -- Last PIN regeneration timestamp
    FOREIGN KEY(locker_id) REFERENCES locker(id)
);
```

#### **3. ADMIN_USER Table**
```sql
CREATE TABLE admin_user (
    id INTEGER PRIMARY KEY,
    username VARCHAR(80) NOT NULL UNIQUE,    -- Admin username
    password_hash VARCHAR(128) NOT NULL,     -- Hashed password
    last_login DATETIME                      -- Last login timestamp
);
```

#### **4. LOCKER_SENSOR_DATA Table**
```sql
CREATE TABLE locker_sensor_data (
    id INTEGER PRIMARY KEY,
    locker_id INTEGER NOT NULL,               -- FK to locker.id
    timestamp DATETIME NOT NULL,              -- Sensor reading time
    has_contents BOOLEAN NOT NULL,            -- True if locker has contents
    FOREIGN KEY(locker_id) REFERENCES locker(id)
);
```

**Note on Data Access**: With the adoption of Hexagonal Architecture, direct interaction with these tables from application services or business logic is minimized. Instead, data access is primarily handled through a **Repository Pattern**. Repositories (located in `app/persistence/repositories/`) encapsulate the logic for querying and modifying data, using the SQLAlchemy models defined in `app/persistence/models.py`. This decouples the core application from the specifics of data storage.

### **Relationships**

1. **Locker ↔ Parcel** (1:Many)
   - One locker can contain multiple parcels over time
   - Each parcel belongs to exactly one locker

2. **Locker ↔ Sensor Data** (1:Many)
   - One locker generates multiple sensor readings
   - Each reading belongs to exactly one locker

3. **Admin User** (Independent)
   - No direct foreign key relationships
   - Links to audit trail via admin_id in audit database

##  **Audit Database Schema (campus_locker_audit.db)**

### **AUDIT_LOG Table**
```sql
CREATE TABLE audit_log (
    id INTEGER PRIMARY KEY,
    timestamp DATETIME NOT NULL,          -- When action occurred
    action VARCHAR(100) NOT NULL,         -- Action description
    details TEXT,                         -- Additional action details
    admin_id INTEGER,                     -- FK to main DB admin_user.id
    admin_username VARCHAR(80)            -- Admin username (denormalized)
);
```

### **Audit Trail Purpose**
- **Administrative Actions**: Login attempts, configuration changes
- **Security Events**: Failed authentication, suspicious activity
- **System Changes**: Database modifications, locker management
- **Cross-Database Link**: `admin_id` references `admin_user.id` in main database

##  **Data Flow & Relationships**

### **Core Business Flow**
```
1. LOCKER (configured from JSON) 
   ↓
2. PARCEL (deposited into locker)
   ↓  
3. SENSOR_DATA (monitors locker contents)
   ↓
4. PARCEL (picked up, status updated)
```

### **Administrative Flow**
```
1. ADMIN_USER (authenticates)
   ↓
2. AUDIT_LOG (action recorded)
   ↓
3. Business Operations (lockers, parcels)
   ↓
4. AUDIT_LOG (results recorded)
```

##  **Database Management**

### **Configuration-Driven Setup**
- **Locker creation**: From `databases/lockers-hwr.json`
- **Schema creation**: Automatic via Flask-SQLAlchemy, with models defined in `app/persistence/models.py`.
- **Data access**: Primarily through repositories in `app/persistence/repositories/`.
- **Data validation**: Business logic enforcement within services and business entities.
- **Safety**: Automatic backups before changes

### **Current Configuration (HWR)**
```json
{
  "metadata": {
    "total_count": 15,
    "size_distribution": {"small": 5, "medium": 5, "large": 5},
    "location": "HWR"
  },
  "lockers": [
    {"id": 1, "location": "HWR Locker 1", "size": "small", "status": "free"},
    // ... 14 more lockers
  ]
}
```

### **Safety Features**
- **Conflict Detection**: Prevents duplicate locker IDs
- **Backup Creation**: Automatic before data changes
- **Add-Only Mode**: Safely add new lockers without affecting existing
- **Audit Trail**: All administrative actions logged

##  **Database Queries**

This section provides examples of raw SQL queries for understanding data relationships and for direct database inspection. Within the application, similar data retrieval and manipulation logic is encapsulated within methods in the repository classes (`app/persistence/repositories/`).

### **Common Operations**

#### **Locker Status Overview**
```sql
SELECT size, status, COUNT(*) as count
FROM locker 
GROUP BY size, status 
ORDER BY size, status;
```

#### **Active Parcels**
```sql
SELECT l.location, p.recipient_email, p.deposited_at
FROM locker l
JOIN parcel p ON l.id = p.locker_id
WHERE p.status = 'deposited'
ORDER BY p.deposited_at DESC;
```

#### **Locker Utilization**
```sql
SELECT 
    l.size,
    COUNT(DISTINCT l.id) as total_lockers,
    COUNT(DISTINCT CASE WHEN p.status = 'deposited' THEN l.id END) as occupied_lockers,
    ROUND(COUNT(DISTINCT CASE WHEN p.status = 'deposited' THEN l.id END) * 100.0 / COUNT(DISTINCT l.id), 2) as utilization_percent
FROM locker l
LEFT JOIN parcel p ON l.id = p.locker_id
GROUP BY l.size;
```

#### **Recent Sensor Activity**
```sql
SELECT l.location, s.timestamp, s.has_contents
FROM locker l
JOIN locker_sensor_data s ON l.id = s.locker_id
WHERE s.timestamp > datetime('now', '-24 hours')
ORDER BY s.timestamp DESC;
```

#### **Admin Audit Trail**
```sql
SELECT a.timestamp, a.action, a.admin_username, a.details
FROM audit_log a
WHERE a.timestamp > datetime('now', '-7 days')
ORDER BY a.timestamp DESC
LIMIT 50;
```

##  **Performance Considerations**

### **Indexes (Automatic via SQLAlchemy)**
- Primary keys on all tables
- Foreign key indexes
- Unique constraint on admin_user.username

### **Optimization Recommendations**
- **Sensor Data**: Consider archiving old readings (>30 days)
- **Audit Log**: Regular cleanup of old audit entries
- **Parcel History**: Archive completed parcels after pickup

##  **Data Integrity**

### **Constraints**
- **Foreign Keys**: Enforce referential integrity
- **NOT NULL**: Prevent incomplete records
- **UNIQUE**: Ensure admin username uniqueness
- **Check Constraints**: Via business logic validation

### **Business Rules Enforced**
- Locker sizes: only "small", "medium", "large"
- Locker status: only "free", "occupied", "out_of_service"
- Parcel status: only "deposited", "picked_up", "expired"
- PIN expiry: Must be future timestamp
- Email format: Validated via application logic

##  **Deployment & Maintenance**

### **Database Files in Production**
```
/app/databases/              # Container persistent volume
 campus_locker.db         # Main database
 campus_locker_audit.db   # Audit database
 lockers-hwr.json         # Configuration
 backups/                 # Automatic backups
     campus_locker_backup_20241129_143022.db
     ...
```

### **Backup Strategy**
- **Automatic**: Before any data-changing operations
- **Manual**: `cp databases/campus_locker.db databases/manual_backup_$(date +%Y%m%d).db`
- **Docker Volume**: Persistent storage survives container restarts

### **Monitoring Queries**
```sql
-- Database health check
SELECT 'main' as db, COUNT(*) as locker_count FROM locker
UNION ALL
SELECT 'audit' as db, COUNT(*) as log_count FROM audit_log;

-- Configuration verification  
SELECT COUNT(*) as expected FROM locker WHERE 1=1; -- Should be 15

-- Data integrity check
SELECT 
    COUNT(*) as total_parcels,
    COUNT(CASE WHEN status = 'deposited' THEN 1 END) as active_parcels,
    COUNT(CASE WHEN locker_id NOT IN (SELECT id FROM locker) THEN 1 END) as orphaned_parcels
FROM parcel;
```

This dual-database architecture ensures **data integrity**, **audit compliance**, and **operational safety** while maintaining the simplicity needed for the HWR campus locker deployment. 