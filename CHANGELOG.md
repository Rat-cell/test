# 📋 Campus Locker System - Changelog

## v2.1.2 (2025-01-XX) - Email Template Enhancement & System Standardization

### 🎨 Email Template Overhaul
- **Professional Email Design**: Completely redesigned all email templates with clean, professional formatting
- **Removed Clutter**: Eliminated excessive emojis and verbose text for better readability
- **Consistent Styling**: Standardized formatting across all email types with clear section headers
- **Dynamic Configuration**: All templates now use configurable PIN expiry and parcel lifecycle values

### 🔄 PIN Regeneration Enhancement
- **Universal Regeneration Links**: All PIN-related emails now include "🔄 NEED A NEW PIN?" section
- **Always Available**: Recipients can regenerate PINs from any PIN-related email, not just the initial notification
- **Improved User Experience**: Clear instructions and accessible regeneration throughout the PIN lifecycle

### 📅 Parcel Lifecycle Information
- **Pickup Deadline Clarity**: All emails now include "7 days from deposit" pickup deadline information
- **Dynamic Configuration**: Parcel pickup deadlines read from `PARCEL_MAX_PICKUP_DAYS` configuration
- **Security Notes**: Enhanced security information about timeframes and PIN validity

### 🌐 URL Configuration Standardization
- **Consistent URL Structure**: Standardized all URL references throughout the codebase to use `localhost` (port 80)
- **Flask Port Migration**: Migrated Flask application from port 5000 to port 80 internally for consistency
- **Nginx Upstream Fix**: Updated nginx configuration to properly proxy to Flask on port 80
- **Documentation Updates**: Updated all documentation files (README, QUICK_START, COLLABORATION_GUIDE) with correct URLs

### 🗄️ Database Management
- **Locker Availability**: Added additional test lockers to ensure sufficient availability for all sizes
- **Database Cleanup**: Freed occupied lockers and added new lockers for comprehensive testing
- **Proper Data Structure**: Ensured all lockers use correct field structure (status='free' instead of is_available)

### 🔧 Configuration Files Updated
- **Flask Configuration**: Updated `SERVER_NAME` from 'localhost:5000' to 'localhost' in all config files
- **Docker Compose**: Updated environment variables and port mappings for consistency
- **Nginx Configuration**: Fixed upstream server configuration and proxy headers
- **Dockerfile Updates**: Updated EXPOSE directives and gunicorn binding for port 80

### 📧 Email Template Improvements
**Before (cluttered):**
```
🎉 Great news! Your parcel has been deposited and is ready for pickup!
📍 Locker Details: • Locker ID: {locker_id} • Deposited: {deposited_time}
🔑 TO GET YOUR PICKUP PIN: Click the button below...
```

**After (clean):**
```
Hello!
Your parcel has been deposited and is ready for pickup.
PICKUP DETAILS: • Locker: #{locker_id} • Deposited: {deposited_time}
GENERATE YOUR PIN: To get your pickup PIN, click the link below: {pin_generation_url}
```

### 🧪 Testing & Verification
- **Email Template Testing**: Created comprehensive test script to verify all template improvements
- **URL Configuration Testing**: Verified all URL references work correctly across the system
- **Container Rebuild**: Successfully rebuilt and tested all Docker containers with changes
- **Health Check Verification**: Confirmed all services healthy after updates

### 🛠️ Technical Improvements
- **Service Integration**: Enhanced notification service to pass PIN regeneration URLs to all email types
- **PIN Service Updates**: Modified PIN service methods to generate and include regeneration URLs
- **Template Engine**: Improved email template creation with dynamic configuration values
- **Error Handling**: Maintained robust error handling throughout all template and URL changes

### 📚 Documentation Updates
- **README Updates**: Updated main README with correct URL references and access instructions
- **Quick Start Guide**: Corrected all localhost references for proper system access
- **Collaboration Guide**: Updated development URLs and testing procedures

### 🔒 Security Enhancements
- **PIN Regeneration Security**: Maintained secure token-based PIN regeneration with rate limiting
- **Email Security**: Preserved all security warnings and instructions in cleaned templates
- **Configuration Security**: Maintained secure configuration practices with environment variables

### 🎯 User Experience Improvements
- **Clear Communication**: Simplified email language while maintaining all essential information
- **Better Navigation**: Improved email structure with logical flow and clear action items
- **Consistent Experience**: Standardized user experience across all email touchpoints
- **Accessibility**: Enhanced readability and accessibility of all email communications

### 🐛 Bug Fixes
- **Port Conflicts**: Resolved Flask port configuration conflicts with nginx proxy
- **URL Inconsistencies**: Fixed hardcoded URL references throughout the codebase
- **Template Rendering**: Fixed email template rendering with proper configuration values
- **Container Health**: Resolved health check issues after port migration

---

## v2.1.0 (2025-05-27) - Email Security & Manual Testing Fixes

### 🔒 Security Improvements
- **PIN Security**: Removed PIN display from deposit confirmation page - depositors can no longer see the pickup PIN
- **Email-Only PIN Distribution**: PINs are now exclusively sent via email to recipients

### 📧 Email System Fixes
- **Fixed Email Configuration**: Corrected hardcoded MAIL_SERVER to read from environment variables
- **MailHog Integration**: Emails now properly route to MailHog container for testing
- **Environment Variable Support**: All email settings now configurable via environment variables

### 🗄️ Database Improvements
- **Automatic Database Seeding**: Database now auto-populates with initial lockers and admin user on first startup
- **Manual Testing Ready**: No manual database setup required for testing
- **18 Pre-configured Lockers**: 6 small, 6 medium, 6 large lockers ready for use

### 🔧 Configuration Enhancements
- **Environment-Based Config**: Email settings now read from Docker environment variables
- **Flexible Mail Server**: Supports both localhost (development) and mailhog (production) configurations
- **Updated Admin Credentials**: Default admin password strengthened to meet security requirements

### 📚 Documentation Updates
- **Updated Quick Start Guide**: Reflects correct admin credentials (admin/AdminPass123!)
- **Manual Testing Instructions**: Clear step-by-step testing procedures
- **Email Testing Guide**: Instructions for using MailHog interface

### 🐛 Bug Fixes
- **Root Route Method Support**: Fixed "Method Not Allowed" error on main page form submission
- **Admin Login Redirect**: Fixed admin login to redirect to locker management instead of deposit page
- **Database Persistence**: Improved database initialization and seeding process
- **Container Health Checks**: Enhanced service startup reliability

### 🧪 Testing Improvements
- **Manual Testing Workflow**: Documented complete testing procedures
- **Email Verification**: MailHog integration for email testing
- **Security Validation**: Confirmed PIN privacy and email-only distribution

---

## v2.0.0 (Previous Release)
- Initial hexagonal architecture implementation
- Docker deployment setup
- Basic locker management functionality
- Admin authentication system
- Email notification system (basic)
- Comprehensive test suite (91/91 tests passing)

---

## v1.x (Legacy)
- Previous monolithic implementation
- Local development setup
- Basic functionality without containerization 