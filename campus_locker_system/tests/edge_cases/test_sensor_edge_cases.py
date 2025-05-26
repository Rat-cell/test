# Edge Case Coverage Note:
# This file tests error handling for the locker sensor data API endpoint.

import pytest
from app import db
from app.persistence.models import Locker

# Test: Submitting sensor data with missing 'has_contents' field should return 400
def test_sensor_data_missing_has_contents(client, init_database, app):
    with app.app_context():
        locker = Locker.query.first()
        response = client.post(f'/api/v1/lockers/{locker.id}/sensor_data', json={})
        assert response.status_code == 400
        assert b'has_contents' in response.data or b'error' in response.data

# Test: Submitting sensor data with non-boolean 'has_contents' should return 400
def test_sensor_data_invalid_type(client, init_database, app):
    with app.app_context():
        locker = Locker.query.first()
        response = client.post(f'/api/v1/lockers/{locker.id}/sensor_data', json={'has_contents': 'not_a_boolean'})
        assert response.status_code == 400
        assert b'has_contents' in response.data or b'error' in response.data

# Test: Submitting sensor data for a non-existent locker should return 404
def test_sensor_data_nonexistent_locker(client, init_database, app):
    with app.app_context():
        response = client.post('/api/v1/lockers/99999/sensor_data', json={'has_contents': True})
        assert response.status_code == 404 or response.status_code == 400
        assert b'locker' in response.data or b'error' in response.data 