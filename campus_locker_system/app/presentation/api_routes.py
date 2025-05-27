from flask import Blueprint, jsonify, request, current_app
from app.services.parcel_service import retract_deposit, dispute_pickup, report_parcel_missing_by_recipient
from app.persistence.models import Locker, LockerSensorData # Import LockerSensorData and Locker
from app import db # Import db

api_bp = Blueprint('api', __name__, url_prefix='/api/v1')

@api_bp.route('/deposit/<int:parcel_id>/retract', methods=['POST'])
def handle_deposit_retraction(parcel_id):
    # Authentication/Authorization for locker client would go here in a real system
    # For now, proceed directly to service call.
    
    parcel, error = retract_deposit(parcel_id)
    if error:
        # Consider more specific HTTP status codes, e.g., 404 if not found, 400/409 if bad state
        # For example:
        if "not found" in error.lower():
            status_code = 404
        elif "not in 'deposited' state" in error.lower():
            status_code = 409 # Conflict with current state
        else:
            status_code = 400 # Bad request or other client error
        return jsonify({"status": "error", "message": error}), status_code
        
    return jsonify({
        "status": "success", 
        "message": "Deposit retracted successfully.", 
        "parcel_id": parcel.id, 
        "new_parcel_status": parcel.status, 
        "locker_id": parcel.locker_id, 
        "new_locker_status": parcel.locker.status # Accessing locker status via backref
    }), 200

@api_bp.route('/lockers/<int:locker_id>/sensor_data', methods=['POST'])
def submit_locker_sensor_data(locker_id):
    # Placeholder for future authentication/authorization
    # e.g., client_api_key = request.headers.get('X-API-KEY')
    # if not is_valid_client_key(client_api_key):
    #     return jsonify({"status": "error", "message": "Unauthorized"}), 401

    data = request.get_json()
    if not data:
        return jsonify({"status": "error", "message": "No data provided"}), 400

    has_contents = data.get('has_contents')
    if not isinstance(has_contents, bool): # Checks if it's a boolean, also covers if it's None
        return jsonify({"status": "error", "message": "'has_contents' must be a boolean and is required"}), 400

    # Check if the locker exists
    locker = db.session.get(Locker, locker_id)
    if not locker:
        return jsonify({"status": "error", "message": "Locker not found"}), 404

    try:
        sensor_data_entry = LockerSensorData(
            locker_id=locker_id,
            has_contents=has_contents
        )
        db.session.add(sensor_data_entry)
        db.session.commit()
        return jsonify({
            "status": "success",
            "message": "Sensor data recorded successfully.",
            "sensor_data_id": sensor_data_entry.id
        }), 201
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Failed to record sensor data for locker {locker_id}: {str(e)}")
        return jsonify({"status": "error", "message": "Failed to record sensor data"}), 500

@api_bp.route('/parcel/<int:parcel_id>/report-missing', methods=['POST'])
def handle_parcel_report_missing(parcel_id):
    # Authentication/Authorization for locker client would go here in a real system.
    # This might also involve checking if the PIN for this parcel_id was recently used at this specific locker terminal.
    # For now, proceed directly to service call.
    
    parcel, error = report_parcel_missing_by_recipient(parcel_id)
    
    if error:
        # Determine appropriate HTTP status code based on error type
        status_code = 400 # Generic client error
        if "not found" in error.lower():
            status_code = 404
        elif "cannot be reported missing by recipient from its current state" in error.lower(): # Specific error from service
            status_code = 409 # Conflict with current state
        return jsonify({"status": "error", "message": error}), status_code
        
    if parcel:
        # The service function report_parcel_missing_by_recipient does not return the locker object.
        # So, new_locker_status cannot be directly accessed here unless the service is changed or we re-fetch.
        # For this subtask, we will omit new_locker_status from the response.
        return jsonify({
            "status": "success", 
            "message": "Parcel successfully reported as missing.",
            "parcel_id": parcel.id,
            "new_parcel_status": parcel.status, # Should be 'missing'
            "locker_id": parcel.locker_id
            # "new_locker_status": parcel.locker.status # Omitted for now
        }), 200
    else:
        # Should be caught by the error condition, but as a fallback
        return jsonify({"status": "error", "message": "Failed to report parcel missing for an unknown reason."}), 500

@api_bp.route('/pickup/<int:parcel_id>/dispute', methods=['POST'])
def handle_pickup_dispute(parcel_id):
    # Authentication/Authorization for locker client
    
    parcel, error = dispute_pickup(parcel_id)
    if error:
        if "not found" in error.lower():
            status_code = 404
        elif "not in 'picked_up' state" in error.lower():
            status_code = 409 # Conflict
        else:
            status_code = 400
        return jsonify({"status": "error", "message": error}), status_code
        
    return jsonify({
        "status": "success", 
        "message": "Pickup disputed successfully.", 
        "parcel_id": parcel.id, 
        "new_parcel_status": parcel.status, 
        "locker_id": parcel.locker_id, 
        "new_locker_status": parcel.locker.status # Accessing locker status via backref
    }), 200
