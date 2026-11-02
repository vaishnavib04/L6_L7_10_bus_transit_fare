
import pytest

from bus_transit_fare import (
    process_commute_manifest,
    inspect_smartcard_turnstiles
)


def test_invalid_manifests():
    with pytest.raises(ValueError):
        process_commute_manifest("invalid", 2.0)


def test_negative_booking_fee():
    with pytest.raises(ValueError):
        process_commute_manifest([], -1.0)


def test_all_routes_and_passenger_types():
    manifests = [
        # Inactive route
        {
            "route_active": False,
            "route_type": "local",
            "commuters": []
        },

        # Unsupported route
        {
            "route_active": True,
            "route_type": "premium",
            "commuters": []
        },

        # Express route: invalid zones and blacklisted card
        {
            "route_active": True,
            "route_type": "express",
            "priority_boarding": True,
            "commuters": [
                {"zones": 0, "type": "regular"},
                {"zones": 2, "type": "regular", "blacklisted": True}
            ]
        },

        # Shuttle route: blacklisted, student, senior and regular
        {
            "route_active": True,
            "route_type": "shuttle",
            "commuters": [
                {"zones": 2, "type": "regular", "blacklisted": True},
                {"zones": 1, "type": "student"},
                {"zones": 2, "type": "senior"},
                {"zones": 1, "type": "regular"}
            ]
        },

        # Local route using default route and commuter values
        {
            "route_active": True,
            "priority_boarding": True,
            "commuters": [{}]
        },

        # Active route with no commuters
        {
            "route_active": True,
            "route_type": "local",
            "commuters": []
        }
    ]

    result = process_commute_manifest(manifests, 2.0)

    assert result["status"] == "COMPLETED"
    assert result["total_fare"] > 0


def test_zero_ridership():
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

    assert result["total_fare"] == 0.0
    assert result["status"] == "ZERO_RIDERSHIP"


def test_audit_rejection():
    manifests = [
        {"route_active": True, "route_type": "unknown"}
        for _ in range(5)
    ]

    result = process_commute_manifest(manifests, 2.0)

    assert result["status"] == "AUDIT_REJECTED"


def test_empty_commute_manifest():
    result = process_commute_manifest([], 2.0)

    assert result["total_fare"] == 0.0
    assert result["status"] == "ZERO_RIDERSHIP"


def test_empty_turnstile_data():
    assert inspect_smartcard_turnstiles([]) == "NO_DATA"


def test_operational_turnstiles():
    readings = [
        [4, 2, 4],
        [1, 2, 3]
    ]

    assert inspect_smartcard_turnstiles(readings) == "OPERATIONAL"


def test_jammed_turnstile():
    readings = [
        [1, 4, 5, 2]
    ]

    assert inspect_smartcard_turnstiles(readings) == "TURNSTILE_JAM"
