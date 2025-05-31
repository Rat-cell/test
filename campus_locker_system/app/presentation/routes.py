from flask import render_template, request, redirect, url_for, flash, session, current_app, jsonify
from . import main_bp
from app.services.parcel_service import (
    assign_locker_and_create_parcel,
    process_pickup,
    mark_parcel_missing_by_admin,
    process_overdue_parcels,
    report_parcel_missing_by_recipient,
    process_reminder_notifications,
    get_parcel_by_id
)
from app.services.audit_service import AuditService
from app.services.locker_service import set_locker_status, mark_locker_as_emptied
from app.services.pin_service import (
    generate_pin_by_token,
    request_pin_regeneration_by_recipient_email_and_locker,
    get_pin_expiry_hours,
    regenerate_pin_token
)
from app.services.notification_service import NotificationService
from app.services.database_service import DatabaseService
from app.services.admin_auth_service import AdminAuthService
from .decorators import admin_required
from datetime import datetime
import datetime as dt

@main_bp.route('/health', methods=['GET'])
def health_check():
    """Enhanced health check endpoint with comprehensive database status"""
    try:
        # Perform comprehensive database health check
        is_healthy, health_data = DatabaseService.health_check()

        # Get database statistics
        stats = DatabaseService.get_database_statistics()

        response_data = {
            'status': 'healthy' if is_healthy else 'degraded',
            'service': 'campus-locker-system',
            'version': '2.1.1',
            'database': {
                'main_database': health_data.get('main_database', 'unknown'),
                'audit_database': health_data.get('audit_database', 'unknown'),
                'record_counts': health_data.get('record_counts', {}),
                'issues': health_data.get('issues', [])
            },
            'statistics': stats if not stats.get('error') else {'error': stats.get('error')}
        }

        status_code = 200 if is_healthy else 503
        return jsonify(response_data), status_code

    except Exception as e:
        current_app.logger.error(f"Health check error: {str(e)}")
        return jsonify({
            'status': 'unhealthy',
            'service': 'campus-locker-system',
            'error': str(e)
        }), 503

@main_bp.route('/', methods=['GET'])
def home():
    """Home page with navigation options for deposit and pickup"""
    return render_template('home.html')

@main_bp.route('/deposit', methods=['GET', 'POST'])
def deposit_parcel():
    if request.method == 'POST':
        parcel_size = request.form.get('parcel_size')
        recipient_email = request.form.get('recipient_email')

        if not parcel_size or not recipient_email:
            flash('Parcel size and recipient email are required.', 'error')
            return redirect(url_for('main.deposit_parcel'))

        confirm_recipient_email = request.form.get('confirm_recipient_email')
        if not confirm_recipient_email:
            flash('Please confirm the recipient email address.', 'error')
            return redirect(url_for('main.deposit_parcel'))

        if recipient_email != confirm_recipient_email:
            flash('Email addresses do not match. Please try again.', 'error')
            return redirect(url_for('main.deposit_parcel'))

        result = assign_locker_and_create_parcel(recipient_email, parcel_size)
        if result[0] is None:  # parcel is None means error
            flash(result[1], 'error')  # result[1] is the error message
            return redirect(url_for('main.deposit_parcel'))

        parcel = result[0]
        success_message = result[1]
        flash(success_message, 'success')

        pin_expiry_hours = get_pin_expiry_hours()

        return render_template('deposit_confirmation.html',
                               parcel=parcel,
                               message=success_message,
                               pin_expiry_hours=pin_expiry_hours)

    return render_template('deposit_form.html')

@main_bp.route('/generate-pin/<token>', methods=['GET'])
def generate_pin_by_token_route(token):
    """
    FR-05: Re-issue PIN - Token-based PIN generation for expired PIN recovery
    """
    try:
        parcel, message = generate_pin_by_token(token)
        pin_expiry_hours = get_pin_expiry_hours()

        if parcel:
            flash(message, 'success')
            return render_template('pin_generation_success.html',
                                 parcel=parcel,
                                 message=message,
                                 pin_expiry_hours=pin_expiry_hours)
        else:
            flash(message, 'error')
            return render_template('pin_generation_error.html',
                                 error_message=message)
    except Exception as e:
        current_app.logger.error(f"Error in PIN generation route: {str(e)}")
        flash('An unexpected error occurred. Please try again later.', 'error')
        return render_template('pin_generation_error.html',
                             error_message='An unexpected error occurred.')

