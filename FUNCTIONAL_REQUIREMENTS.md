# 📋 Functional Requirements - Campus Locker System v2.1.5

## 📖 Overview

This document defines the functional requirements for the Campus Locker System. Each requirement is assigned a unique identifier (FR-XX) for traceability throughout the codebase.

**Latest Update**: Version 2.1.5 completes core functional requirements with FR-07 (Audit Trail), FR-08 (Out of Service), and FR-09 (Invalid PIN Error Handling) fully implemented and verified.

---

## 🏆 Version 2.1.5 Achievement Summary

### **Enterprise-Level Functionality Completed**
Version 2.1.5 represents a significant milestone in the Campus Locker System development, completing three critical functional requirements that bring the system to enterprise production readiness:

#### **✅ FR-07: Audit Trail - Enterprise Compliance**
- **Complete audit infrastructure** with dual-database architecture
- **Comprehensive event logging** covering all system activities with timestamps
- **Administrative oversight** with audit log viewing and filtering capabilities
- **Compliance ready** for regulatory requirements and security audits
- **Performance optimized** for production environments with minimal impact

#### **✅ FR-08: Out of Service - Operational Excellence**
- **Smart maintenance workflows** enabling administrators to disable malfunctioning lockers
- **Intelligent assignment logic** that automatically skips out-of-service lockers
- **Professional admin interface** for locker status management and maintenance
- **Business rule validation** ensuring proper status transitions and data integrity
- **Real-world operational support** for maintenance scenarios and capacity planning

#### **✅ FR-09: Invalid PIN Error Handling - User Experience Excellence**
- **Professional error handling** with clear, user-friendly messages for all PIN scenarios
- **Recovery guidance** providing step-by-step help and direct access to PIN regeneration
- **Security conscious design** protecting sensitive information while being helpful
- **Visual feedback systems** with immediate error display and professional styling
- **Comprehensive coverage** of all PIN error scenarios with appropriate responses

### **Production Readiness Achievements**
- **📊 Complete Requirements Coverage**: All core functional requirements (FR-01 through FR-09) fully implemented
- **🧪 Comprehensive Testing**: Detailed test coverage with verification documents for all requirements
- **📋 Audit Compliance**: Enterprise-grade audit trail supporting regulatory compliance
- **⚙️ Operational Management**: Professional maintenance workflows for real-world deployment
- **🎨 User Experience**: Exceptional error handling and user guidance throughout the system
- **🏗️ Enterprise Architecture**: Production-ready dual-database design with performance optimization
- **🔒 Security Excellence**: Security-conscious design with comprehensive audit trails and data protection

### **Development Quality Standards**
- **Code Traceability**: All requirements marked with FR-XX comments throughout codebase
- **Test Coverage**: Comprehensive test suites for all implemented requirements
- **Documentation Excellence**: Complete verification documents and implementation guides
- **Version Control**: Systematic requirement tracking and change management
- **Team Collaboration**: Clear requirement ownership and implementation accountability

**Version 2.1.5 Status**: ✅ **ENTERPRISE-READY** - The Campus Locker System now provides comprehensive functionality suitable for production deployment with full administrative oversight, operational management, and exceptional user experience.

---

## 🎯 Core Functional Requirements

### FR-01: Assign Locker
**Description**: Assign the next free locker large enough for the parcel.

**Acceptance Criteria**:
- System identifies next available locker that fits parcel size requirements
- Locker assignment completes in ≤ 200 ms
- System handles case when no suitable locker is available
- Locker status is updated to "occupied" upon assignment
- Assignment process is atomic (all-or-nothing)

**Priority**: CRITICAL
**Status**: ✅ IMPLEMENTED
**Implementation**: `app/services/parcel_service.py::assign_locker_and_create_parcel`

---

### FR-02: Generate PIN
**Description**: Create a 6-digit PIN and store its salted SHA-256 hash.

**Acceptance Criteria**:
- System generates cryptographically secure 6-digit numeric PIN
- PIN is hashed using salted SHA-256 before storage
- Original PIN is never stored in plain text
- PIN generation supports email-based delivery system
- Each PIN generation invalidates previous PIN for same parcel
- Salt is unique per PIN for enhanced security

**Priority**: CRITICAL
**Status**: ✅ IMPLEMENTED
**Implementation**: `app/business/pin.py::PinManager`, `app/services/pin_service.py`

