# 📋 Campus Locker System - Changelog

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