@main_bp.route('/pickup', methods=['GET', 'POST'])
def pickup_parcel():
    if request.method == 'POST':
        pin = request.form.get('pin')

        if not pin:
            flash('PIN is required.', 'error')
            return redirect(url_for('main.pickup_parcel'))

        result = process_pickup(pin)
        if result[0] is None:  # parcel is None means error
            flash(result[1], 'error')
            return redirect(url_for('main.pickup_parcel'))

        parcel = result[0]
        success_message = result[1]
        return render_template('pickup_confirmation.html',
                               parcel=parcel,
                               message=success_message)

    return render_template('pickup_form.html')

@main_bp.route('/report-missing/<int:parcel_id>', methods=['POST'])
def report_missing_parcel_by_recipient(parcel_id):
    """Route for recipients to report their parcel as missing after pickup"""
    try:
        parcel = get_parcel_by_id(parcel_id)
        if not parcel:
            flash('Parcel not found.', 'error')
            return redirect(url_for('main.pickup_parcel'))

        recipient_email = parcel.recipient_email
        locker_id = parcel.locker_id

        result_parcel, error = report_parcel_missing_by_recipient(parcel_id)

        if error:
            flash(f'Error reporting parcel as missing: {error}', 'error')
            return redirect(url_for('main.pickup_parcel'))

        admin_notification_success, admin_notification_message = NotificationService.send_parcel_missing_admin_notification(
            parcel_id=parcel_id,
            locker_id=locker_id,
            recipient_email=recipient_email
        )

        if not admin_notification_success:
            current_app.logger.warning(f"Admin notification failed for missing parcel {parcel_id}: {admin_notification_message}")

        AuditService.log_event("PARCEL_REPORTED_MISSING_BY_RECIPIENT_UI", details={
            "parcel_id": parcel_id,
            "locker_id": locker_id,
            "recipient_email_domain": recipient_email.split('@')[1] if '@' in recipient_email else 'unknown',
            "reported_via": "Web_UI_after_pickup",
            "admin_notified": admin_notification_success
        })

        flash('Your parcel has been reported as missing. The administrators have been notified and will investigate.', 'success')

        now = datetime.now(dt.UTC)
        report_time = now.strftime('%Y-%m-%d %H:%M:%S')
        reference_date = now.strftime('%Y%m%d')

        return render_template('missing_report_confirmation.html',
                               parcel=parcel,
                               parcel_id=parcel_id,
                               report_time=report_time,
                               reference_date=reference_date,
                               current_time=report_time,
                               reference_number=f"MISSING-{parcel_id}-{reference_date}")

    except Exception as e:
        current_app.logger.error(f"Error in report missing parcel route for parcel {parcel_id}: {str(e)}")
        flash('An unexpected error occurred. Please try again later.', 'error')
        return redirect(url_for('main.pickup_parcel'))

@main_bp.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    is_valid, _ = AdminAuthService.validate_session()
    if is_valid:
        return redirect(url_for('main.manage_lockers'))

    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        admin_user, message = AdminAuthService.authenticate_admin(username, password)

        if admin_user:
            AdminAuthService.create_session(admin_user)
            flash('Admin login successful!', 'success')
            return redirect(url_for('main.manage_lockers'))
        else:
            flash(f'Login failed: {message}', 'error')
            return redirect(url_for('main.admin_login'))

    return render_template('admin/admin_login.html')

@main_bp.route('/admin/logout')
def admin_logout():
    AdminAuthService.logout()
    flash('You have been logged out.', 'info')
    return redirect(url_for('main.admin_login'))

@main_bp.route('/admin/audit-logs')
@admin_required
def audit_logs_view():
    # Remove audit logging for viewing audit logs (creates spam)
    # admin_session = AdminAuthService.get_current_session()
    # admin_id = admin_session.admin_id if admin_session else None
    # AuditService.log_event("ADMIN_VIEW_AUDIT_LOGS", {"admin_id": admin_id})
    
    page = request.args.get('page', 1, type=int)
    # FR-07: Audit Trail - Retrieve audit logs using service layer
    logs_pagination = AuditService.get_paginated_audit_logs(page=page, per_page=15)
    return render_template('admin/audit_logs.html', logs_pagination=logs_pagination)

