from flask import render_template, request, redirect, url_for, flash, session, current_app, jsonify # Add current_app
from . import main_bp # Assuming main_bp is defined in app/presentation/__init__.py
from app.services.parcel_service import (
    assign_locker_and_create_parcel, 
    process_pickup,
    mark_parcel_missing_by_admin,
    process_overdue_parcels,
    report_parcel_missing_by_recipient,
    process_reminder_notifications
    # Removed send_individual_reminder since we're going fully automatic
)
from app.services.audit_service import AuditService
from app.persistence.models import Locker, AuditLog, AdminUser, Parcel, LockerSensorData # Add LockerSensorData
from .decorators import admin_required # Add admin_required decorator
from app import db # Add db for session.get
from app.services.locker_service import set_locker_status, mark_locker_as_emptied
from app.services.pin_service import (
    reissue_pin, 
    request_pin_regeneration_by_recipient, 
    generate_pin_by_token,
    regenerate_pin_token,
    request_pin_regeneration_by_recipient_email_and_locker
)
from app.services.notification_service import NotificationService

@main_bp.route('/health', methods=['GET'])
def health_check():
    """Enhanced health check endpoint with comprehensive database status"""
    try:
        from app.services.database_service import DatabaseService
        
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
        
        # Return appropriate status code
        status_code = 200 if is_healthy else 503
        return jsonify(response_data), status_code
        
    except Exception as e:
        current_app.logger.error(f"Health check error: {str(e)}")
        return jsonify({
            'status': 'unhealthy',
            'service': 'campus-locker-system',
            'error': str(e)
        }), 503

@main_bp.route('/', methods=['GET', 'POST']) # Root route handles both GET and POST like deposit
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
        
        # Get PIN expiry hours from config for template
        from app.business.pin import PinManager
        pin_expiry_hours = PinManager.get_pin_expiry_hours()
        
        return render_template('deposit_confirmation.html', 
                               parcel=parcel, 
                               message=success_message,
                               pin_expiry_hours=pin_expiry_hours)

    return render_template('deposit_form.html')

@main_bp.route('/generate-pin/<token>', methods=['GET'])
def generate_pin_by_token_route(token):
    """Generate PIN using email token"""
    try:
        parcel, message = generate_pin_by_token(token)
        
        # Get PIN expiry hours from config
        from app.business.pin import PinManager
        pin_expiry_hours = PinManager.get_pin_expiry_hours()
        
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

        # Updated to handle new return format (parcel, message)
        result = process_pickup(pin)
        if result[0] is None:  # parcel is None means error
            flash(result[1], 'error')  # result[1] is the error message
            return redirect(url_for('main.pickup_parcel'))
        
        parcel = result[0]
        success_message = result[1]
        flash(success_message, 'success')
        return render_template('pickup_confirmation.html', 
                               parcel=parcel, 
                               message=success_message)

    return render_template('pickup_form.html')

@main_bp.route('/report-missing/<int:parcel_id>', methods=['POST'])
def report_missing_parcel_by_recipient(parcel_id):
    """Route for recipients to report their parcel as missing after pickup"""
    try:
        # Get parcel before reporting as missing to access recipient email
        parcel = db.session.get(Parcel, parcel_id)
        if not parcel:
            flash('Parcel not found.', 'error')
            return redirect(url_for('main.pickup_parcel'))
        
        # Store recipient email for admin notification
        recipient_email = parcel.recipient_email
        locker_id = parcel.locker_id
        
        # Use existing business logic to report parcel missing
        result_parcel, error = report_parcel_missing_by_recipient(parcel_id)
        
        if error:
            flash(f'Error reporting parcel as missing: {error}', 'error')
            return redirect(url_for('main.pickup_parcel'))
        
        # Send admin notification email
        admin_notification_success, admin_notification_message = NotificationService.send_parcel_missing_admin_notification(
            parcel_id=parcel_id,
            locker_id=locker_id,
            recipient_email=recipient_email
        )
        
        if not admin_notification_success:
            current_app.logger.warning(f"Admin notification failed for missing parcel {parcel_id}: {admin_notification_message}")
        
        # Enhanced audit logging for recipient-reported missing parcel
        admin_id = None  # No admin involved - this is recipient action
        AuditService.log_event("PARCEL_REPORTED_MISSING_BY_RECIPIENT_UI", details={
            "parcel_id": parcel_id,
            "locker_id": locker_id,
            "recipient_email_domain": recipient_email.split('@')[1] if '@' in recipient_email else 'unknown',
            "reported_via": "Web_UI_after_pickup",
            "admin_notified": admin_notification_success
        })
        
        flash('Your parcel has been reported as missing. The administrators have been notified and will investigate.', 'success')
        
        # Generate formatted datetime strings for the template
        from datetime import datetime
        now = datetime.utcnow()
        report_time = now.strftime('%Y-%m-%d %H:%M:%S')
        reference_date = now.strftime('%Y%m%d')
        
        return render_template('missing_report_confirmation.html', 
                               parcel_id=parcel_id,
                               report_time=report_time,
                               reference_date=reference_date)
        
    except Exception as e:
        current_app.logger.error(f"Error in report missing parcel route for parcel {parcel_id}: {str(e)}")
        flash('An unexpected error occurred. Please try again later.', 'error')
        return redirect(url_for('main.pickup_parcel'))

