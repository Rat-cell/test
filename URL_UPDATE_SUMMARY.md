# URL Configuration Updates Summary

This document summarizes all the URL and server name updates made to ensure consistent use of `localhost:5000` for Flask's internal URL generation while maintaining proper nginx proxy routing.

## 🎯 Objective
- Flask should generate URLs using `localhost:5000` (SERVER_NAME)
- Users should access the application via `http://localhost` (nginx proxy)
- Email links should work correctly with the nginx proxy setup
- All documentation should be consistent

## 📝 Files Updated

### 1. Configuration Files
- **`campus_locker_system/app/config.py`**: Updated default SERVER_NAME from `localhost` to `localhost:5000`
- **`app/config.py`**: Confirmed already set to `localhost:5000`

### 2. Documentation Files
- **`README.md`**: 
  - Updated health check example from `localhost:5001` to `localhost` 
  - Updated legacy setup URLs from `127.0.0.1:5000` to `localhost:5000`
  - Added debugging note for direct app access
- **`QUICK_START.md`**: Updated local development URL from `127.0.0.1:5000` to `localhost:5000`
- **`COLLABORATION_GUIDE.md`**: 
  - Updated local development URL from `127.0.0.1:5000` to `localhost:5000`
  - Updated troubleshooting section to clarify nginx proxy usage

### 3. Test Scripts
- **`debug_email_templates.py`**: Updated sample PIN generation URL from `localhost:5000` to `localhost`
- **`test_email_templates.py`**: Updated test PIN generation URL from `localhost:5000` to `localhost`

### 4. New Files Created
- **`test_url_configuration.py`**: New comprehensive test script to verify URL configuration

## 🔧 Configuration Logic

### Flask Internal Configuration
```python
SERVER_NAME = 'localhost:5000'  # Required for url_for(_external=True)
PREFERRED_URL_SCHEME = 'http'
APPLICATION_ROOT = '/'
```

### Nginx Proxy Mapping
```
External (User Access)     →   Internal (Flask)
http://localhost           →   http://localhost:5000
http://localhost/health    →   http://localhost:5000/health
http://localhost/deposit   →   http://localhost:5000/deposit
```

### Email Link Generation
When Flask generates email links:
1. `url_for('main.generate_pin_by_token_route', token='abc123', _external=True)`
2. Flask generates: `http://localhost:5000/generate-pin/abc123`
3. Nginx proxy routes this correctly when users click the link

## 🚫 Files NOT Changed (Correctly Configured)

### Docker Health Checks (Internal)
These should remain `localhost:5000` since they run inside containers:
- `docker-compose.yml`: Health check uses `localhost:5000/health`
- `Dockerfile`: Health check uses `localhost:5000/health`
- `campus_locker_system/Dockerfile`: Health check uses `localhost:5000/health`

### Test Infrastructure
These are correctly configured:
- `test_email_pin_generation.py`: Uses `BASE_URL = "http://localhost"`
- `scripts/test-deployment.sh`: Uses `BASE_URL = "http://localhost"`

## ✅ Expected Results

### User Experience
- Users access: `http://localhost`
- Health check: `http://localhost/health`
- Admin login: `http://localhost/admin/login`
- MailHog: `http://localhost:8025`

### Email Links
- Email contains: `http://localhost/generate-pin/token-abc123`
- User clicks link → nginx routes to Flask correctly
- PIN generation works seamlessly

### Development vs Production
- **Local development**: `python run.py` → access via `http://localhost:5000`
- **Docker production**: `make up` → access via `http://localhost` (nginx proxy)

## 🧪 Testing

Run the new test script to verify configuration:
```bash
python test_url_configuration.py
```

Test email link generation:
```bash
python test_email_templates.py
python debug_email_templates.py
```

Test deployment:
```bash
make test
```

## 🔍 Verification Steps

1. **Start Docker deployment**: `make up`
2. **Check health**: `curl http://localhost/health`
3. **Test email links**: Deposit a parcel and check MailHog for correct URLs
4. **Verify proxy**: Ensure nginx routes all requests correctly

The system should now have consistent URL configuration across all components! 