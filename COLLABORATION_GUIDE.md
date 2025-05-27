# 🤝 Campus Locker System v2.0 - Collaboration Guide

Welcome to the **Campus Locker System v2.0**! This guide will help you get started with the project immediately after cloning.

## 🎯 What You Get When You Clone v2.00 Branch

### ✅ Complete Working System
- **91 comprehensive tests** (100% passing)
- **Hexagonal architecture** with 6 business domains
- **Production-ready Docker deployment**
- **All source code and configuration files**
- **Complete documentation and guides**

### 🚀 Instant Setup (5 Minutes)
```bash
# 1. Clone the repository
git clone <your-repository-url>
cd <repository-name>
git checkout v2.00

# 2. Start the system (one command!)
make up

# 3. Verify everything works
make test

# 4. Access the application
open http://localhost/
```

## 📁 What's Included for Collaboration

### 🔧 Docker Deployment Files
- `docker-compose.yml` - Production deployment
- `docker-compose.dev.yml` - Development environment
- `Dockerfile` & `Dockerfile.dev` - Container configurations
- `nginx.conf` - Reverse proxy configuration
- `Makefile` - Convenient commands

### 📚 Documentation
- `README.md` - Complete v2.0 documentation
- `QUICK_START.md` - 5-minute setup guide
- `DOCKER_DEPLOYMENT.md` - Detailed deployment guide
- `COLLABORATION_GUIDE.md` - This file!

### 🛠️ Setup Scripts
- `scripts/setup.sh` - Automated project initialization
- `scripts/test-deployment.sh` - Deployment verification
- `campus_locker_system/scripts/` - Additional utilities

### 💻 Complete Source Code
- **All application code** (no missing files!)
- **All test files** (91 tests ready to run)
- **All configuration files**
- **All documentation**

### 🚫 What's NOT Included (Intentionally)
- `venv/` - Virtual environment (you create your own)
- `__pycache__/` - Python cache (regenerated automatically)
- `*.db` files - Databases (created when you run the app)
- `*.log` files - Log files (created at runtime)
- `.env` - Environment variables (use `.env.template`)

## 🏃‍♂️ Quick Start for New Team Members

### Option 1: Docker (Recommended)
```bash
# Prerequisites: Docker Desktop installed
git clone <repo-url> && cd <repo-name>
git checkout v2.00
make up
# ✅ Done! App running at http://localhost/
```

### Option 2: Local Development
```bash
# Prerequisites: Python 3.12+, Docker for MailHog
git clone <repo-url> && cd <repo-name>
git checkout v2.00
python3 -m venv venv
source venv/bin/activate
pip install -r campus_locker_system/requirements.txt
cd campus_locker_system && python run.py
# ✅ Done! App running at http://127.0.0.1:5000/
```

### Option 3: Automated Setup
```bash
git clone <repo-url> && cd <repo-name>
git checkout v2.00
bash scripts/setup.sh
# ✅ Fully automated setup with verification!
```

## 🧪 Testing & Development

### Run All Tests
```bash
# Docker environment
make test

# Local environment
cd campus_locker_system && pytest
```

### Development Commands
```bash
make dev-up        # Start development environment
make dev-down      # Stop development environment
make logs          # View application logs
make clean         # Clean up Docker resources
```

## 🏗️ Architecture Overview

### Business Domains (6)
1. **Parcel Management** - Deposit, pickup, tracking
2. **Locker Operations** - Status, availability, sensors
3. **PIN Management** - Generation, validation, reissue
4. **Notifications/Email** - User communications
5. **Admin & Authentication** - User management, security
6. **Audit Logging** - Complete activity tracking

### Layer Structure
```
Presentation Layer (routes.py, api_routes.py)
    ↓
Service Layer (6 service classes)
    ↓
Business Layer (6 domain classes)
    ↓
Persistence Layer (models.py)
    ↓
Adapters Layer (database, email, audit)
    ↓
Database Layer (SQLite with audit separation)
```

## 🔧 Configuration & Customization

### Environment Variables
Copy `.env.template` to `.env` and customize:
```bash
cp .env.template .env
# Edit .env with your preferred settings
```

### Database Configuration
- **Main DB**: `campus_locker_system/databases/campus_locker.db`
- **Audit DB**: `campus_locker_system/databases/campus_locker_audit.db`
- Both created automatically on first run

### Email Testing
- **MailHog Web UI**: http://localhost:8025
- **SMTP**: localhost:1025 (configured automatically)

## 🚨 Troubleshooting

### Port Conflicts
If port 5000 is busy (common on macOS):
- System automatically uses port 5001
- Access via http://localhost:5001/

### Container Issues
```bash
docker ps                    # Check container status
make logs                   # View application logs
make down && make up        # Restart everything
```

### Test Failures
```bash
make test                   # Run deployment tests
cd campus_locker_system && pytest -v  # Run unit tests
```

## 📊 Project Status

### ✅ What's Working
- **91/91 tests passing** (100% success rate)
- **All business domains operational**
- **Docker deployment fully functional**
- **Complete documentation**
- **Security hardened**

### 🎯 Ready for Development
- **Clean codebase** with hexagonal architecture
- **Comprehensive test coverage**
- **Easy local development setup**
- **Production-ready deployment**

## 🤝 Contributing

### Development Workflow
1. **Clone and setup** (5 minutes with this guide)
2. **Create feature branch** from `v2.00`
3. **Develop with tests** (all 91 tests must pass)
4. **Test deployment** with `make test`
5. **Submit pull request** to `v2.00` branch

### Code Standards
- **Hexagonal architecture** - maintain layer separation
- **Test coverage** - all new features must have tests
- **Docker compatibility** - ensure changes work in containers
- **Documentation** - update relevant docs

## 🆘 Getting Help

1. **Check documentation**: README.md, QUICK_START.md, DOCKER_DEPLOYMENT.md
2. **Run diagnostics**: `make test` and `make logs`
3. **Verify setup**: All 91 tests should pass
4. **Check containers**: `docker ps` should show 4 healthy services

---

**🎉 Welcome to the team! You now have everything needed to start contributing to the Campus Locker System v2.0.**

**The system is production-ready, fully tested, and designed for collaborative development. Happy coding! 🚀** 