@main_bp.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        from app.services.admin_auth_service import AdminAuthService
        admin_user, message = AdminAuthService.authenticate_admin(username, password)

        if admin_user:
            AdminAuthService.create_session(admin_user)
            flash('Admin login successful!', 'success')
            # Redirect to admin dashboard (locker management)
            return redirect(url_for('main.manage_lockers'))
        else:
            flash(f'Login failed: {message}', 'error')
            return redirect(url_for('main.admin_login'))

    return render_template('admin/admin_login.html')

@main_bp.route('/admin/logout') # Basic logout
def admin_logout():
    from app.services.admin_auth_service import AdminAuthService
    AdminAuthService.logout()
    flash('You have been logged out.', 'info')
    return redirect(url_for('main.admin_login'))

@main_bp.route('/admin/audit-logs')
@admin_required
def audit_logs_view():
    # 🔥 ENHANCED AUDIT LOGGING: Track admin accessing audit logs
    admin_id = session.get('admin_id')
    admin_user = db.session.get(AdminUser, admin_id)
    admin_username = admin_user.username if admin_user else "UnknownAdmin"
    
    AuditService.log_event("ADMIN_ACCESSED_AUDIT_LOGS", {
        "admin_id": admin_id,
        "admin_username": admin_username,
        "logs_requested": 100  # Default limit
    })
    
    # Use the new audit service to get logs
    logs = AuditService.get_audit_logs(limit=100)
    return render_template('admin/audit_logs.html', logs=logs)

@main_bp.route('/admin/lockers', methods=['GET'])
@admin_required
def manage_lockers():
    # 🔥 ENHANCED AUDIT LOGGING: Track admin accessing locker management
    admin_id = session.get('admin_id')
    admin_user = db.session.get(AdminUser, admin_id)
    admin_username = admin_user.username if admin_user else "UnknownAdmin"
    
    enable_sensor_feature = current_app.config.get('ENABLE_LOCKER_SENSOR_DATA_FEATURE', True)
    default_sensor_state = current_app.config.get('DEFAULT_LOCKER_SENSOR_STATE_IF_UNAVAILABLE', False)

    lockers = Locker.query.order_by(Locker.id).all()
    
    # Count locker statuses for audit logging
    occupied_count = sum(1 for locker in lockers if locker.status == 'occupied')
    out_of_service_count = sum(1 for locker in lockers if locker.status == 'out_of_service')
    
    AuditService.log_event("ADMIN_ACCESSED_LOCKER_MANAGEMENT", {
        "admin_id": admin_id,
        "admin_username": admin_username,
        "total_lockers_viewed": len(lockers),
        "occupied_lockers": occupied_count,
        "out_of_service_lockers": out_of_service_count
    })
    
    lockers_with_parcels = []
    for locker in lockers:
        parcel_in_locker = None
        # Relevant parcel statuses that might be in an 'occupied' or 'disputed_contents' locker
        relevant_parcel_statuses = ['deposited', 'pickup_disputed', 'missing'] 
        if locker.status in ['occupied', 'disputed_contents', 'out_of_service']: 
            # Query for parcels in relevant states for this locker
            parcel_in_locker = Parcel.query.filter(
                Parcel.locker_id == locker.id,
                Parcel.status.in_(relevant_parcel_statuses)
            ).order_by(Parcel.id.desc()).first() # Get the latest relevant parcel
        
        latest_sensor_reading = None
        if enable_sensor_feature:
            # Fetch the latest sensor data for the locker only if feature is enabled
            latest_sensor_reading = LockerSensorData.query.filter_by(locker_id=locker.id).order_by(LockerSensorData.timestamp.desc()).first()
        
        lockers_with_parcels.append({
            'locker': locker, 
            'parcel': parcel_in_locker,
            'sensor_data': latest_sensor_reading 
        })
    return render_template(
        'admin/manage_lockers.html', 
        lockers_with_parcels=lockers_with_parcels,
        enable_sensor_feature=enable_sensor_feature,
        default_sensor_state=default_sensor_state
    )

