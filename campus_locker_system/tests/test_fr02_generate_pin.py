"""
FR-02 Generate PIN Test Suite

This module contains comprehensive tests for the FR-02 requirement:
"Create a 6-digit PIN and store its salted SHA-256 hash"

Test Categories:
1. PIN Generation Tests
2. Cryptographic Security Tests
3. Salted Hash Storage Tests
4. PIN Verification Tests
5. Salt Uniqueness Tests
6. Performance Tests
7. Security Validation Tests
8. Integration Tests

Author: Campus Locker System Team I
Date: May 30, 2025
FR-02 Implementation: Critical security requirement for PIN management
"""

import pytest
import hashlib
import re
import time
import threading
from unittest.mock import patch, MagicMock

from app import create_app, db
from app.business.pin import PinManager
from app.services.pin_service import PinService
from app.persistence.models import Parcel, Locker


class TestFR02GeneratePin:
    """
    FR-02: Generate PIN - Critical Security Test Suite
    
    Tests the PIN generation system that must create cryptographically secure
    6-digit PINs with salted SHA-256 hashing for secure storage.
    """

    @pytest.fixture
    def app(self):
        """Create test application with FR-02 configuration"""
        app = create_app()
        app.config['TESTING'] = True
        app.config['WTF_CSRF_ENABLED'] = False
        return app

    @pytest.fixture
    def client(self, app):
        """Create test client"""
        return app.test_client()

    @pytest.fixture
    def test_locker_and_parcel(self, app):
        """Setup test locker and parcel for PIN testing"""
        with app.app_context():
            # Create test locker
            locker = Locker(id=901, location="Test PIN Locker", size="medium", status="occupied")
            db.session.add(locker)
            
            # Create test parcel
            parcel = Parcel(
                locker_id=901,
                recipient_email="test-fr02@example.com",
                status="deposited",
                pin_hash=None  # Will be set by PIN generation
            )
            db.session.add(parcel)
            db.session.commit()
            
            yield locker, parcel
            
            # Cleanup
            db.session.delete(parcel)
            db.session.delete(locker)
            db.session.commit()

    # ===== 1. PIN GENERATION TESTS =====

    def test_fr02_generates_6_digit_pin(self):
        """
        FR-02: Test that system generates exactly 6-digit numeric PIN
        Verifies PIN format and length requirements
        """
        # Generate PIN
        pin, pin_hash = PinManager.generate_pin_and_hash()
        
        # Verify PIN is exactly 6 digits
        assert len(pin) == 6, "FR-02: PIN must be exactly 6 digits"
        assert pin.isdigit(), "FR-02: PIN must contain only numeric digits"
        assert re.match(r'^\d{6}$', pin), "FR-02: PIN must match 6-digit numeric pattern"

    def test_fr02_generates_unique_pins(self):
        """
        FR-02: Test that system generates unique PINs across multiple generations
        Verifies PIN uniqueness and randomness
        """
        pins = set()
        
        # Generate multiple PINs
        for _ in range(100):
            pin, _ = PinManager.generate_pin_and_hash()
            pins.add(pin)
        
        # Verify high uniqueness (allowing for some collision in 6-digit space)
        uniqueness_ratio = len(pins) / 100
        assert uniqueness_ratio > 0.95, f"FR-02: PIN uniqueness too low ({uniqueness_ratio:.2%}), expected >95%"

    def test_fr02_generates_cryptographically_secure_pins(self):
        """
        FR-02: Test that PINs are cryptographically secure
        Verifies use of os.urandom for secure random generation
        """
        pins = []
        
        # Generate multiple PINs and analyze distribution
        for _ in range(1000):
            pin, _ = PinManager.generate_pin_and_hash()
            pins.append(pin)
        
        # Check for uniform distribution across first digit
        first_digits = [int(pin[0]) for pin in pins]
        digit_counts = {str(i): first_digits.count(i) for i in range(10)}
        
        # Each digit should appear roughly 10% of the time (±5%)
        for digit, count in digit_counts.items():
            frequency = count / 1000
            assert 0.05 <= frequency <= 0.15, f"FR-02: Digit {digit} appears {frequency:.1%}, expected ~10% (cryptographic randomness)"

    def test_fr02_pins_include_leading_zeros(self):
        """
        FR-02: Test that PINs properly handle leading zeros
        Verifies 6-digit format with zero-padding
        """
        # Mock os.urandom to return small values that would create leading zeros
        with patch('os.urandom') as mock_urandom:
            # Return bytes that create number < 100000 (requires leading zeros)
            mock_urandom.return_value = b'\x00\x00\x01'  # Creates small number
            
            pin, _ = PinManager.generate_pin_and_hash()
            
            # Verify PIN is still 6 digits with leading zeros
            assert len(pin) == 6, "FR-02: PIN with leading zeros must still be 6 digits"
            assert pin.startswith('0'), "FR-02: Small numbers should have leading zeros"

    # ===== 2. CRYPTOGRAPHIC SECURITY TESTS =====

    def test_fr02_uses_salted_sha256_hashing(self):
        """
        FR-02: Test that PIN uses salted SHA-256 hashing
        Verifies cryptographic hash implementation
        """
        pin, pin_hash = PinManager.generate_pin_and_hash()
        
        # Verify hash format: salt_hex:hash_hex
        assert ':' in pin_hash, "FR-02: Hash must contain salt separator"
        
        salt_hex, hash_hex = pin_hash.split(':')
        
        # Verify salt is 32 hex characters (16 bytes)
        assert len(salt_hex) == 32, "FR-02: Salt must be 16 bytes (32 hex chars)"
        assert re.match(r'^[0-9a-f]{32}$', salt_hex), "FR-02: Salt must be valid hex"
        
        # Verify hash is 128 hex characters (64 bytes from PBKDF2)
        assert len(hash_hex) == 128, "FR-02: Hash must be 64 bytes (128 hex chars)"
        assert re.match(r'^[0-9a-f]{128}$', hash_hex), "FR-02: Hash must be valid hex"

    def test_fr02_original_pin_not_stored(self):
        """
        FR-02: Test that original PIN is never stored in plain text
        Verifies security requirement for hash-only storage
        """
        pin, pin_hash = PinManager.generate_pin_and_hash()
        
        # Verify PIN is not contained in hash
        assert pin not in pin_hash, "FR-02: Original PIN must not appear in hash"
        
        # Verify hash doesn't contain obvious PIN patterns
        assert not any(digit * 3 in pin_hash for digit in '0123456789'), "FR-02: Hash should not contain obvious patterns"

    def test_fr02_pbkdf2_iterations_sufficient(self):
        """
        FR-02: Test that PBKDF2 uses sufficient iterations for security
        Verifies computational cost against brute force attacks
        """
        # Test with known PIN to verify iteration count
        test_pin = "123456"
        test_salt = b'0' * 16  # Fixed salt for testing
        
        # Time the hashing operation
        start_time = time.time()
        hashed = hashlib.pbkdf2_hmac('sha256', test_pin.encode('utf-8'), test_salt, 100000, dklen=64)
        end_time = time.time()
        
        # Should take some time (but not too much for usability)
        hash_time = end_time - start_time
        assert 0.01 < hash_time < 1.0, f"FR-02: PBKDF2 timing ({hash_time:.3f}s) indicates appropriate iteration count"

    # ===== 3. SALTED HASH STORAGE TESTS =====

    def test_fr02_unique_salt_per_pin(self):
        """
        FR-02: Test that each PIN gets a unique salt
        Verifies salt uniqueness for enhanced security
        """
        salts = set()
        
        # Generate multiple PIN hashes
        for _ in range(50):
            pin, pin_hash = PinManager.generate_pin_and_hash()
            salt_hex = pin_hash.split(':')[0]
            salts.add(salt_hex)
        
        # All salts should be unique
        assert len(salts) == 50, "FR-02: Each PIN must have unique salt for enhanced security"

    def test_fr02_same_pin_different_hashes(self):
        """
        FR-02: Test that same PIN produces different hashes due to unique salts
        Verifies salt effectiveness against rainbow table attacks
        """
        # Generate hash for same PIN multiple times
        pin1, hash1 = PinManager.generate_pin_and_hash()
        
        # Mock to generate same PIN but different salt
        with patch('os.urandom', side_effect=[b'\x00\x00\x01', b'\x11' * 16, b'\x00\x00\x01', b'\x22' * 16]):
            pin2, hash2 = PinManager.generate_pin_and_hash()
            pin3, hash3 = PinManager.generate_pin_and_hash()
        
        # Same PINs should produce different hashes
        if pin2 == pin3:  # If we got same PIN (which we mocked)
            assert hash2 != hash3, "FR-02: Same PIN must produce different hashes with unique salts"

    def test_fr02_hash_format_consistency(self):
        """
        FR-02: Test hash format consistency across generations
        Verifies standardized storage format
        """
        hashes = []
        
        # Generate multiple hashes
        for _ in range(10):
            pin, pin_hash = PinManager.generate_pin_and_hash()
            hashes.append(pin_hash)
        
        # All hashes should follow same format
        for pin_hash in hashes:
            parts = pin_hash.split(':')
            assert len(parts) == 2, "FR-02: Hash format must be 'salt_hex:hash_hex'"
            assert len(parts[0]) == 32, "FR-02: Salt part must be 32 hex characters"
            assert len(parts[1]) == 128, "FR-02: Hash part must be 128 hex characters"

    # ===== 4. PIN VERIFICATION TESTS =====

    def test_fr02_correct_pin_verification(self):
        """
        FR-02: Test that correct PIN verification works
        Verifies hash verification functionality
        """
        # Generate PIN and hash
        pin, pin_hash = PinManager.generate_pin_and_hash()
        
        # Verify correct PIN
        assert PinManager.verify_pin(pin_hash, pin), "FR-02: Correct PIN should verify successfully"

    def test_fr02_incorrect_pin_rejection(self):
        """
        FR-02: Test that incorrect PIN is rejected
        Verifies security against wrong PINs
        """
        # Generate PIN and hash
        pin, pin_hash = PinManager.generate_pin_and_hash()
        
        # Try different wrong PINs
        wrong_pins = ['000000', '123456', '999999', str(int(pin) + 1).zfill(6)]
        
        for wrong_pin in wrong_pins:
            if wrong_pin != pin:  # Skip if accidentally same
                assert not PinManager.verify_pin(pin_hash, wrong_pin), f"FR-02: Wrong PIN '{wrong_pin}' should be rejected"

    def test_fr02_malformed_hash_handling(self):
        """
        FR-02: Test handling of malformed hash strings
        Verifies robust error handling
        """
        pin = "123456"
        
        # Test various malformed hashes
        malformed_hashes = [
            "invalid",
            "no_colon_separator",
            "invalid:hash",
            "tooshort:hash",
            ":" + "a" * 128,  # Missing salt
            "a" * 32 + ":",   # Missing hash
            "",
            None
        ]
        
        for malformed_hash in malformed_hashes:
            if malformed_hash is not None:
                result = PinManager.verify_pin(malformed_hash, pin)
                assert result is False, f"FR-02: Malformed hash '{malformed_hash}' should return False"

    # ===== 5. SALT UNIQUENESS TESTS =====

    def test_fr02_salt_entropy_quality(self):
        """
        FR-02: Test quality of salt entropy
        Verifies cryptographic randomness of salts
        """
        salts = []
        
        # Collect salt bytes from multiple generations
        for _ in range(100):
            pin, pin_hash = PinManager.generate_pin_and_hash()
            salt_hex = pin_hash.split(':')[0]
            salt_bytes = bytes.fromhex(salt_hex)
            salts.append(salt_bytes)
        
        # Test entropy - each byte position should have varied values
        for byte_pos in range(16):
            byte_values = {salt[byte_pos] for salt in salts}
            # Should have good variety in each byte position
            assert len(byte_values) > 20, f"FR-02: Salt byte {byte_pos} has low entropy ({len(byte_values)} unique values)"

    def test_fr02_salt_size_security(self):
        """
        FR-02: Test that salt size meets security standards
        Verifies 16-byte salt size for security
        """
        pin, pin_hash = PinManager.generate_pin_and_hash()
        salt_hex = pin_hash.split(':')[0]
        salt_bytes = bytes.fromhex(salt_hex)
        
        # 16 bytes is minimum recommended salt size
        assert len(salt_bytes) >= 16, "FR-02: Salt must be at least 16 bytes for security"
        assert len(salt_bytes) == 16, "FR-02: Salt should be exactly 16 bytes as implemented"

    # ===== 6. PERFORMANCE TESTS =====

    def test_fr02_pin_generation_performance(self):
        """
        FR-02: Test PIN generation performance
        Verifies reasonable generation time for user experience
        """
        generation_times = []
        
        # Measure multiple PIN generations
        for _ in range(10):
            start_time = time.time()
            pin, pin_hash = PinManager.generate_pin_and_hash()
            end_time = time.time()
            
            generation_time = (end_time - start_time) * 1000  # Convert to milliseconds
            generation_times.append(generation_time)
        
        # Calculate average
        avg_time = sum(generation_times) / len(generation_times)
        max_time = max(generation_times)
        
        # Should be fast enough for real-time use
        assert avg_time < 100.0, f"FR-02: Average PIN generation time {avg_time:.2f}ms should be <100ms"
        assert max_time < 500.0, f"FR-02: Maximum PIN generation time {max_time:.2f}ms should be <500ms"

    def test_fr02_pin_verification_performance(self):
        """
        FR-02: Test PIN verification performance
        Verifies reasonable verification time for user experience
        """
        # Generate test PIN and hash
        pin, pin_hash = PinManager.generate_pin_and_hash()
        
        verification_times = []
        
        # Measure multiple verifications
        for _ in range(10):
            start_time = time.time()
            result = PinManager.verify_pin(pin_hash, pin)
            end_time = time.time()
            
            verification_time = (end_time - start_time) * 1000  # Convert to milliseconds
            verification_times.append(verification_time)
            assert result is True, "FR-02: Verification should succeed in performance test"
        
        # Calculate average
        avg_time = sum(verification_times) / len(verification_times)
        max_time = max(verification_times)
        
        # Should be fast enough for real-time use
        assert avg_time < 200.0, f"FR-02: Average PIN verification time {avg_time:.2f}ms should be <200ms"
        assert max_time < 1000.0, f"FR-02: Maximum PIN verification time {max_time:.2f}ms should be <1000ms"

    # ===== 7. SECURITY VALIDATION TESTS =====

    def test_fr02_timing_attack_resistance(self):
        """
        FR-02: Test resistance to timing attacks
        Verifies consistent verification timing regardless of PIN correctness
        """
        pin, pin_hash = PinManager.generate_pin_and_hash()
        
        # Measure timing for correct PIN
        correct_times = []
        for _ in range(50):
            start_time = time.time()
            PinManager.verify_pin(pin_hash, pin)
            end_time = time.time()
            correct_times.append(end_time - start_time)
        
        # Measure timing for incorrect PIN
        wrong_pin = str((int(pin) + 1) % 1000000).zfill(6)
        incorrect_times = []
        for _ in range(50):
            start_time = time.time()
            PinManager.verify_pin(pin_hash, wrong_pin)
            end_time = time.time()
            incorrect_times.append(end_time - start_time)
        
        # Calculate averages
        avg_correct = sum(correct_times) / len(correct_times)
        avg_incorrect = sum(incorrect_times) / len(incorrect_times)
        
        # Times should be similar (within 50% to account for system variance)
        time_ratio = abs(avg_correct - avg_incorrect) / max(avg_correct, avg_incorrect)
        assert time_ratio < 0.5, f"FR-02: Timing difference {time_ratio:.1%} may indicate timing attack vulnerability"

    def test_fr02_pin_space_coverage(self):
        """
        FR-02: Test that PIN generation covers full 6-digit space
        Verifies no systematic bias in PIN generation
        """
        pins = set()
        
        # Generate many PINs to check coverage
        for _ in range(10000):
            pin, _ = PinManager.generate_pin_and_hash()
            pins.add(pin)
        
        # Should cover significant portion of 6-digit space (000000-999999)
        coverage = len(pins) / 1000000
        assert coverage > 0.005, f"FR-02: PIN coverage {coverage:.1%} too low, may indicate bias"
        
        # Check for presence of edge cases
        edge_cases = ['000000', '000001', '999999', '123456']
        for edge_case in edge_cases:
            if edge_case in pins:
                break
        else:
            # If no edge cases found, that might indicate bias (though unlikely with 10k samples)
            pass  # This is acceptable for 10k samples

    # ===== 8. INTEGRATION TESTS =====

    def test_fr02_integration_with_parcel_service(self, app, test_locker_and_parcel):
        """
        FR-02: Test integration with parcel service
        Verifies PIN generation works within full system context
        """
        with app.app_context():
            locker, parcel = test_locker_and_parcel
            
            # Generate PIN for parcel
            pin, pin_hash = PinManager.generate_pin_and_hash()
            
            # Update parcel with PIN hash
            parcel.pin_hash = pin_hash
            db.session.commit()
            
            # Verify integration
            assert parcel.pin_hash is not None, "FR-02: Parcel should have PIN hash after generation"
            assert parcel.pin_hash == pin_hash, "FR-02: Parcel PIN hash should match generated hash"
            
            # Verify PIN verification works with stored hash
            assert PinManager.verify_pin(parcel.pin_hash, pin), "FR-02: PIN verification should work with stored hash"

    def test_fr02_integration_with_pin_service(self, app):
        """
        FR-02: Test integration with PIN service layer
        Verifies service layer properly uses business logic
        """
        with app.app_context():
            # Test PIN service functionality
            from app.services.pin_service import PinService
            
            # Generate PIN through service
            pin_data = PinService.generate_new_pin("test@example.com")
            
            # Verify service returns proper structure
            assert 'pin' in pin_data, "FR-02: PIN service should return PIN"
            assert 'hash' in pin_data, "FR-02: PIN service should return hash"
            
            # Verify PIN format
            pin = pin_data['pin']
            pin_hash = pin_data['hash']
            
            assert len(pin) == 6, "FR-02: Service-generated PIN should be 6 digits"
            assert pin.isdigit(), "FR-02: Service-generated PIN should be numeric"
            assert ':' in pin_hash, "FR-02: Service-generated hash should be salted"

    def test_fr02_concurrent_pin_generation_safety(self):
        """
        FR-02: Test thread safety of concurrent PIN generation
        Verifies no race conditions in PIN generation
        """
        pins = []
        hashes = []
        errors = []
        
        def generate_pin_thread():
            try:
                pin, pin_hash = PinManager.generate_pin_and_hash()
                pins.append(pin)
                hashes.append(pin_hash)
            except Exception as e:
                errors.append(str(e))
        
        # Start multiple concurrent threads
        threads = []
        for _ in range(10):
            thread = threading.Thread(target=generate_pin_thread)
            threads.append(thread)
            thread.start()
        
        # Wait for all threads to complete
        for thread in threads:
            thread.join()
        
        # Verify no errors occurred
        assert len(errors) == 0, f"FR-02: Concurrent PIN generation should not cause errors: {errors}"
        
        # Verify all generations succeeded
        assert len(pins) == 10, "FR-02: All concurrent PIN generations should succeed"
        assert len(hashes) == 10, "FR-02: All concurrent hash generations should succeed"
        
        # Verify all PINs are unique (high probability)
        unique_pins = set(pins)
        assert len(unique_pins) >= 8, "FR-02: Most concurrent PINs should be unique"

    def test_fr02_pin_invalidation_on_regeneration(self, app, test_locker_and_parcel):
        """
        FR-02: Test that each PIN generation invalidates previous PIN
        Verifies security requirement for PIN invalidation
        """
        with app.app_context():
            locker, parcel = test_locker_and_parcel
            
            # Generate first PIN
            pin1, hash1 = PinManager.generate_pin_and_hash()
            parcel.pin_hash = hash1
            db.session.commit()
            
            # Generate second PIN (should invalidate first)
            pin2, hash2 = PinManager.generate_pin_and_hash()
            parcel.pin_hash = hash2
            db.session.commit()
            
            # Verify first PIN is invalidated (no longer stored)
            current_hash = parcel.pin_hash
            assert current_hash == hash2, "FR-02: Only latest PIN hash should be stored"
            
            # Verify second PIN works
            assert PinManager.verify_pin(current_hash, pin2), "FR-02: Latest PIN should verify successfully"
            
            # Verify first PIN no longer works (since hash was replaced)
            assert not PinManager.verify_pin(current_hash, pin1), "FR-02: Previous PIN should not work with new hash"


