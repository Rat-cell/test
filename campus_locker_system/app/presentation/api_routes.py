from flask import Blueprint, jsonify, request
from app.application.services import retract_deposit, dispute_pickup
# Assuming Locker model might be needed if we access parcel.locker.status directly in the response
# from app.persistence.models import Locker 

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
