# Campus Locker System - Test Suite

This directory contains automated tests for the Campus Locker System, focusing on Non-Functional Requirements (NFRs) and core functionality.

## 🧪 Test Overview

### **NFR-04: Backup Functionality Tests**
- **File**: `test_nfr04_backup_functionality.py`
- **Purpose**: Tests automated backup creation, WAL checkpoint handling, and data preservation
- **Key Features**:
  - Backup creation on initialization
  - WAL mode compatibility 
  - Data integrity verification
  - Scheduled backup logic

### **NFR-02: Auto-Recovery Tests**
- **File**: `test_nfr02_auto_recovery.py`
- **Purpose**: Tests system reliability, health checks, and crash safety
- **Key Features**:
  - Isolated in-memory testing (no impact on real database)
  - Health check endpoint testing
  - SQLite WAL mode configuration
  - Transaction durability verification

### **JSON Configuration & Overwrite Protection**
- **File**: `test_json_overwrite_protection.py`
- **Purpose**: Tests client JSON configuration loading with safety protection
- **Key Features**:
  - First run: Successfully adds lockers from JSON
  - Second run: Demonstrates overwrite protection
  - Conflict detection and data safety
  - Client configuration workflow

## 🚀 Running Tests

### **Run All Tests**
```bash
python -m pytest tests/ -v
```

### **Run Specific Test Categories**
```bash
# Backup functionality
python -m pytest tests/test_nfr04_backup_functionality.py -v -s

# Auto-recovery features
python -m pytest tests/test_nfr02_auto_recovery.py -v -s

# JSON configuration
python -m pytest tests/test_json_overwrite_protection.py -v -s
```

### **Run Individual Tests**
```bash
# Test backup creation
python -m pytest tests/test_nfr04_backup_functionality.py::TestNFR04BackupFunctionality::test_nfr04_automated_backup_creation -v -s

# Test overwrite protection
python -m pytest tests/test_json_overwrite_protection.py::TestJSONOverwriteProtection::test_json_configuration_overwrite_protection -v -s
```

## 🛡️ Test Isolation

- **NFR-02 tests**: Use isolated in-memory databases (no impact on real data)
- **Backup tests**: Force WAL checkpoints to ensure complete data backup
- **JSON tests**: Use temporary directories and databases
- **Real database**: Protected from test interference

## 📊 Test Results

All tests demonstrate:
- ✅ **Backup functionality**: Creates backups with complete data
- ✅ **Overwrite protection**: Prevents duplicate/conflicting data
- ✅ **Database isolation**: Tests don't affect production data
- ✅ **WAL mode compatibility**: Handles SQLite Write-Ahead Logging properly
- ✅ **Client safety**: JSON configuration works safely

## 🔧 Configuration

Tests respect the following configurations:
- `SKIP_DATABASE_INITIALIZATION`: Disables real database init in tests
- Temporary directories for isolated testing
- WAL checkpoint handling for backup integrity

---

**Note**: The test suite focuses on data safety, backup reliability, and client configuration workflows. All tests are designed to be non-destructive to production data. 