---

### FR-03: Email Notification System
**Description**: System shall send automated email notifications for key parcel lifecycle events.

**Acceptance Criteria**:
- Send parcel deposit confirmation with PIN generation link
- Send PIN generation notification with pickup instructions
- Send PIN reissue notifications when regenerated
- All emails include clear pickup instructions and security information
- Emails are professionally formatted and mobile-friendly
- System handles email delivery failures gracefully

**Priority**: HIGH
**Status**: ✅ IMPLEMENTED
**Implementation**: `app/services/notification_service.py`, `app/business/notification.py`

---

### FR-04: Send Reminder After 24h of Occupancy
**Description**: Send fully automatic bulk reminders after configurable hours of parcel occupancy without any admin intervention.

**Acceptance Criteria**:
- System automatically identifies parcels that have been deposited for configurable hours without pickup
- System sends automated bulk reminder emails to all eligible recipients 
- System runs completely automatically via background scheduler (no admin action required)
- System tracks reminder sent status to prevent duplicate reminders
- System includes pickup instructions and PIN regeneration options in reminder emails
- System logs all reminder activities for comprehensive audit trail
- System handles email delivery failures gracefully with error logging
- Timing is fully configurable via environment variables (open-closed principle)
- Background processing runs at configurable intervals (default: every hour)
- System operates independently without any manual triggers or admin intervention

**Priority**: MEDIUM
**Status**: ✅ IMPLEMENTED & FULLY AUTOMATED
**Implementation**:
- `app/config.py::REMINDER_HOURS_AFTER_DEPOSIT` - Configurable timing (default 24h)
- `app/config.py::REMINDER_PROCESSING_INTERVAL_HOURS` - Automatic check interval (default 1h)
- `app/business/parcel.py::reminder_sent_at` - Tracks reminder delivery status to prevent duplicates
- `app/business/notification.py::create_24h_reminder_email` - Professional email template creation
- `app/services/notification_service.py::send_24h_reminder_notification` - Email delivery service
- `app/services/parcel_service.py::process_reminder_notifications` - Main bulk processing logic
- `app/presentation/routes.py::automatic_reminder_processing` - System endpoint for automated processing
- `app/__init__.py::_start_automatic_reminder_scheduler` - Fully automatic background scheduler

**Automatic Operation**:
- **Background Scheduler**: Automatically starts with application initialization
- **Processing Interval**: Configurable (default: every 1 hour via `REMINDER_PROCESSING_INTERVAL_HOURS`)
- **No Admin Required**: System operates completely independently
- **Bulk Processing**: Processes all eligible parcels in single operation
- **Error Resilience**: Continues operation despite individual email failures
- **Audit Logging**: All activities automatically logged with detailed tracking

**Configuration**:
```bash
# When to send reminders (hours after deposit)
REMINDER_HOURS_AFTER_DEPOSIT=24  # Default: 24 hours

# How often to check for reminders (hours between checks)  
REMINDER_PROCESSING_INTERVAL_HOURS=1  # Default: every hour

# No admin configuration required - fully automatic operation
```

**Operational Flow**:
1. Background scheduler starts automatically with application
2. Every hour (configurable), system checks for eligible parcels
3. System identifies parcels deposited ≥ 24h ago (configurable) with no reminder sent
4. System sends bulk reminder emails to all eligible recipients
5. System marks parcels as reminded to prevent duplicates
6. System logs all activities for audit trail
7. Process repeats automatically without intervention

---

### FR-05: Re-issue PIN
**Description**: Allow users to generate a fresh PIN when their old one has expired or is no longer usable.

**Acceptance Criteria**:
- Users can request a new PIN when their current PIN has expired
- System validates user identity via email and locker ID before issuing new PIN
- System invalidates previous PIN when generating a new one (security requirement)
- System supports both traditional direct PIN delivery and email-based PIN generation systems
- System enforces rate limiting (maximum 3 PIN generations per day for security)
- System sends new PIN via email notification with pickup instructions
- System logs all PIN re-issue activities for audit trail
- System handles expired PIN generation tokens by allowing token regeneration
- Users can access PIN re-issue functionality via dedicated web form
- System provides clear instructions for when and how to use PIN re-issue functionality

