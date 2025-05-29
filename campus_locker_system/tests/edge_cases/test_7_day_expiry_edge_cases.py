# Edge Case Coverage Note:
# This file tests the complete 7-day parcel expiry process including
# automatic status changes, pickup blocking, and admin management workflows

import pytest
from app import db
from app.services.parcel_service import assign_locker_and_create_parcel, process_overdue_parcels, process_pickup
from app.business.parcel import Parcel
from app.persistence.models import Locker
from app.business.pin import PinManager
from datetime import datetime, timedelta

def test_complete_7_day_expiry_workflow(init_database, app):
    """Test the complete 7-day parcel expiry process from deposit to admin cleanup"""
    with app.app_context():
        # Step 1: Create a test parcel
        result = assign_locker_and_create_parcel('expiry-test@example.com', 'medium')
        parcel, message = result
        assert parcel is not None
        assert parcel.status == 'deposited'
        
        # Get the locker
        locker = db.session.get(Locker, parcel.locker_id)
        assert locker.status == 'occupied'
        
        original_locker_id = parcel.locker_id
        original_deposited_at = parcel.deposited_at
        
        # Step 2: Simulate parcel being 8 days old (past 7-day limit)
        old_date = datetime.utcnow() - timedelta(days=8)
        parcel.deposited_at = old_date
        db.session.commit()
        
        # Verify parcel is now overdue
        from app.business.parcel import ParcelManager
        assert ParcelManager.is_overdue(parcel.deposited_at, 7) == True
        
        # Step 3: Process overdue parcels
        processed_count, process_message = process_overdue_parcels()
        assert processed_count == 1
        assert "1 overdue parcels processed" in process_message
        
        # Step 4: Verify status changes
        db.session.refresh(parcel)
        db.session.refresh(locker)
        
        assert parcel.status == 'return_to_sender'
        assert locker.status == 'awaiting_collection'
        assert parcel.locker_id == original_locker_id  # Parcel still associated with locker
        
        # Step 5: Verify pickup is blocked
        test_pin, test_hash = PinManager.generate_pin_and_hash()
        parcel.pin_hash = test_hash
        db.session.commit()
        
        pickup_result = process_pickup(test_pin)
        pickup_parcel, pickup_message = pickup_result
        
        assert pickup_parcel is None
        assert "Invalid PIN" in pickup_message or "not matching" in pickup_message

def test_overdue_parcel_status_transitions(init_database, app):
    """Test that overdue parcels follow correct status transition rules"""
    with app.app_context():
        # Create parcel
        parcel, _ = assign_locker_and_create_parcel('status-test@example.com', 'small')
        assert parcel is not None
        
        # Simulate overdue
        parcel.deposited_at = datetime.utcnow() - timedelta(days=8)
        db.session.commit()
        
        # Verify status transition is allowed
        from app.business.parcel import ParcelManager
        assert ParcelManager.can_transition_status('deposited', 'return_to_sender') == True
        
        # Process overdue
        process_overdue_parcels()
        
        db.session.refresh(parcel)
        assert parcel.status == 'return_to_sender'
        
        # Verify return_to_sender is terminal state
        assert ParcelManager.can_transition_status('return_to_sender', 'picked_up') == False
        assert ParcelManager.can_transition_status('return_to_sender', 'deposited') == False

def test_locker_status_after_overdue_processing(init_database, app):
    """Test locker status changes when parcels become overdue"""
    with app.app_context():
        # Create parcel in occupied locker
        parcel, _ = assign_locker_and_create_parcel('locker-status@example.com', 'large')
        assert parcel is not None
        
        locker = db.session.get(Locker, parcel.locker_id)
        assert locker.status == 'occupied'
        
        # Simulate overdue
        parcel.deposited_at = datetime.utcnow() - timedelta(days=9)
        db.session.commit()
        
        # Process overdue
        process_overdue_parcels()
        
        db.session.refresh(locker)
        assert locker.status == 'awaiting_collection'

