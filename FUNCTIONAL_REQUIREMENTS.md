# 📋 Functional Requirements - Campus Locker System v2.1.4

## 📖 Overview

This document defines the functional requirements for the Campus Locker System. Each requirement is assigned a unique identifier (FR-XX) for traceability throughout the codebase.

**Latest Update**: FR-04 is now fully automated with background scheduling - no admin intervention required.

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

## 🎯 Requirements Traceability Matrix

| Requirement ID | Priority | Status | Test Coverage | Code Location |
|---------------|----------|--------|---------------|---------------|
| FR-01 | CRITICAL | ✅ | ✅ | `parcel_service.py` |
| FR-02 | CRITICAL | ✅ | ✅ | `pin.py`, `pin_service.py` |
| FR-03 | HIGH | ✅ | ✅ | `notification_service.py`, `notification.py` |
| FR-04 | MEDIUM | ✅ IMPLEMENTED & FULLY AUTOMATED | ✅ | `config.py`, `__init__.py` (scheduler), `parcel_service.py`, `notification_service.py`, `routes.py` |
| FR-06 | HIGH | ✅ VERIFIED | ✅ TESTED | `routes.py`, `parcel_service.py`, `missing_report_confirmation.html` |

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

**Last Updated**: May 30, 2025 - v2.1.4
**Document Owner**: Campus Locker System Team I 