@main_bp.route('/admin/parcel/<int:parcel_id>/view', methods=['GET'])
@admin_required
def view_parcel_admin(parcel_id):
    parcel = db.session.get(Parcel, parcel_id)
    if not parcel:
        flash(f"Parcel ID {parcel_id} not found.", "error")
        return redirect(url_for('main.manage_lockers'))
    
    # 🔥 ENHANCED AUDIT LOGGING: Track admin parcel viewing
    admin_id = session.get('admin_id')
    admin_user = db.session.get(AdminUser, admin_id)
    admin_username = admin_user.username if admin_user else "UnknownAdmin"
    
    AuditService.log_event("ADMIN_VIEWED_PARCEL", {
        "admin_id": admin_id,
        "admin_username": admin_username,
        "parcel_id": parcel_id,
        "parcel_status": parcel.status,
        "locker_id": parcel.locker_id,
        "recipient_email_domain": parcel.recipient_email.split('@')[1] if '@' in parcel.recipient_email else 'unknown'  # Privacy-friendly logging
    })
    
    locker = db.session.get(Locker, parcel.locker_id) if parcel.locker_id else None
    return render_template('admin/view_parcel.html', parcel=parcel, locker=locker)

@main_bp.route('/admin/parcel/<int:parcel_id>/mark-missing', methods=['POST'])
@admin_required
def mark_parcel_missing_admin_action(parcel_id):
    admin_id = session.get('admin_id')
    admin_user = db.session.get(AdminUser, admin_id)
    admin_username = admin_user.username if admin_user else "UnknownAdmin"

    parcel, error = mark_parcel_missing_by_admin(
        admin_id=admin_id,
        admin_username=admin_username,
        parcel_id=parcel_id
    )
    if error:
        flash(f"Error marking parcel {parcel_id} as missing: {error}", "error")
    else:
        flash(f"Parcel {parcel_id} successfully marked as missing.", "success")
    
    # Redirect to the parcel view page if parcel exists, otherwise to lockers list
    if parcel: 
        return redirect(url_for('main.view_parcel_admin', parcel_id=parcel_id))
    return redirect(url_for('main.manage_lockers'))

@main_bp.route('/request-new-pin', methods=['GET', 'POST'])
def request_new_pin_action():
    if request.method == 'POST':
        recipient_email = request.form.get('recipient_email')
        locker_id = request.form.get('locker_id')

        if not recipient_email or not locker_id:
            flash('Email and Locker ID are required.', 'error')
            return redirect(url_for('main.request_new_pin_action'))

        # Call the service function that handles both PIN systems
        parcel, message = request_pin_regeneration_by_recipient_email_and_locker(recipient_email, locker_id)

        # Always flash a generic message for security (to prevent fishing)
        flash("If your details matched an active parcel eligible for a new PIN, an email has been sent to the registered email address. Please check your inbox (and spam folder).", "info")
        return redirect(url_for('main.request_new_pin_action'))

    # Get PIN expiry hours from config for template
    from app.business.pin import PinManager
    pin_expiry_hours = PinManager.get_pin_expiry_hours()
    
    return render_template('request_new_pin_form.html', pin_expiry_hours=pin_expiry_hours)