@main_bp.route('/admin/lockers', methods=['GET'])
@admin_required
def manage_lockers():
    # Remove audit logging for viewing locker management (creates spam)
    # admin_session = AdminAuthService.get_current_session()
    # admin_id = admin_session.admin_id if admin_session else None
    # AuditService.log_event("ADMIN_VIEW_LOCKER_MANAGEMENT", {"admin_id": admin_id})

    from app.services.locker_service import get_all_lockers_with_parcel_counts
    lockers_with_parcels = get_all_lockers_with_parcel_counts()
    
    # NFR-05: Accessibility - Pass status choices for dropdowns
    from app.business.locker import LockerManager
    locker_statuses = LockerManager.VALID_STATUSES
    
    return render_template('admin/manage_lockers.html', lockers_with_parcels=lockers_with_parcels, locker_statuses=locker_statuses)

@main_bp.route('/admin/parcel/<int:parcel_id>/view', methods=['GET'])
@admin_required
def view_parcel_admin(parcel_id):
    parcel = get_parcel_by_id(parcel_id)
    if not parcel:
        flash('Parcel not found.', 'error')
        return redirect(url_for('main.manage_lockers'))
    
    # Remove audit logging for viewing parcel details (creates spam)
    # admin_session = AdminAuthService.get_current_session()
    # admin_id = admin_session.admin_id if admin_session else None
    # AuditService.log_event("ADMIN_VIEW_PARCEL_DETAILS", {
    #     "admin_id": admin_id,
    #     "parcel_id": parcel_id,
    #     "locker_id": parcel.locker_id
    # })
    
    return render_template('admin/view_parcel.html', parcel=parcel)

@main_bp.route('/admin/parcel/<int:parcel_id>/mark-missing', methods=['POST'])
@admin_required
def mark_parcel_missing_admin_action(parcel_id):
    admin_session = AdminAuthService.get_current_session()
    if not admin_session: # Should be caught by @admin_required but good practice
        flash('Admin session not found.', 'error')
        return redirect(url_for('main.admin_login'))

    # Use service layer to mark parcel missing
    # FR-06: Report Missing Item - Admin action to mark item missing
    # FR-07: Audit Trail - Ensures this action is logged via ParcelService
    success, message = mark_parcel_missing_by_admin(
        admin_id=admin_session.admin_id,
        admin_username=admin_session.username, # FR-07: Pass username for audit
        parcel_id=parcel_id
    )
    if success:
        flash(message, 'success')
    else:
        flash(message, 'error')
    return redirect(url_for('main.manage_lockers')) # Or redirect to parcel view if preferred

@main_bp.route('/request-new-pin', methods=['GET', 'POST'])
def request_new_pin_action():
    if request.method == 'POST':
        recipient_email = request.form.get('recipient_email')
        locker_id_str = request.form.get('locker_id') # Keep as string for initial validation

        if not recipient_email or not locker_id_str:
            flash('Email and Locker ID are required.', 'error')
            return redirect(url_for('main.request_new_pin_action'))
        
        # FR-05: Re-issue PIN - Use service layer for PIN regeneration request
        parcel, message = request_pin_regeneration_by_recipient_email_and_locker(recipient_email, locker_id_str)
        
        if parcel: # Success means parcel was found and link sent
            flash(message, 'success') # "PIN generation link has been regenerated..."
            return redirect(url_for('main.home')) 
        else: # Error or parcel not found
            flash(message, 'info') # "If your details matched an active parcel..." or specific error
            return redirect(url_for('main.request_new_pin_action'))

    return render_template('request_new_pin_form.html')