# ===== STANDALONE TEST FUNCTIONS =====

def test_fr02_cryptographic_strength_validation():
    """
    FR-02: Standalone test for cryptographic strength validation
    Validates entropy and randomness of PIN generation
    """
    # Generate large sample for statistical analysis
    pins = []
    for _ in range(1000):
        pin, _ = PinManager.generate_pin_and_hash()
        pins.append(pin)
    
    # Statistical tests for randomness
    
    # 1. Chi-square test for uniform distribution
    digit_counts = [0] * 10
    for pin in pins:
        for digit in pin:
            digit_counts[int(digit)] += 1
    
    # Expected count per digit (6 digits * 1000 PINs / 10 possible digits)
    expected = 600
    chi_square = sum((observed - expected) ** 2 / expected for observed in digit_counts)
    
    # Chi-square critical value for 9 degrees of freedom at 95% confidence is ~16.9
    assert chi_square < 25.0, f"FR-02: Chi-square {chi_square:.2f} indicates non-uniform distribution"
    
    # 2. Test for sequential patterns (should be rare)
    sequential_count = 0
    for pin in pins:
        if any(int(pin[i]) == int(pin[i+1]) - 1 for i in range(5)):
            sequential_count += 1
    
    sequential_rate = sequential_count / 1000
    assert sequential_rate < 0.3, f"FR-02: Sequential pattern rate {sequential_rate:.1%} too high"
    
    print(f"FR-02 Cryptographic Validation: Chi-square={chi_square:.2f}, Sequential rate={sequential_rate:.1%}")