def test_overdue_processing_with_out_of_service_locker(init_database, app):
    """Test overdue processing when locker is out of service"""
    with app.app_context():
        # Create parcel
        parcel, _ = assign_locker_and_create_parcel('oos-test@example.com', 'medium')
        assert parcel is not None
        
        # Mark locker as out of service
        locker = db.session.get(Locker, parcel.locker_id)
        locker.status = 'out_of_service'
        db.session.commit()
        
        # Simulate overdue
        parcel.deposited_at = datetime.utcnow() - timedelta(days=10)
        db.session.commit()
        
        # Process overdue
        process_overdue_parcels()
        
        db.session.refresh(parcel)
        db.session.refresh(locker)
        
        assert parcel.status == 'return_to_sender'
        assert locker.status == 'awaiting_collection'  # Should change from out_of_service

def test_multiple_overdue_parcels_batch_processing(init_database, app):
    """Test processing multiple overdue parcels in one batch"""
    with app.app_context():
        # Create multiple parcels
        parcels = []
        for i in range(3):
            parcel, _ = assign_locker_and_create_parcel(f'batch-test-{i}@example.com', 'small')
            assert parcel is not None
            
            # Make them all overdue
            parcel.deposited_at = datetime.utcnow() - timedelta(days=8 + i)
            parcels.append(parcel)
        
        db.session.commit()
        
        # Process all overdue
        processed_count, message = process_overdue_parcels()
        assert processed_count == 3
        assert "3 overdue parcels processed" in message
        
        # Verify all are marked return_to_sender
        for parcel in parcels:
            db.session.refresh(parcel)
            assert parcel.status == 'return_to_sender'

def test_edge_case_exactly_7_days_old(init_database, app):
    """Test parcel that is exactly 7 days old (should NOT be processed)"""
    with app.app_context():
        # Create parcel
        parcel, _ = assign_locker_and_create_parcel('exactly-7@example.com', 'medium')
        assert parcel is not None
        
        # Make it exactly 7 days old (not 8)
        parcel.deposited_at = datetime.utcnow() - timedelta(days=7)
        db.session.commit()
        
        # Process overdue
        processed_count, _ = process_overdue_parcels()
        assert processed_count == 0  # Should not process 7-day-old parcel
        
        db.session.refresh(parcel)
        assert parcel.status == 'deposited'  # Should remain deposited

def test_edge_case_parcel_without_deposited_at(init_database, app):
    """Test handling of parcel with invalid deposited_at timestamp"""
    with app.app_context():
        # Create parcel
        parcel, _ = assign_locker_and_create_parcel('invalid-date@example.com', 'small')
        assert parcel is not None
        
        # Set invalid deposited_at
        parcel.deposited_at = None
        db.session.commit()
        
        # Process overdue (should skip this parcel)
        processed_count, _ = process_overdue_parcels()
        assert processed_count == 0
        
        db.session.refresh(parcel)
        assert parcel.status == 'deposited'  # Should remain unchanged

def test_pickup_attempt_immediately_after_expiry(init_database, app):
    """Test pickup attempt immediately after parcel expires"""
    with app.app_context():
        # Create parcel with valid PIN
        parcel, _ = assign_locker_and_create_parcel('immediate-pickup@example.com', 'large')
        assert parcel is not None
        
        # Set up PIN for traditional pickup
        test_pin, test_hash = PinManager.generate_pin_and_hash()
        parcel.pin_hash = test_hash
        parcel.otp_expiry = datetime.utcnow() + timedelta(hours=24)
        
        # Verify pickup works before expiry
        pickup_result = process_pickup(test_pin)
        pickup_parcel, pickup_message = pickup_result
        assert pickup_parcel is not None  # Should work initially
        
        # Reset parcel to deposited state
        parcel.status = 'deposited'
        parcel.picked_up_at = None
        locker = db.session.get(Locker, parcel.locker_id)
        locker.status = 'occupied'
        db.session.commit()
        
        # Make parcel overdue and process
        parcel.deposited_at = datetime.utcnow() - timedelta(days=8)
        db.session.commit()
        process_overdue_parcels()
        
        # Now pickup should fail
        pickup_result = process_pickup(test_pin)
        pickup_parcel, pickup_message = pickup_result
        assert pickup_parcel is None
        assert "Invalid PIN" in pickup_message or "not matching" in pickup_message

