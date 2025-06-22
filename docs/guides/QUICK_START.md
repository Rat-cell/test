#  Campus Locker System v2.1.3 - Quick Start Guide

**Get the production-ready Campus Locker System running in under 5 minutes!**

---

##  Prerequisites
- **Docker Desktop** (macOS/Windows) or **Docker Engine** (Linux)
- **Docker Compose** (included with Docker Desktop)
- **Git** for cloning the repository

---

##  Quick Start (Recommended)

### 1. Clone and Navigate
```bash
git clone <repository-url>
cd campus_locker_system
```

### 2. Deploy System
```bash
make up
```

### 3. Verify Health
```bash
make test
```

### 4. Access Application
- ** Main Application**: http://localhost
- ** Health Check**: http://localhost/health  
- ** Email Testing (MailHog)**: http://localhost:8025
- ** Admin Login**: http://localhost/admin/login (admin/AdminPass123!)

** That's it! You now have a production-ready locker system with 15 HWR lockers!**

---

##  What You Get Instantly

 **15 Pre-configured HWR Lockers** (5 small, 5 medium, 5 large)  
 **Safety-First Architecture** with automatic backups  
 **Dual Database System** (main + audit trail)  
 **91 Comprehensive Tests** - All passing  
 **Production Docker Stack** (Nginx + Gunicorn + Redis)  
 **Email Testing Ready** - MailHog integration  
 **Complete Documentation** - Operational guides included  

---

##  Essential Commands

```bash
# Production Deployment
make up             # Start production system
make down           # Stop production system
make test           # Run deployment validation
make logs           # View system logs
make clean          # Clean up resources

# System Management
make build          # Rebuild containers
make help           # Show all commands
```

---

##  Documentation Quick Access

- ** [Main System Overview](../../docs/introduction/ABOUT_PROJECT.md)** - Comprehensive system documentation, architecture, and project structure.
- ** [Database Documentation](../specifications/DATABASE_DOCUMENTATION.md)** - Database architecture details

---

##  Quick Troubleshooting

### Port Conflicts
```bash
# If port conflicts occur, check container status
docker ps -a
make logs
```

### System Reset
```bash
# Complete reset (WARNING: Removes all data)
make down
make clean
make up
```

### Health Check
```bash
# Verify system health
curl http://localhost/health
# Expected: {"status":"healthy","service":"campus-locker-system","version":"2.1.3"}
```

---

##  Production Ready Features

### **Safety & Security**
- ** Automatic Backups**: All operations create safety backups
- ** Conflict Detection**: Prevents accidental data overwriting
- ** Audit Trail**: Complete activity logging
- ** Secure Authentication**: Admin access with password protection

### **Deployment & Monitoring**
- ** Production Docker Stack**: Nginx reverse proxy, Gunicorn WSGI, Redis caching
- ** Health Monitoring**: Built-in health checks and service monitoring
- ** Persistent Storage**: Database files stored with bind mounts for backup/debugging
- ** Performance Optimized**: Multi-worker deployment with caching

### **Business Ready**
- ** Complete Parcel Management**: Deposit, PIN generation, pickup workflow
- ** Email Notifications**: Professional templates with PIN regeneration
- **‍ Admin Dashboard**: Full management interface with audit logs
- ** Hexagonal Architecture**: Clean, maintainable, scalable design

---

##  Need Help?

1. ** Check Logs**: `make logs` - View container logs
2. ** Run Tests**: `make test` - Verify deployment health  
3. ** [Main System Overview](../../docs/introduction/ABOUT_PROJECT.md)** - Comprehensive guide, architecture, and project structure.

---

##  Next Steps

After quick start deployment:

1. ** Review [Main System Overview](../../docs/introduction/ABOUT_PROJECT.md)** - Understand system capabilities and structure.
2. ** Configure Environment** - Customize settings via environment variables
3. ** Run Full Tests** - Validate all 91 tests pass
4. ** Check Admin Dashboard** - Explore management interface
5. ** Test Email Flow** - Verify email notifications via MailHog

---

**Campus Locker System v2.1.3** - Production-hardened parcel management with safety-first architecture  