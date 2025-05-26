from flask import render_template, request, redirect, url_for, flash, session, current_app # Add current_app
from . import main_bp # Assuming main_bp is defined in app/presentation/__init__.py
from app.application.services import (
    assign_locker_and_create_parcel, 
    process_pickup, 
    verify_admin_credentials, 
    log_audit_event, # Add log_audit_event
    set_locker_status, # Add set_locker_status
    mark_parcel_missing_by_admin, # Add this
    reissue_pin, # Add reissue_pin
    process_overdue_parcels, # Add process_overdue_parcels
    mark_locker_as_emptied, # Add mark_locker_as_emptied
    request_pin_regeneration_by_recipient # Add request_pin_regeneration_by_recipient
)
from app.persistence.models import Locker, AuditLog, AdminUser, Parcel, LockerSensorData # Add LockerSensorData
from .decorators import admin_required # Add admin_required decorator
from app import db # Add db for session.get

@main_bp.route('/', methods=['GET']) # Optional: redirect root to deposit page
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

        parcel, pin, error_message = assign_locker_and_create_parcel(parcel_size, recipient_email)

        print(f"DEBUG: error_message from assign_locker_and_create_parcel: {error_message}")

        if error_message:
            flash(f'Error: {error_message}', 'error')
            return redirect(url_for('main.deposit_parcel'))

        if parcel and pin:
            # We need the actual locker number/identifier to display.
            # The 'parcel' object has 'locker_id', which is the foreign key.
            # We can use this ID to fetch the locker object or just display the ID.
            # For simplicity, let's assume locker_id is sufficient as "Locker ID".
            flash('Parcel deposited successfully!', 'success')
            return render_template('deposit_confirmation.html', locker_id=parcel.locker_id, pin=pin)
        else:
            # This case should ideally be covered by error_message, but as a fallback:
            flash('An unexpected error occurred.', 'error')
            return redirect(url_for('main.deposit_parcel'))

    return render_template('deposit_form.html')

@main_bp.route('/pickup', methods=['GET', 'POST'])
def pickup_parcel():
    if request.method == 'POST':
        pin_provided = request.form.get('pin')

        if not pin_provided or not pin_provided.isdigit() or len(pin_provided) != 6:
            flash('Please enter a valid 6-digit PIN.', 'error')
            return redirect(url_for('main.pickup_parcel'))

        parcel, locker, error_message = process_pickup(pin_provided)

        if error_message:
            flash(f'Error: {error_message}', 'error')
            return redirect(url_for('main.pickup_parcel'))

        if parcel and locker:
            flash('Parcel picked up successfully!', 'success')
            return render_template('pickup_confirmation.html', locker_id=locker.id) # or locker.name if it has one
        else:
            # This case should ideally be covered by error_message
            flash('An unexpected error occurred during pickup.', 'error')
            return redirect(url_for('main.pickup_parcel'))

    return render_template('pickup_form.html')

@main_bp.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        admin_user = verify_admin_credentials(username, password)

        if admin_user:
            session['admin_id'] = admin_user.id # Store admin_id in session
            log_audit_event("ADMIN_LOGIN_SUCCESS", {
                "admin_username": admin_user.username, 
                "admin_id": admin_user.id
            })
            flash('Admin login successful!', 'success')
            # Redirect to a future admin dashboard page
            # For now, redirect to deposit page or a simple success message page
            return redirect(url_for('main.deposit_parcel')) # Placeholder redirect
        else:
            log_audit_event("ADMIN_LOGIN_FAIL", {"username_attempted": username})
            flash('Invalid admin credentials.', 'error')
            return redirect(url_for('main.admin_login'))

    return render_template('admin/admin_login.html')

@main_bp.route('/admin/logout') # Basic logout
def admin_logout():
    admin_id_from_session = session.get('admin_id')
    if admin_id_from_session:
        log_audit_event("ADMIN_LOGOUT", {"admin_id": admin_id_from_session})
    
    session.pop('admin_id', None)
    flash('You have been logged out.', 'info')
    return redirect(url_for('main.admin_login'))

@main_bp.route('/admin/audit-logs')
@admin_required
def audit_logs_view():
    # Query the latest 100 audit logs, newest first
    logs = AuditLog.query.order_by(AuditLog.timestamp.desc()).limit(100).all()
    return render_template('admin/audit_logs.html', logs=logs)

@main_bp.route('/admin/lockers', methods=['GET'])
@admin_required
def manage_lockers():
    enable_sensor_feature = current_app.config.get('ENABLE_LOCKER_SENSOR_DATA_FEATURE', True)
    default_sensor_state = current_app.config.get('DEFAULT_LOCKER_SENSOR_STATE_IF_UNAVAILABLE', False)

    lockers = Locker.query.order_by(Locker.id).all()
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

        request_pin_regeneration_by_recipient(recipient_email, locker_id) # Call the actual service

        # Always flash the same generic message for security (to prevent fishing)
        flash("If your details matched an active parcel eligible for a new PIN, an email with the new PIN has been sent to the registered email address. Please check your inbox (and spam folder).", "info")
        return redirect(url_for('main.request_new_pin_action'))

    return render_template('request_new_pin_form.html')

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
    processed_count, message = process_overdue_parcels()
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