@main_bp.route('/admin/locker/<int:locker_id>/mark-emptied', methods=['POST'])
@admin_required
def admin_mark_locker_emptied_action(locker_id):
    admin_id_from_session = session.get('admin_id')
    # It's good practice to ensure admin_id is actually in session,
    # though @admin_required should protect this.
    if not admin_id_from_session:
        flash("Admin session not found. Please log in again.", "error")
        return redirect(url_for('main.admin_login'))

    admin_user = db.session.get(AdminUser, admin_id_from_session)
    admin_username = admin_user.username if admin_user else "UnknownAdmin"
    
    # If admin_user is None here, it implies an issue with session or DB consistency
    # as @admin_required should have ensured a valid session.
    if not admin_user:
         current_app.logger.warning(f"Admin user with ID {admin_id_from_session} not found in DB during mark-emptied action for locker {locker_id}.")
         # Fallback, though ideally this state shouldn't be reached if @admin_required works.

    updated_locker, message = mark_locker_as_emptied(
        locker_id=locker_id,
        admin_id=admin_id_from_session,
        admin_username=admin_username
    )

    # The service function returns (Locker|None, message_string).
    # If updated_locker is None, it means the locker itself wasn't found.
    # If updated_locker is returned but message indicates an issue (e.g., "Locker is not awaiting collection."),
    # it's an operational error but not a DB error.
    if message == "Locker successfully marked as free.":
        flash(f"Locker {locker_id} status updated: {message}", "success")
    elif updated_locker is None and message == "Locker not found.": # Specific check for locker not found
        flash(f"Error for locker {locker_id}: {message}", "error")
    else: # Other errors or conditions like "Locker is not awaiting collection."
        flash(f"Notice for locker {locker_id}: {message}", "warning") # Use warning for non-critical errors

    return redirect(url_for('main.manage_lockers'))

@main_bp.route('/admin/parcels/process-overdue', methods=['POST'])
@admin_required
def admin_process_overdue_parcels_action():
    # 🔥 ENHANCED AUDIT LOGGING: Track admin bulk operations
    admin_id = session.get('admin_id')
    admin_user = db.session.get(AdminUser, admin_id)
    admin_username = admin_user.username if admin_user else "UnknownAdmin"
    
    # Log the initiation of bulk operation
    AuditService.log_event("ADMIN_INITIATED_BULK_PROCESS_OVERDUE", {
        "admin_id": admin_id,
        "admin_username": admin_username,
        "operation_type": "process_overdue_parcels"
    })
    
    processed_count, message = process_overdue_parcels()
    
    # Log the completion of bulk operation
    AuditService.log_event("ADMIN_COMPLETED_BULK_PROCESS_OVERDUE", {
        "admin_id": admin_id,
        "admin_username": admin_username,
        "processed_count": processed_count,
        "operation_result": message,
        "operation_type": "process_overdue_parcels"
    })
    
    flash(f"Overdue parcel processing complete. {processed_count} parcels processed. {message}", "info")
    return redirect(url_for('main.manage_lockers'))

@main_bp.route('/admin/parcel/<int:parcel_id>/reissue-pin', methods=['POST'])
@admin_required
def reissue_pin_admin_action(parcel_id):
    # Admin ID and username could be fetched from session for logging if needed by reissue_pin,
    # but the current reissue_pin service doesn't require them as direct params.
    # It logs events internally.
    
    parcel, message = reissue_pin(parcel_id)

    if parcel: # Success is indicated by the parcel object being returned
        flash(f"Successfully reissued PIN for parcel {parcel_id}. {message}", "success")
    else: # An error occurred
        flash(f"Error reissuing PIN for parcel {parcel_id}: {message}", "error")
    
    return redirect(url_for('main.view_parcel_admin', parcel_id=parcel_id))