@main_bp.route('/admin/locker/<int:locker_id>/mark-emptied', methods=['POST'])
@admin_required
def admin_mark_locker_emptied_action(locker_id):
    """
    FR-08: Mark Locker as Emptied (Admin Action)
    Allows admin to mark a locker as emptied and available, typically after maintenance
    or resolving a disputed contents issue.
    """
    admin_session = AdminAuthService.get_current_session()
    admin_id = admin_session.admin_id if admin_session else None
    admin_username = admin_session.username if admin_session else "UnknownAdmin"

    # FR-08: Use service layer for marking locker as emptied
    # FR-07: Audit trail is handled within the service
    success, message = mark_locker_as_emptied(
        locker_id=locker_id,
        admin_id=admin_id,
        admin_username=admin_username
    )

    if success:
        flash(message, 'success')
    else:
        flash(message, 'error')
    
    return redirect(url_for('main.manage_lockers'))

@main_bp.route('/admin/parcels/process-overdue', methods=['POST'])
@admin_required
def admin_process_overdue_parcels_action():
    # 🔥 ENHANCED AUDIT LOGGING: Track admin bulk operations
    admin_session = AdminAuthService.get_current_session()
    admin_id = admin_session.admin_id if admin_session else None
    AuditService.log_event("ADMIN_TRIGGER_PROCESS_OVERDUE_PARCELS", {"admin_id": admin_id})

    # FR-07: Audit Trail - Further details logged within process_overdue_parcels service
    processed_count, error_count, message = process_overdue_parcels(admin_initiated=True, admin_id=admin_id)
    
    flash(f"{message} Processed: {processed_count}, Errors: {error_count}.", 'info')
    return redirect(url_for('main.manage_lockers'))

@main_bp.route('/admin/regenerate_pin_token/<int:parcel_id>', methods=['POST'])
@admin_required
def regenerate_pin_token_admin_action(parcel_id):
    """
    FR-05: Admin action to regenerate a PIN token for a specific parcel.
    """
    admin_session = AdminAuthService.get_current_session()
    admin_id = admin_session.admin_id if admin_session else None # For audit

    parcel = get_parcel_by_id(parcel_id) # Fetch parcel using service
    if not parcel:
        flash(f"Parcel ID {parcel_id} not found.", "error")
        return redirect(url_for('main.manage_lockers'))

    # FR-05: Re-issue PIN - Use PinService for token regeneration
    # FR-07: Audit trail handled by PinService
    success, message = regenerate_pin_token(parcel_id, parcel.recipient_email, admin_reset=True)
    
    if success:
        flash(f"Successfully regenerated PIN token for Parcel ID {parcel_id}. {message}", "success")
    else:
        flash(f"Failed to regenerate PIN token for Parcel ID {parcel_id}. Error: {message}", "error")
        
    return redirect(request.referrer or url_for('main.view_parcel_admin', parcel_id=parcel_id))

@main_bp.route('/admin/locker/<int:locker_id>/set-status', methods=['POST'])
@admin_required
def update_locker_status(locker_id):
    new_status = request.form.get('new_status')
    admin_session = AdminAuthService.get_current_session()
    admin_id = admin_session.admin_id if admin_session else None # For audit
    admin_username = admin_session.username if admin_session else "UnknownAdmin" # For audit

    # FR-08: Set Locker Status (Out of Service / Free)
    # FR-07: Audit trail handled by LockerService
    success, message = set_locker_status(
        admin_id=admin_id, 
        admin_username=admin_username,
        locker_id=locker_id, 
        new_status=new_status
    )

    if success:
        flash(message, 'success')
    else:
        flash(message, 'error')
    return redirect(url_for('main.manage_lockers'))