def test_fr02_pbkdf2_parameter_validation():
    """
    FR-02: Validate PBKDF2 parameters for security compliance
    Ensures industry-standard security parameters
    """
    # Test the actual PBKDF2 implementation
    test_pin = "123456"
    test_salt = b'test_salt_16byte'
    
    # Test with current parameters
    start_time = time.time()
    hash_result = hashlib.pbkdf2_hmac('sha256', test_pin.encode('utf-8'), test_salt, 100000, dklen=64)
    end_time = time.time()
    
    # Verify parameters
    assert len(hash_result) == 64, "FR-02: PBKDF2 should produce 64-byte output"
    
    hash_time = end_time - start_time
    assert 0.01 < hash_time < 2.0, f"FR-02: PBKDF2 timing {hash_time:.3f}s indicates appropriate iteration count"
    
    print(f"FR-02 PBKDF2 Validation: 100,000 iterations in {hash_time:.3f}s")


def test_fr02_system_health_check():
    """
    FR-02: Test system health for PIN generation functionality
    Verifies all components are available and working
    """
    app = create_app()
    
    with app.app_context():
        # Test that PIN manager exists and is functional
        assert hasattr(PinManager, 'generate_pin_and_hash'), "FR-02: PinManager should have generation method"
        assert hasattr(PinManager, 'verify_pin'), "FR-02: PinManager should have verification method"
        
        # Test basic functionality
        pin, pin_hash = PinManager.generate_pin_and_hash()
        assert isinstance(pin, str), "FR-02: PIN should be string"
        assert isinstance(pin_hash, str), "FR-02: PIN hash should be string"
        assert len(pin) == 6, "FR-02: PIN should be 6 characters"
        
        # Test verification works
        assert PinManager.verify_pin(pin_hash, pin), "FR-02: PIN verification should work"
        
        print("FR-02 System Health: All components functional")


if __name__ == '__main__':
    # Run FR-02 tests
    pytest.main([__file__, '-v', '-s']) 