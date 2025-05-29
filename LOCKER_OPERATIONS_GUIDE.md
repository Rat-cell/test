# 🛡️ Locker Operations Guide

**Complete guide for safe configuration and operational management of the Campus Locker System**

The Campus Locker System is built with **safety-first principles** to prevent accidental data loss while providing flexible configuration options. This guide covers both initial configuration and ongoing operational safety.

---

## 📋 **Quick Reference**

### ✅ **SAFE Operations**
- `python seed_lockers.py --verify-only` - Check system state (ZERO RISK)
- `python seed_lockers.py --initial-seed` - First-time setup only (ZERO RISK)
- `python seed_lockers.py --add-new --file new-lockers.json` - Add new lockers safely (LOW RISK, auto-backup)

### ⚠️ **DANGEROUS Operations**
- `python seed_lockers.py --admin-reset-confirm` - **DESTROYS ALL DATA** (HIGH RISK)

### 📁 **Configuration Storage**
All configurations are stored in the persistent `databases/` directory to ensure they survive deployments and container restarts.

---

## 🔒 **Safety Features**

### **Multi-Mode Safety System**
- **🔍 Verify-Only**: Check database state without any changes
- **➕ Add-Only**: Add new lockers while protecting existing ones  
- **🌱 Initial-Seed**: Only works on completely empty databases
- **💥 Admin-Reset**: Destructive operations require multiple confirmations

### **Automatic Protection**
- **Timestamped Backups**: Created before ANY data-changing operation
- **Conflict Detection**: Automatically detects and blocks ID conflicts
- **Multiple Confirmations**: Destructive operations require exact text confirmation
- **Clear Error Messages**: Detailed explanations when operations are blocked

---

## 📁 **Configuration Methods (Priority Order)**

### **1. Environment Variables (Highest Priority)**
Quick setup using environment variables:

```bash
# Simple configuration format
export LOCKER_SIMPLE_CONFIG="count:15,size_small:5,size_medium:5,size_large:5,location_prefix:HWR Locker {unit}"
```

**Format Parameters:**
- `count:N` - Total number of lockers
- `size_small:N` - Number of small lockers
- `size_medium:N` - Number of medium lockers  
- `size_large:N` - Number of large lockers
- `location_prefix:PATTERN` - Location pattern with placeholders

**Available Placeholders:**
- `{locker_id}` - Sequential locker ID
- `{floor}` - Calculated floor number
- `{unit}` - Unit number within floor
- `{size}` - Locker size

### **2. JSON Configuration File (Medium Priority)**
Detailed configuration using JSON files:

```bash
# Specify custom config file location (must be in persistent storage)
export LOCKER_CONFIG_FILE="/app/databases/your-custom-lockers.json"
```

**Default Location:** `databases/lockers-hwr.json` (persistent storage)

### **3. Default Configuration (Fallback)**
Automatic generation using application defaults if no other configuration is provided.

---

## 🛠️ **Safe Configuration Workflows**

### **🚀 Initial System Setup (First Time)**

**Step 1: Plan Your Configuration**
```bash
# Check if database is empty (safe for initial setup)
python seed_lockers.py --verify-only
```

**Step 2: Choose Configuration Method**
- **Option A**: Use environment variables for simple setups
- **Option B**: Create JSON file for complex configurations

**Step 3: Initialize System**
```bash
# Only works on empty databases - completely safe
python seed_lockers.py --initial-seed
```

**Step 4: Verify Setup**
```bash
# Confirm everything was created correctly
python seed_lockers.py --verify-only
```

### **➕ Adding New Lockers (Production Safe)**

**Step 1: Check Current State**
```bash
# Always start by understanding current state
python seed_lockers.py --verify-only
```

**Step 2: Create Add-Only JSON**
Create a new JSON file with **ONLY** the new lockers (different IDs):

```json
{
  "metadata": {
    "description": "Additional lockers for expansion",
    "version": "1.1"
  },
  "lockers": [
    {"id": 16, "location": "HWR Locker 16", "size": "small", "status": "free"},
    {"id": 17, "location": "HWR Locker 17", "size": "medium", "status": "free"},
    {"id": 18, "location": "HWR Locker 18", "size": "large", "status": "free"}
  ]
}
```

**Important**: Only use IDs that don't exist in the database!

**Step 3: Safety Test**
```bash
# This will show conflicts if any exist (doesn't make changes)
python seed_lockers.py --add-new --file databases/new-lockers.json --dry-run
```

**Step 4: Execute Addition**
```bash
# Automatic backup created before changes
python seed_lockers.py --add-new --file databases/new-lockers.json
```

**Step 5: Verify Results**
```bash
# Confirm new lockers were added correctly
python seed_lockers.py --verify-only
```

---

## 📐 **JSON Configuration Format**