@main_bp.route('/system/process-reminders', methods=['POST', 'GET'])
def automatic_reminder_processing():
    """
    FR-04: Manually trigger or view status of automatic reminder processing
    This endpoint is primarily for the background scheduler but can be manually triggered.
    """
    admin_session = AdminAuthService.get_current_session()
    admin_id = admin_session.admin_id if admin_session else None
    trigger_source = "manual_admin_trigger" if admin_id else "manual_system_trigger"
    
    # Prevent unauthorized manual trigger if needed, or restrict to POST
    # For now, let's assume if an admin is logged in, it's an admin trigger.
    # If not, it's a system/test trigger.

    if request.method == 'POST' or (request.method == 'GET' and admin_id): # Allow GET only if admin
        current_app.logger.info(f"FR-04: Manual reminder processing triggered by: {trigger_source}")
        
        # FR-07: Audit Trail - Detailed logging handled by process_reminder_notifications
        processed_count, error_count = process_reminder_notifications(
            triggered_by_admin=bool(admin_id), 
            admin_id=admin_id
        )
        
        # Log to audit service
        AuditService.log_event("FR-04_MANUAL_REMINDER_PROCESSING", {
            "processed_count": processed_count,
            "error_count": error_count,
            "trigger_source": trigger_source,
            "admin_id": admin_id
        })
        
        flash(f"Reminder processing complete. Processed: {processed_count}, Errors: {error_count}.", 'info')
        
        if admin_id:
            return redirect(url_for('main.manage_lockers')) # Redirect admin to a relevant page
        else:
            return jsonify({"status": "success", "processed": processed_count, "errors": error_count}), 200
    
    elif request.method == 'GET' and not admin_id: # Non-admin GET request
        # FR-04: Provide information about the scheduler for GET requests (if desired)
        # This could be a status page or simple confirmation for testing
        # For now, let's just return a simple message if not triggered by admin
        return jsonify({"message": "Reminder processing is typically automatic. POST to trigger manually (admin only)."}), 200

    # If POST from non-admin, or other invalid access method:
    flash("Unauthorized to trigger reminder processing.", "error")
    return redirect(url_for('main.home'))

@main_bp.route('/system/logout-all-admins', methods=['POST', 'GET'])
@admin_required
def system_logout_all_admins():
    """
    System utility to logout all active admin sessions.
    This is a sensitive operation and should be protected.
    Requires SECRET_KEY to be passed as a query parameter for GET requests for safety.
    """
    admin_session = AdminAuthService.get_current_session()
    acting_admin_id = admin_session.admin_id if admin_session else "UnknownAdmin"

    if request.method == 'GET':
        # Safety check for GET requests
        provided_key = request.args.get('secret_key_confirm')
        if provided_key != current_app.config.get('SECRET_KEY'):
            AuditService.log_event("SYSTEM_LOGOUT_ALL_ADMINS_FAIL", {
                "reason": "Missing or invalid secret_key_confirm for GET request",
                "acting_admin_id": acting_admin_id
            })
            flash("Invalid or missing secret key for GET request. This action must be confirmed.", "error")
            return redirect(url_for('main.manage_lockers'))

    # If POST or GET with valid key
    try:
        # This functionality would require iterating through active sessions
        # Flask's default session mechanism (client-side cookies) doesn't easily support server-side invalidation of all sessions.
        # A more robust solution would involve server-side session storage (e.g., Redis, database)
        # For now, this is a placeholder for a more complex implementation or will only log out the current admin.
        
        # Placeholder: If using server-side sessions, this is where you'd clear them.
        # For client-side, we can't force logout all others without changing their cookie secret.
        # We can log the intent and log out the current admin if this is an admin action.
        
        count_logged_out = 0
        # Example: if using flask_session with a server-side store:
        # from flask_session import Session
        # session_interface = current_app.session_interface
        # if hasattr(session_interface, 'store'): # e.g. RedisStore
        #    all_sessions = session_interface.store.keys('session:*') # or similar
        #    for sess_key in all_sessions:
        #        session_interface.store.delete(sess_key)
        #        count_logged_out +=1
        
        # For now, just log the action and log out the current admin if they initiated
        AdminAuthService.logout() # Logs out the current admin
        count_logged_out = 1 # At least the current admin

        AuditService.log_event("SYSTEM_LOGOUT_ALL_ADMINS_ATTEMPT", {
            "acting_admin_id": acting_admin_id,
            "sessions_cleared_estimate": count_logged_out, # This is an estimate
            "notes": "Standard client-side sessions cannot be force-invalidated server-side easily. Current admin logged out."
        })
        flash(f"Attempted to log out all admin sessions. Your session has been logged out. ({count_logged_out} session(s) affected directly).", "info")
        return redirect(url_for('main.admin_login')) # Redirect to login after logout
        
    except Exception as e:
        current_app.logger.error(f"Error during system_logout_all_admins: {str(e)}")
        AuditService.log_event("SYSTEM_LOGOUT_ALL_ADMINS_ERROR", {
            "acting_admin_id": acting_admin_id,
            "error": str(e)
        })
        flash(f"An error occurred: {str(e)}", "error")
        return redirect(url_for('main.manage_lockers'))