**Business Rules**:
- Only parcels in "deposited" status are eligible for PIN re-issue
- User email must match the original recipient email for security
- Each new PIN invalidates all previous PINs for the same parcel
- PIN re-issue requests are rate-limited to prevent abuse
- System automatically resets daily generation count after 24 hours
- Both admin-initiated and user-initiated PIN re-issue are supported

**Priority**: HIGH
**Status**: ✅ IMPLEMENTED
**Implementation**:
- `app/services/pin_service.py::reissue_pin` - Admin-initiated PIN re-issue
- `app/services/pin_service.py::request_pin_regeneration_by_recipient` - User-initiated PIN regeneration  
- `app/services/pin_service.py::generate_pin_by_token` - Email-based PIN generation (handles expired PINs)
- `app/services/pin_service.py::regenerate_pin_token` - Token regeneration for expired links
- `app/services/pin_service.py::request_pin_regeneration_by_recipient_email_and_locker` - User form handler
- `app/presentation/routes.py::request_new_pin_action` - Web form interface for PIN re-issue
- `app/presentation/routes.py::generate_pin_by_token_route` - Token-based PIN generation
- `app/presentation/routes.py::regenerate_pin_token_admin_action` - Admin token regeneration
- `app/presentation/templates/request_new_pin_form.html` - User interface for PIN re-issue requests
- `app/presentation/templates/pin_generation_success.html` - Success page with regeneration options
- `app/business/notification.py::create_pin_reissue_email` - Email template for admin re-issue
- `app/business/notification.py::create_pin_regeneration_email` - Email template for user regeneration
- `app/services/notification_service.py::send_pin_reissue_notification` - Admin notification delivery
- `app/services/notification_service.py::send_pin_regeneration_notification` - User notification delivery

---

### FR-06: Report Missing Item
**Description**: Enable recipients to flag a locker as "package missing".

**Acceptance Criteria**:
- Recipients can report parcel as missing from pickup confirmation page
- System marks parcel status as "missing"
- System immediately notifies administrators via email
- System takes affected locker out of service for inspection
- System logs incident in audit trail with complete details
- System provides confirmation to recipient that report was submitted

**Priority**: HIGH
**Status**: ✅ IMPLEMENTED & TESTED
**Implementation**:
- `app/presentation/routes.py::report_missing_parcel_by_recipient`
- `app/services/parcel_service.py::report_parcel_missing_by_recipient`
- `app/services/notification_service.py::send_parcel_missing_admin_notification`
- `app/presentation/templates/missing_report_confirmation.html`

**Recent Updates**:
- **✅ Fixed (2024-05-30)**: Resolved JavaScript template error in missing report confirmation page
- **✅ Tested**: Template now uses server-side datetime formatting instead of client-side moment.js
- **✅ Verified**: All FR-06 functionality working correctly without JavaScript errors

---

### FR-07: Audit Trail
**Description**: Record every deposit, pickup and admin override with a timestamp for complete system accountability.

**Acceptance Criteria**:
- System automatically logs all parcel deposit events with timestamp and details
- System automatically logs all successful pickup events with timestamp and PIN verification details
- System automatically logs all failed pickup attempts with timestamp and reason (invalid PIN, expired PIN, etc.)
- System automatically logs all admin override actions with timestamp, admin identity, and action details
- System automatically logs all locker status changes with timestamp and triggering event
- System automatically logs all PIN generation, reissue, and regeneration events with timestamps
- System automatically logs all security events (failed logins, permission denials) with timestamps
- System automatically logs all notification deliveries with timestamp and delivery status
- All audit logs include sufficient detail for incident investigation and compliance reporting
- Audit logs are stored in separate database for data integrity and tamper resistance
- System provides admin interface for viewing and filtering audit logs
- System supports audit log retention policies and automated cleanup
- System categorizes audit events by type (user_action, admin_action, security_event, system_action, error_event)
- System assigns severity levels to audit events (low, medium, high, critical) for prioritization

**Priority**: CRITICAL (Compliance & Security)
**Status**: ✅ IMPLEMENTED & COMPREHENSIVE
**Implementation**:
- `app/services/audit_service.py::AuditService` - Main audit logging orchestration
- `app/business/audit.py::AuditManager` - Business logic for audit event creation and classification
- `app/business/audit.py::AuditEventClassifier` - Event categorization and severity assignment
- `app/adapters/audit_adapter.py` - Database adapter for audit log storage
- `app/persistence/models.py::AuditLog` - Separate audit database model
- `campus_locker_audit.db` - Dedicated audit trail database

