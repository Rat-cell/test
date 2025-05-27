# 🚀 Campus Locker System v2.1 - Quick Start Guide

**Get the Campus Locker System running in under 5 minutes!**

## Prerequisites
- **Docker Desktop** (macOS/Windows) or **Docker Engine** (Linux)
- **Git** for cloning the repository

## 🏃‍♂️ Quick Start (Recommended)

### 1. Clone the Repository
```bash
git clone <your-repository-url>
cd <repository-name>
git checkout v2.00  # Switch to the v2.0 branch
```

### 2. Start the System
```bash
make up
```

### 3. Verify Deployment
```bash
make test
```

### 4. Access the Application
- **🏠 Main Application**: http://localhost/
- **💊 Health Check**: http://localhost/health
- **📧 Email Testing (MailHog)**: http://localhost:8025
- **👤 Admin Login**: http://localhost/admin/login (admin/AdminPass123!)

## 📋 Available Commands

```bash
# Production Environment
make build          # Build Docker images
make up             # Start production deployment
make down           # Stop production deployment
make logs           # View production logs
make test           # Test deployment

# Development Environment
make dev-up         # Start development deployment
make dev-down       # Stop development deployment
make dev-logs       # View development logs

# Maintenance
make clean          # Clean up Docker resources
make help           # Show all available commands
```

## 🛠️ Alternative: Local Development Setup

If you prefer local development without Docker:

### 1. Setup Python Environment
```bash
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r campus_locker_system/requirements.txt
```

### 2. Start MailHog (for email testing)
```bash
docker run -d -p 1025:1025 -p 8025:8025 mailhog/mailhog
```

### 3. Create Admin User
```bash
cd campus_locker_system
python create_admin.py admin adminpass123
```

### 4. Run Application
```bash
python run.py
```

### 5. Access Application
- **Main App**: http://127.0.0.1:5000/
- **MailHog**: http://localhost:8025

## 🧪 Testing

### Run All Tests
```bash
# Docker environment (recommended)
make test

# Local environment
cd campus_locker_system
pytest
```

### Run Tests with Coverage
```bash
# Docker environment
docker-compose exec app pytest --cov=app

# Local environment
pytest --cov=app
```

## 📚 Documentation

- **Complete README**: See `README.md` for comprehensive documentation
- **Docker Deployment**: See `DOCKER_DEPLOYMENT.md` for detailed deployment guide
- **Architecture**: Hexagonal architecture with 6 business domains

## 🔧 Troubleshooting

### Port Conflicts
If port 5000 is in use (common on macOS):
- The system automatically uses port 5001 externally
- Access via http://localhost:5001/health

### Container Issues
```bash
# Check container status
docker ps

# View logs
make logs

# Restart containers
make down && make up
```

### Reset Everything
```bash
make down
make clean
make build
make up
```

## 🎯 What You Get

✅ **91 Comprehensive Tests** - All passing  
✅ **Hexagonal Architecture** - Clean, maintainable design  
✅ **Docker Deployment** - Production-ready containerization  
✅ **Security Hardened** - Non-root containers, security headers  
✅ **Email Testing** - MailHog integration  
✅ **Health Monitoring** - Built-in health checks  
✅ **Complete Documentation** - Guides and troubleshooting  

## 🆘 Need Help?

1. Check the troubleshooting section in `README.md`
2. Run `make logs` to view container logs
3. Run `make test` to verify deployment
4. Review `DOCKER_DEPLOYMENT.md` for detailed setup

---

**Campus Locker System v2.0** - Enterprise-ready parcel management system 🚀 