### **Standard Structure**
```json
{
  "metadata": {
    "description": "Your deployment description",
    "version": "1.0",
    "location": "Your Location",
    "total_count": 15,
    "size_distribution": {
      "small": 5,
      "medium": 5,
      "large": 5
    }
  },
  "lockers": [
    {"id": 1, "location": "Building A, Floor 1, Unit 1", "size": "small", "status": "free"},
    {"id": 2, "location": "Building A, Floor 1, Unit 2", "size": "medium", "status": "free"}
  ]
}
```

### **Required Fields**
- `lockers` - Array of locker configurations
- `location` - Physical location description (string)
- `size` - Locker size: `"small"`, `"medium"`, `"large"`

### **Optional Fields**
- `id` - Locker identifier (auto-generated if not provided)
- `status` - Initial status: `"free"`, `"occupied"`, `"out_of_service"`
- `metadata` - Configuration information (for documentation)

### **Locker Sizes & Dimensions**
- **Small**: 30cm H × 40cm W × 45cm D
- **Medium**: 50cm H × 40cm W × 45cm D  
- **Large**: 80cm H × 40cm W × 45cm D

---

## 🚫 **What NOT To Do**

### **❌ NEVER include existing IDs in new JSON:**
```json
{
  "lockers": [
    {"id": 1, "location": "...", "size": "..."},  // ← Will be blocked!
    {"id": 2, "location": "...", "size": "..."},  // ← Will be blocked!
    {"id": 16, "location": "...", "size": "..."}  // ← Only this would be added
  ]
}
```

### **❌ NEVER use removed unsafe commands:**
```bash
# This old approach was removed for safety
python seed_lockers.py --force  # ← REMOVED: Too dangerous
```

### **❌ NEVER skip verification:**
```bash
# Always check current state first
python seed_lockers.py --verify-only
```

---

## 🔧 **Environment Configuration Options**

### **File Path Configuration**
```bash
# Custom config file location (must be in persistent databases directory)
export LOCKER_CONFIG_FILE="/app/databases/your-custom-lockers.json"

# Disable automatic locker seeding
export ENABLE_DEFAULT_LOCKER_SEEDING=false
```

### **Default Generation Settings**
```bash
# Fallback configuration when no file/env config is provided
export DEFAULT_LOCKER_COUNT=20
export DEFAULT_LOCATION_PATTERN="Building A, Floor {floor}, Row {row}"

# Size distribution percentages (must total 100)
export DEFAULT_SIZE_SMALL_PERCENT=40
export DEFAULT_SIZE_MEDIUM_PERCENT=40  
export DEFAULT_SIZE_LARGE_PERCENT=20
```

---

## 🛡️ **Troubleshooting Safety Blocks**

### **"SAFETY BLOCK: Found ID conflicts"**
**Problem**: Your JSON contains IDs that already exist in database  
**Solution**: 
1. Check current IDs: `python seed_lockers.py --verify-only`
2. Remove existing IDs from your JSON
3. Keep only truly new lockers with unused IDs
4. Or use `--admin-reset-confirm` if you want to replace everything

### **"Database already contains lockers"**
**Problem**: Trying to initial-seed on non-empty database  
**Solution**: Use `--add-new` instead of `--initial-seed`

### **"Operation cancelled. Safety first!"**
**Problem**: Admin reset confirmation was incorrect  
**Solution**: Type the exact confirmation phrases: `DELETE ALL LOCKERS` and `YES DELETE`

### **"Invalid config file"**
**Problem**: JSON syntax or validation errors  
**Solution**: 
1. Validate JSON syntax online or with `python -m json.tool yourfile.json`
2. Check required fields: `location` and `size`
3. Verify size values: only `small`, `medium`, `large` allowed

---

## 📊 **Backup Management**

### **Automatic Backups**
- **When**: Created before every data-changing operation
- **Naming**: `campus_locker_backup_YYYYMMDD_HHMMSS.db`
- **Location**: Same `databases/` directory (persistent storage)

### **Manual Backup**
```bash
# Create manual backup with timestamp
cp databases/campus_locker.db databases/manual_backup_$(date +%Y%m%d).db
```

### **Restore from Backup**
```bash
# Stop application first, then:
cp databases/campus_locker_backup_20241129_143022.db databases/campus_locker.db
# Restart application
```

---

## ⚠️ **DANGEROUS: Admin Reset (Use Only in Emergencies)**

### **Complete System Reset**
```bash
python seed_lockers.py --admin-reset-confirm
```

- **Risk Level**: 🔴 **HIGH RISK - DESTROYS ALL DATA**
- **Requires**: Two exact confirmation phrases
- **What it destroys**: All lockers, parcels, sensor data, usage history
- **Safety**: Creates backup before destruction
- **Use only for**: Complete system reset, disaster recovery

**Confirmation Process:**
1. Type: `DELETE ALL LOCKERS`
2. Type: `YES DELETE`

---

## 🎯 **Example Configurations**

