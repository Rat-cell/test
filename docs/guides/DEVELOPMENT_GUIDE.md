# 🚀 Campus Locker System - Development Guide

**For initial setup and to get the system running quickly, please see the [🚀 Quick Start Guide](QUICK_START.md).**

This comprehensive guide covers everything else you need to know for development, deployment, and collaboration for the **Campus Locker System v2.1.1**.

---

## 🐳 Docker Deployment

### Architecture Overview
The system uses a multi-container Docker setup:

- **App Container**: Flask application (Python)
- **Nginx Container**: Reverse proxy and static file serving
- **MailHog Container**: Email testing and development
- **Redis Container**: Caching and session storage

### Container Configuration

#### Application Container
- **Port**: Internal 80, External 5001
- **Environment**: Production-ready Flask setup
- **Volumes**: Persistent databases and logs
- **Health Checks**: Automated monitoring

#### Nginx Reverse Proxy
- **Port**: 80 (main entry point)
- **Purpose**: Load balancing, SSL termination, static files
- **Configuration**: Optimized for Flask applications

### Environment Variables
Key configuration options in `docker-compose.yml`:

```yaml
# Flask Configuration
FLASK_ENV=production
SECRET_KEY=your-super-secret-key

# Database Configuration
DATABASE_URL=sqlite:////app/databases/campus_locker.db
AUDIT_DATABASE_URL=sqlite:////app/databases/campus_locker_audit.db

# Email Configuration
MAIL_SERVER=mailhog
MAIL_PORT=1025
MAIL_DEFAULT_SENDER=noreply@campuslocker.local

# Application Settings
PARCEL_MAX_PICKUP_DAYS=7
PIN_EXPIRY_HOURS=24
```

---

## 🛠️ Development Workflow

### Available Make Commands
```bash
# Get help with available commands
make help

# Build and deployment
make build       # Build Docker images
make up          # Start all services
make down        # Stop all services

# Monitoring
make logs        # View application logs

# Testing
make test        # Run full test suite
make quick-test  # Quick deployment test

# Maintenance
make clean       # Clean up Docker resources
```

### Development Best Practices

#### Code Organization
- Follow **Hexagonal Architecture** principles
- Keep business logic in `app/business/`
- Use adapters for external dependencies
- Write tests for all new features

#### Testing Strategy
- **Unit Tests**: Test individual components
- **Integration Tests**: Test component interactions
- **End-to-End Tests**: Test complete workflows
- **Maintain 90%+ test coverage**

#### Git Workflow
```bash
# Create feature branch
git checkout -b feature/your-feature-name

# Make changes and test
make test

# Commit with descriptive messages
git commit -m "feat: add email PIN generation workflow"

# Push and create pull request
git push origin feature/your-feature-name
```

---

## 🧪 Testing

### Running Tests
```bash
# All tests using Make
make test

# Direct pytest commands
pytest tests/
pytest tests/unit/
pytest tests/integration/
pytest tests/flow/

# With coverage
pytest --cov=app tests/

# Specific test file
pytest tests/test_pin_service.py -v

# Run tests in Docker container
docker-compose exec app pytest
```

### Test Database
- Tests use in-memory SQLite
- Automatic setup/teardown
- Isolated test data

### Email Testing
- MailHog captures all emails
- Access at http://localhost:8025
- No real emails sent during testing

---

## 🔧 Configuration

### Application Settings
Key settings in `app/config.py`:

```python
# PIN Configuration
PIN_EXPIRY_HOURS = 24
PIN_GENERATION_TOKEN_EXPIRY_HOURS = 24

# Parcel Lifecycle
PARCEL_MAX_PICKUP_DAYS = 7
PARCEL_MAX_PIN_REISSUE_DAYS = 7

# Email Settings
MAIL_DEFAULT_SENDER = 'noreply@campuslocker.local'
```

### Database Configuration
- **Main DB**: User data, parcels, lockers
- **Audit DB**: Comprehensive audit logging
- **Automatic migrations**: Schema updates handled automatically

---

## 📊 Monitoring & Logging

### Health Checks
- **Endpoint**: `/health`
- **Automated**: Docker health checks every 30s
- **Response**: JSON with service status

### Logging
- **Location**: `logs/campus_locker.log`
- **Rotation**: Automatic log rotation
- **Levels**: DEBUG, INFO, WARNING, ERROR, CRITICAL

### Audit Logging
- **All user actions** logged
- **Admin activities** tracked
- **Security events** monitored
- **Retention policies** enforced

---

## 🚨 Troubleshooting

### Common Issues

#### Services Won't Start
```bash
# Check Docker status
docker-compose ps

# View service logs
make logs

# Restart services
make down && make up
```

#### Database Issues
```bash
# Access app container
docker-compose exec app bash

# Access database
sqlite3 databases/campus_locker.db

# Reset database (development only)
make clean
make up
```

#### Email Not Working
- Check MailHog at http://localhost:8025
- Verify MAIL_SERVER environment variable
- Check application logs for email errors

#### Port Conflicts
- Default ports: 80 (nginx), 5001 (app), 8025 (mailhog)
- Modify `docker-compose.yml` if conflicts occur
- Restart after port changes

### Getting Help
1. Check this guide first
2. Review application logs: `make logs`
3. Check test results: `make test`
4. Review Docker status: `docker-compose ps`

---

## 🔄 Deployment Updates

### Updating the Application
```bash
# Pull latest changes
git pull origin main

# Rebuild and restart
make down
make build
make up

# Verify deployment
make test
```

### Database Migrations
- Automatic schema updates
- Backup before major updates
- Test migrations in development first

### Rolling Back
```bash
# Stop current deployment
make down

# Checkout previous version
git checkout <previous-commit>

# Redeploy
make build
make up
```

---

## 📚 Additional Resources

### Architecture Documentation
- `[Database Documentation](../specifications/DATABASE_DOCUMENTATION.md)` - Complete database architecture & operations guide
- `[Project Structure Guide](../introduction/ABOUT_PROJECT_STRUCTURE.md)` - Detailed project structure

### API Documentation
- Health endpoint: `GET /health`
- Admin endpoints: `POST /admin/*`
- User endpoints: `GET|POST /deposit`, `GET|POST /pickup`

### Development Tools
- **pytest**: Testing framework
- **Flask**: Web framework
- **SQLAlchemy**: Database ORM
- **Docker**: Containerization
- **nginx**: Reverse proxy

---

*This guide covers the essential aspects of developing and deploying the Campus Locker System. For specific technical details, refer to the individual documentation files in the project.*