**Audit Coverage**:
- **Deposit Events**: `PARCEL_CREATED_EMAIL_PIN`, `PARCEL_CREATED_TRADITIONAL_PIN` with parcel ID, locker ID, recipient details
- **Pickup Events**: `USER_PICKUP_SUCCESS`, `USER_PICKUP_FAIL_INVALID_PIN`, `USER_PICKUP_FAIL_PIN_EXPIRED` with PIN patterns and timing
- **Admin Actions**: `ADMIN_LOGIN_SUCCESS/FAIL`, `ADMIN_LOCKER_STATUS_CHANGED`, `ADMIN_MARKED_PARCEL_MISSING` with admin identity
- **PIN Management**: `PIN_GENERATED_VIA_EMAIL`, `PIN_REISSUED`, `PIN_REGENERATED` with generation counts and timing
- **Security Events**: `ADMIN_PERMISSION_DENIED`, `USER_PICKUP_FAIL_INVALID_PIN` with security context
- **System Actions**: `PARCEL_MARKED_RETURN_TO_SENDER`, `NOTIFICATION_SENT`, `FR-04_REMINDER_SENT` with automated processing details
- **Error Events**: All exceptions and failures with detailed error context and recovery actions

**Audit Features**:
- **Separate Database**: Audit logs stored in `campus_locker_audit.db` for tamper resistance
- **Automatic Classification**: Events automatically categorized by business logic (user_action, admin_action, security_event, system_action, error_event)
- **Severity Assignment**: Events assigned severity levels (low, medium, high, critical) for incident prioritization
- **Rich Context**: All logs include timestamps, user context, IP addresses, session IDs where available
- **Admin Interface**: Web interface for viewing, filtering, and searching audit logs
- **Retention Policies**: Configurable retention periods by event category with automated cleanup
- **Performance Optimized**: Asynchronous logging to prevent impact on user operations
- **Compliance Ready**: Comprehensive logging suitable for security audits and regulatory compliance

---

### FR-08: Out of Service
**Description**: Let an admin disable a malfunctioning locker so it is skipped during assignment.

**Acceptance Criteria**:
- Administrators can mark any locker as "out_of_service" to disable it
- System skips out_of_service lockers during automatic assignment process  
- System prevents new parcel deposits into out_of_service lockers
- Administrators can return out_of_service lockers to "free" status after maintenance
- System validates locker status transitions using business rules
- System maintains parcels already in out_of_service lockers (no automatic removal)
- System includes out_of_service lockers in utilization statistics for capacity planning
- System logs all locker status changes in audit trail with admin identity and timestamps
- Admin interface provides clear visual indication of out_of_service locker status
- System prevents setting locker to "free" if it contains disputed or deposited parcels

**Business Rules**:
- Only administrators can change locker status to/from out_of_service
- Locker assignment logic automatically excludes out_of_service lockers
- Out_of_service lockers remain out_of_service until manually restored by admin
- Existing parcels in out_of_service lockers can still be picked up normally
- Admin must resolve any active parcels before setting locker back to "free"
- Status transitions follow defined business logic: free ↔ out_of_service, occupied → out_of_service

**Priority**: HIGH
**Status**: ✅ IMPLEMENTED & VERIFIED
**Implementation**:
- `app/services/locker_service.py::set_locker_status` - Admin locker status management
- `app/business/locker.py::LockerManager.find_available_locker` - Filters out_of_service lockers
- `app/business/locker.py::LockerManager.can_transition_status` - Business rules for status transitions
- `app/services/parcel_service.py::process_pickup` - Maintains out_of_service status after pickup
- `app/presentation/routes.py::admin_set_locker_status_action` - Admin interface for status changes
- `app/presentation/templates/admin_locker_management.html` - Visual indication of out_of_service status

---

### FR-09: Invalid PIN Error Handling
**Description**: On wrong/expired PIN entry, display clear, helpful error messages to improve user experience and guide recovery actions.

