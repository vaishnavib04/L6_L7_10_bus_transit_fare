
import pytest

from bus_transit_fare import (
    process_commute_manifest,
    inspect_smartcard_turnstiles
)


# 1. Input validation branches

def test_invalid_manifest_type():
    with pytest.raises(ValueError):
        process_commute_manifest("invalid", 2.0)


def test_negative_booking_fee():
    with pytest.raises(ValueError):
        process_commute_manifest([], -1.0)


def test_valid_input():
    result = process_commute_manifest([], 2.0)
    assert result["status"] == "ZERO_RIDERSHIP"


# 2. Route activation and route type branches

def test_inactive_route():
    manifests = [
        {"route_active": False, "route_type": "local"}
    ]
    result = process_commute_manifest(manifests, 2.0)
    assert result["status"] == "ZERO_RIDERSHIP"


def test_unsupported_route():
    manifests = [
        {"route_active": True, "route_type": "premium"}
    ]
    result = process_commute_manifest(manifests, 2.0)

    assert result["status"] == "ZERO_RIDERSHIP"
    assert result["total_fare"] == 0.0


def test_express_route():
    manifests = [
        {
            "route_active": True,
            "route_type": "express",
            "commuters": [
                {"zones": 2, "type": "regular"}
            ]
        }
    ]
    result = process_commute_manifest(manifests, 2.0)
    assert result["total_fare"] == 8.0


def test_shuttle_route():
    manifests = [
        {
            "route_active": True,
            "route_type": "shuttle",
            "commuters": [
                {"zones": 2, "type": "regular"}
            ]
        }
    ]
    result = process_commute_manifest(manifests, 2.0)
    assert result["total_fare"] == 6.0


def test_local_route():
    manifests = [
        {
            "route_active": True,
            "route_type": "local",
            "commuters": [
                {"zones": 2, "type": "regular"}
            ]
        }
    ]
    result = process_commute_manifest(manifests, 2.0)
    assert result["total_fare"] == 4.5


def test_default_route_and_commuter_values():
    manifests = [
        {
            "route_active": True,
            "commuters": [{}]
        }
    ]
    result = process_commute_manifest(manifests, 2.0)
    assert result["total_fare"] == 3.5


# 3. Passenger and fare calculation branches

def test_student_passenger():
    manifests = [
        {
            "route_active": True,
            "route_type": "local",
            "commuters": [
                {"zones": 2, "type": "student"}
            ]
        }
    ]
    result = process_commute_manifest(manifests, 2.0)
    assert result["total_fare"] == 1.75


def test_senior_passenger():
    manifests = [
        {
            "route_active": True,
            "route_type": "local",
            "commuters": [
                {"zones": 2, "type": "senior"}
            ]
        }
    ]
    result = process_commute_manifest(manifests, 2.0)
    assert result["total_fare"] == 2.45


def test_invalid_zones():
    manifests = [
        {
            "route_active": True,
            "route_type": "local",
            "commuters": [
                {"zones": 0, "type": "regular"}
            ]
        }
    ]
    result = process_commute_manifest(manifests, 2.0)
    assert result["status"] == "ZERO_RIDERSHIP"


def test_blacklisted_non_express_passenger():
    manifests = [
        {
            "route_active": True,
            "route_type": "local",
            "commuters": [
                {"zones": 2, "blacklisted": True}
            ]
        }
    ]
    result = process_commute_manifest(manifests, 2.0)
    assert result["status"] == "ZERO_RIDERSHIP"


def test_blacklisted_express_passenger():
    manifests = [
        {
            "route_active": True,
            "route_type": "express",
            "commuters": [
                {"zones": 2, "type": "regular", "blacklisted": True},
                {"zones": 2, "type": "regular"}
            ]
        }
    ]
    result = process_commute_manifest(manifests, 2.0)
    assert result["status"] == "ZERO_RIDERSHIP"


def test_express_blacklisted_card_after_invalid_zones():
    manifests = [
        {
            "route_active": True,
            "route_type": "express",
            "commuters": [
                {"zones": 0},
                {"zones": 2, "blacklisted": True}
            ]
        }
    ]
    result = process_commute_manifest(manifests, 2.0)
    assert result["status"] == "ZERO_RIDERSHIP"


# 4. Priority boarding and audit branches

def test_priority_boarding_enabled():
    manifests = [
        {
            "route_active": True,
            "route_type": "local",
            "priority_boarding": True,
            "commuters": [
                {"zones": 2, "type": "regular"}
            ]
        }
    ]
    result = process_commute_manifest(manifests, 2.0)
    assert result["total_fare"] == 6.5


def test_priority_boarding_disabled():
    manifests = [
        {
            "route_active": True,
            "route_type": "local",
            "priority_boarding": False,
            "commuters": [
                {"zones": 2, "type": "regular"}
            ]
        }
    ]
    result = process_commute_manifest(manifests, 2.0)
    assert result["total_fare"] == 4.5


def test_audit_rejection_above_four_rejections():
    manifests = [
        {"route_active": True, "route_type": "unknown"}
        for _ in range(5)
    ]
    result = process_commute_manifest(manifests, 2.0)
    assert result["status"] == "AUDIT_REJECTED"


def test_audit_not_rejected_at_four_rejections():
    manifests = [
        {"route_active": True, "route_type": "unknown"}
        for _ in range(4)
    ]
    result = process_commute_manifest(manifests, 2.0)
    assert result["status"] == "ZERO_RIDERSHIP"


# 5. Turnstile inspection branches

def test_no_turnstile_data():
    assert inspect_smartcard_turnstiles([]) == "NO_DATA"


def test_empty_device_readings():
    assert inspect_smartcard_turnstiles([[]]) == "OPERATIONAL"


def test_turnstile_operational_with_low_failures():
    readings = [[1, 2, 3, 0]]
    assert inspect_smartcard_turnstiles(readings) == "OPERATIONAL"


def test_turnstile_jam_with_consecutive_failures():
    readings = [[4, 5]]
    assert inspect_smartcard_turnstiles(readings) == "TURNSTILE_JAM"


def test_turnstile_failure_streak_resets():
    readings = [[4, 2, 5, 1, 4, 4]]
    assert inspect_smartcard_turnstiles(readings) == "TURNSTILE_JAM"


def test_turnstile_single_failure_not_jammed():
    readings = [[4, 1, 2, 4]]
    assert inspect_smartcard_turnstiles(readings) == "OPERATIONAL"


def test_multiple_devices():
    readings = [
        [4, 1, 4],
        [1, 2, 3]
    ]
    assert inspect_smartcard_turnstiles(readings) == "OPERATIONAL"