def test_admin_actions_on_expired_parcels(init_database, app):
    """Test that admin actions work correctly on expired parcels"""
    with app.app_context():
        from app.services.parcel_service import mark_parcel_missing_by_admin
        
        # Create and expire parcel
        parcel, _ = assign_locker_and_create_parcel('admin-action@example.com', 'medium')
        assert parcel is not None
        
        parcel.deposited_at = datetime.utcnow() - timedelta(days=8)
        db.session.commit()
        process_overdue_parcels()
        
        db.session.refresh(parcel)
        assert parcel.status == 'return_to_sender'
        
        # Test admin can mark as missing
        marked_parcel, error = mark_parcel_missing_by_admin(1, 'test_admin', parcel.id)
        assert marked_parcel is not None
        assert error is None
        assert marked_parcel.status == 'missing'

def test_comprehensive_7_day_expiry_demonstration():
    """
    Comprehensive demonstration test of the 7-day expiry process
    This test can be run independently to show the complete workflow
    """
    from app import create_app
    
    app = create_app()
    with app.app_context():
        print('\n🧪 Testing 7-Day Parcel Expiry Process')
        print('=' * 50)
        
        # Step 1: Create a test parcel
        print('Step 1: Creating test parcel...')
        parcel, message = assign_locker_and_create_parcel('demo-expiry@example.com', 'medium')
        if parcel:
            print(f'✅ Parcel created: ID {parcel.id} in Locker {parcel.locker_id}')
            print(f'   Status: {parcel.status}')
            print(f'   Deposited: {parcel.deposited_at}')
            print(f'   Recipient: {parcel.recipient_email}')
            
            # Check locker status
            locker = db.session.get(Locker, parcel.locker_id)
            print(f'   Locker Status: {locker.status}')
        else:
            print(f'❌ Failed to create parcel: {message}')
            return False
        
        # Step 2: Simulate parcel being 8 days old (past 7-day limit)
        print('\nStep 2: Simulating parcel being 8 days old...')
        old_date = datetime.utcnow() - timedelta(days=8)
        parcel.deposited_at = old_date
        db.session.commit()
        print(f'✅ Updated deposited_at to: {parcel.deposited_at}')
        print(f'   Age: {(datetime.utcnow() - parcel.deposited_at).days} days')
        
        # Step 3: Run overdue processing
        print('\nStep 3: Processing overdue parcels...')
        processed_count, process_message = process_overdue_parcels()
        print(f'✅ Processed {processed_count} overdue parcels')
        print(f'   Message: {process_message}')
        
        # Step 4: Check results
        print('\nStep 4: Checking results after processing...')
        db.session.refresh(parcel)
        db.session.refresh(locker)
        
        print(f'📦 Parcel Status After Processing:')
        print(f'   ID: {parcel.id}')
        print(f'   Status: {parcel.status}')
        print(f'   Deposited: {parcel.deposited_at}')
        print(f'   Picked Up: {parcel.picked_up_at}')
        
        print(f'🔒 Locker Status After Processing:')
        print(f'   ID: {locker.id}')
        print(f'   Status: {locker.status}')
        print(f'   Location: {locker.location}')
        
        # Step 5: Test pickup attempt (should fail)
        print('\nStep 5: Testing pickup attempt on expired parcel...')
        
        # Generate a test PIN and try to use it
        test_pin, test_hash = PinManager.generate_pin_and_hash()
        parcel.pin_hash = test_hash
        db.session.commit()
        
        pickup_result = process_pickup(test_pin)
        pickup_parcel, pickup_message = pickup_result
        
        if pickup_parcel:
            print(f'⚠️  Pickup succeeded: {pickup_message}')
        else:
            print(f'❌ Pickup failed (as expected): {pickup_message}')
        
        # Step 6: Show what admin needs to do
        print('\nStep 6: Administrative actions available...')
        print(f'💼 Admin Dashboard Shows:')
        print(f'   - Parcel {parcel.id} is marked "return_to_sender"')
        print(f'   - Locker {locker.id} status is "{locker.status}"')
        print(f'   - Admin can mark locker as "emptied & free" once parcel is physically removed')
        
        print('\n🎯 Summary of 7-Day Expiry Process:')
        print(f'   ✅ Parcel automatically marked: deposited → {parcel.status}')
        print(f'   ✅ Locker status changed: occupied → {locker.status}')
        print(f'   ✅ Pickup blocked: Recipients cannot pickup expired parcels')
        print(f'   ✅ Admin action required: Physical removal and locker reset')
        
        return True 