@main_bp.route('/admin/parcel/<int:parcel_id>/regenerate-pin-token', methods=['POST'])
@admin_required
def regenerate_pin_token_admin_action(parcel_id):
    """Admin action to regenerate PIN generation token for email-based PIN parcels"""
    try:
        parcel = db.session.get(Parcel, parcel_id)
        if not parcel:
            flash(f"Parcel ID {parcel_id} not found.", "error")
            return redirect(url_for('main.manage_lockers'))
        
        # Check if this parcel uses email-based PIN generation
        if not current_app.config.get('ENABLE_EMAIL_BASED_PIN_GENERATION', True):
            flash("Email-based PIN generation is not enabled.", "error")
            return redirect(url_for('main.view_parcel_admin', parcel_id=parcel_id))
        
        # Regenerate PIN token
        success, message = regenerate_pin_token(parcel_id, parcel.recipient_email)
        
        if success:
            flash(f"Successfully regenerated PIN generation link for parcel {parcel_id}. {message}", "success")
        else:
            flash(f"Error regenerating PIN generation link for parcel {parcel_id}: {message}", "error")
        
        return redirect(url_for('main.view_parcel_admin', parcel_id=parcel_id))
        
    except Exception as e:
        current_app.logger.error(f"Error in regenerate PIN token admin action: {str(e)}")
        flash(f"An unexpected error occurred while regenerating PIN token for parcel {parcel_id}.", "error")
        return redirect(url_for('main.view_parcel_admin', parcel_id=parcel_id))

@main_bp.route('/admin/locker/<int:locker_id>/set-status', methods=['POST'])
@admin_required
def update_locker_status(locker_id):
    new_status = request.form.get('new_status')
    admin_id = session.get('admin_id') 
    
    admin_user = db.session.get(AdminUser, admin_id)
    admin_username = admin_user.username if admin_user else "UnknownAdmin"

    if not new_status:
        flash("No new status provided.", "error")
        return redirect(url_for('main.manage_lockers'))

    locker, error = set_locker_status(
        admin_id=admin_id, 
        admin_username=admin_username, 
        locker_id=locker_id, 
        new_status=new_status
    )

    if error:
        flash(f"Error updating locker {locker_id}: {error}", "error")
    else:
        flash(f"Locker {locker_id} status successfully updated to '{new_status}'.", "success")
    
    return redirect(url_for('main.manage_lockers'))

@main_bp.route('/system/process-reminders', methods=['POST', 'GET'])
def automatic_reminder_processing():
    """
    FR-04: Automatic bulk reminder processing endpoint (no admin auth required)
    FR-04: This endpoint is designed to be called automatically by scheduled tasks
    FR-04: Processes all eligible parcels and sends reminder notifications
    
    This is a system endpoint that can be called by:
    - Cron jobs
    - Health check systems
    - Automated monitoring scripts
    - Docker container scheduled tasks
    
    No authentication required for automation purposes.
    """
    try:
        # FR-04: Process all eligible reminders automatically
        processed_count, error_count = process_reminder_notifications()
        
        # FR-04: Log the automatic processing event
        AuditService.log_event("FR-04_AUTOMATIC_BULK_REMINDER_PROCESSING", {
            "processed_count": processed_count,
            "error_count": error_count,
            "total_eligible": processed_count + error_count,
            "trigger_source": "automatic_system_endpoint",
            "success_rate": f"{(processed_count / (processed_count + error_count) * 100) if (processed_count + error_count) > 0 else 100:.1f}%"
        })
        
        # FR-04: Return JSON response for automated callers
        if request.method == 'GET':
            # Allow GET for simple health check / monitoring
            return jsonify({
                "status": "success",
                "message": f"Automatic reminder processing completed",
                "processed_count": processed_count,
                "error_count": error_count,
                "total_eligible": processed_count + error_count
            }), 200
        else:
            # POST request - return status
            return jsonify({
                "status": "success",
                "message": f"Processed {processed_count} reminders, {error_count} errors",
                "processed_count": processed_count,
                "error_count": error_count
            }), 200
            
    except Exception as e:
        current_app.logger.error(f"FR-04: Error in automatic reminder processing: {str(e)}")
        
        # FR-04: Log the error for debugging
        AuditService.log_event("FR-04_AUTOMATIC_REMINDER_PROCESSING_ERROR", {
            "error_message": str(e),
            "trigger_source": "automatic_system_endpoint"
        })
        
        return jsonify({
            "status": "error",
            "message": f"Error processing reminders: {str(e)}",
            "processed_count": 0,
            "error_count": 1
        }), 500
