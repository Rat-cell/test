from flask import render_template, request, redirect, url_for, flash, session # Add session
from . import main_bp # Assuming main_bp is defined in app/presentation/__init__.py
from app.application.services import (
    assign_locker_and_create_parcel, 
    process_pickup, 
    verify_admin_credentials, 
    log_audit_event, # Add log_audit_event
    set_locker_status, # Add set_locker_status
    mark_parcel_missing_by_admin # Add this
)
from app.persistence.models import Locker, AuditLog, AdminUser, Parcel # Add AdminUser and Parcel
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

        parcel, pin, error_message = assign_locker_and_create_parcel(parcel_size, recipient_email)

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
        lockers_with_parcels.append({'locker': locker, 'parcel': parcel_in_locker})
    return render_template('admin/manage_lockers.html', lockers_with_parcels=lockers_with_parcels)

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