**Acceptance Criteria**:
- System displays specific error messages for different PIN failure scenarios (invalid PIN, expired PIN, format errors)
- Error messages include helpful recovery guidance (request new PIN, check email, contact support)
- System provides immediate visual feedback when PIN entry fails
- Error messages are user-friendly and avoid technical jargon while maintaining security
- System suggests appropriate next actions based on the type of PIN error
- System maintains security by not revealing sensitive information (parcel details, locker contents)
- System includes rate limiting information when user reaches PIN generation limits
- Error handling is consistent across both traditional PIN and email-based PIN systems

**Error Scenarios Covered**:
- **Invalid PIN Format**: Non-numeric, wrong length, special characters
- **Expired PIN**: PIN past expiration time with regeneration guidance
- **Wrong PIN**: Incorrect PIN number with retry and recovery options
- **No Matching Parcel**: PIN doesn't match any active parcel
- **Rate Limited**: User has exceeded daily PIN generation limit
- **System Errors**: Database or service failures with appropriate fallback

**Priority**: MEDIUM
**Status**: ✅ IMPLEMENTED & ENHANCED
**Implementation**:
- `app/presentation/routes.py::pickup_parcel` - Enhanced error message handling for pickup failures
- `app/presentation/templates/pickup_error.html` - NEW: Dedicated error page with recovery guidance
- `app/services/parcel_service.py::process_pickup` - Enhanced error messaging for different failure types
- `app/business/pin.py::PinManager.is_valid_pin_format` - PIN format validation with helpful errors
- `app/presentation/templates/pickup_form.html` - Enhanced error display and recovery guidance

---

## 🎯 Requirements Traceability Matrix

| Requirement ID | Description | Priority | Status | Test Coverage | Implementation Location |
|---------------|-------------|-----------|--------|---------------|------------------------|
| FR-01 | Assign Locker | Critical | ✅ IMPLEMENTED & PERFORMANCE VERIFIED | `test_fr01_assign_locker.py` | `app/services/parcel_service.py` |
| FR-02 | Generate PIN | Critical | ✅ IMPLEMENTED & SECURITY VERIFIED | `test_fr02_generate_pin.py` | `app/business/pin.py` |
| FR-03 | Email Notification System | High | ✅ IMPLEMENTED & COMMUNICATION VERIFIED | `test_fr03_email_notification_system.py` | `app/services/notification_service.py` |
| FR-04 | Send Reminder After 24h | Medium | ✅ IMPLEMENTED & FULLY AUTOMATED | `test_fr04_automated_reminders.py` | `app/services/parcel_service.py` |
| FR-05 | Re-issue PIN | High | ✅ IMPLEMENTED & VERIFIED | `test_fr05_reissue_pin.py` | `app/services/pin_service.py` |
| FR-06 | Report Missing Item | High | ✅ IMPLEMENTED & TESTED | Manual testing completed | `app/services/parcel_service.py` |
| FR-07 | Audit Trail | Critical | ✅ IMPLEMENTED & COMPREHENSIVE | `test_fr07_audit_trail.py` | `app/services/audit_service.py` |
| FR-08 | Out of Service | High | ✅ IMPLEMENTED & VERIFIED | `test_fr08_out_of_service.py` | `app/services/locker_service.py` |
| FR-09 | Invalid PIN Error Handling | Medium | ✅ IMPLEMENTED & ENHANCED | `test_fr09_invalid_pin_errors.py` | `app/presentation/routes.py` |

---

## 📝 Notes

- All functional requirements are currently implemented and tested
- **FR-04 now fully automated (May 2025)**: Background scheduler eliminates need for admin intervention in reminder processing
- **FR-06 recently fixed (2024-05-30)**: JavaScript template error resolved, full functionality verified
- Requirements are traced through code comments with FR-XX identifiers
- Each requirement maps to specific implementation files for maintainability
- Test coverage exists for all critical and high-priority requirements

## 🔄 Change Management

When modifying functionality:
1. Update this requirements document
2. Update corresponding code comments with FR-XX references
3. Update test cases to reflect requirement changes
4. Update traceability matrix
5. Review impact on related requirements

When adding new functional requirements:
1. Assign next available FR-XX identifier
2. Define clear acceptance criteria
3. Add traceability comments to implementing code
4. Update this traceability matrix
5. Create corresponding test cases

**Last Updated**: May 30, 2025 - v2.1.5
**Document Owner**: Campus Locker System Team I 