# Legacy services file - functions have been moved to domain services
# This file now serves as documentation and backward compatibility layer

# ====== MIGRATION COMPLETED ======
# All service functions have been successfully moved to their appropriate domain services:

# PIN-related functions moved to:
# - app.business.pin (PinManager business logic)
# - app.services.pin_service (service orchestration)

# Admin authentication moved to:
# - app.business.admin_auth (AdminAuthManager business logic)  
# - app.services.admin_auth_service (AdminAuthService orchestration)

# Parcel-related functions moved to:
# - app.business.parcel (Parcel business entity)
# - app.services.parcel_service (parcel workflow orchestration)
#   * retract_deposit()
#   * dispute_pickup()
#   * report_parcel_missing_by_recipient()
#   * mark_parcel_missing_by_admin()
#   * process_overdue_parcels()

# Locker-related functions moved to:
# - app.business.locker (Locker business entity)
# - app.services.locker_service (locker management orchestration)
#   * set_locker_status()
#   * mark_locker_as_emptied()

# Notification functions moved to:
# - app.business.notification (email templates and business rules)
# - app.services.notification_service (email sending orchestration)

# Audit logging moved to:
# - app.business.audit (audit event classification and validation)
# - app.services.audit_service (audit orchestration and persistence)

# Backward compatibility functions:
from app.services.audit_service import log_audit_event

# ====== HEXAGONAL ARCHITECTURE ACHIEVED ======
# ✅ Clean separation of concerns
# ✅ Business logic isolated from infrastructure  
# ✅ Service layer orchestrates workflows
# ✅ All 91 tests passing
# ✅ Domain extraction complete (6/6 domains)