### **Small Office (5 Lockers)**
```bash
# Environment variable approach
export LOCKER_SIMPLE_CONFIG="count:5,size_small:2,size_medium:2,size_large:1,location_prefix:Office Locker {unit}"
```

```json
{
  "metadata": {
    "description": "Small office deployment",
    "total_count": 5
  },
  "lockers": [
    {"id": 1, "location": "Reception Desk, Position 1", "size": "small"},
    {"id": 2, "location": "Reception Desk, Position 2", "size": "medium"},
    {"id": 3, "location": "Break Room, Wall Mount 1", "size": "large"},
    {"id": 4, "location": "Lobby, Corner Unit 1", "size": "small"},
    {"id": 5, "location": "Lobby, Corner Unit 2", "size": "medium"}
  ]
}
```

### **University Campus (15 Lockers)**
```bash
# Environment variable approach
export LOCKER_SIMPLE_CONFIG="count:15,size_small:5,size_medium:5,size_large:5,location_prefix:HWR Locker {unit}"
```

```json
{
  "metadata": {
    "description": "HWR Campus deployment",
    "location": "HWR University",
    "total_count": 15,
    "size_distribution": {"small": 5, "medium": 5, "large": 5}
  },
  "lockers": [
    {"id": 1, "location": "HWR Locker 1", "size": "small"},
    {"id": 2, "location": "HWR Locker 2", "size": "small"},
    {"id": 3, "location": "HWR Locker 3", "size": "medium"},
    {"id": 4, "location": "HWR Locker 4", "size": "medium"},
    {"id": 5, "location": "HWR Locker 5", "size": "large"}
  ]
}
```

### **Large Deployment (50 Lockers)**
```bash
# Environment variable approach for scale
export LOCKER_SIMPLE_CONFIG="count:50,size_small:20,size_medium:20,size_large:10,location_prefix:Campus Center Building {building} Floor {floor} Unit {unit}"
```

---

## 🔍 **Validation & Monitoring**

### **Regular Health Checks**
```bash
# Check current state (run weekly)
python seed_lockers.py --verify-only

# Get configuration summary
python -c "
from app.services.locker_configuration_service import LockerConfigurationService
summary = LockerConfigurationService.get_configuration_summary()
print(summary)
"

# Export current configuration for backup
python -c "
from app.services.locker_configuration_service import LockerConfigurationService
config = LockerConfigurationService.export_current_configuration()
import json
print(json.dumps(config, indent=2))
" > current_lockers_backup.json
```

### **Docker Environment Checks**
```bash
# Check configuration loading logs
docker compose logs app | grep -E "(📝|📁|🏗️|⚠️|❌)"

# Verify current locker count
docker compose exec app python -c "
from app.business.locker import Locker
print(f'Total lockers: {Locker.query.count()}')
"
```

---

## 🆘 **Emergency Recovery**

If you accidentally lose data:

### **Immediate Steps**
1. **Stop the application immediately**
   ```bash
   make down  # or docker compose down
   ```

2. **Check for automatic backups**
   ```bash
   ls -la databases/campus_locker_backup_*.db
   ```

3. **Restore latest backup**
   ```bash
   cp databases/campus_locker_backup_YYYYMMDD_HHMMSS.db databases/campus_locker.db
   ```

4. **Restart application**
   ```bash
   make up  # or docker compose up -d
   ```

5. **Verify data integrity**
   ```bash
   python seed_lockers.py --verify-only
   ```

---

## ✅ **Safety Checklist**

Before any database operation:

- [ ] I have checked current state with `--verify-only`
- [ ] I understand what operation I'm performing
- [ ] I have verified backup will be created (for data-changing operations)
- [ ] I am using the safest possible operation for my goal
- [ ] I have tested this in development (for production systems)
- [ ] I have documented this change for the team

---

## 📝 **Best Practices**

### **Configuration Management**
1. **Start Simple**: Use environment variables for initial setup
2. **Document Locations**: Use clear, descriptive location names
3. **Plan Distribution**: Consider your expected parcel size distribution
4. **Test Configuration**: Validate JSON files before deployment
5. **Backup Configuration**: Keep configuration files in version control

### **Operational Safety**
1. **Always verify first** with `--verify-only`
2. **Create add-only JSON files** for new lockers (never include existing IDs)
3. **Test in development** before applying to production
4. **Keep backups** - they're created automatically but verify they exist
5. **Never use admin-reset** unless you truly want to destroy all data
6. **Document changes** - keep track of when and why you added lockers

### **Monitoring**
1. **Regular Health Checks**: Weekly verification of system state
2. **Monitor Usage**: Use health endpoints to track locker utilization
3. **Log Review**: Check application logs for configuration warnings
4. **Backup Verification**: Ensure automatic backups are being created

---

**Remember: Data safety is more important than convenience!** 🛡️

*This configuration system follows the open-closed principle - you can extend and customize without modifying the application code.* 