from datetime import datetime

import pytest

import archsun.core.daylight_service as daylight_service_module
from archsun.core.models import Location, SunState


pytestmark = pytest.mark.unit


def test_daylight_service_delegates_to_calculate_sun_position(monkeypatch):
    location = Location(latitude=30.0, longitude=31.0, timezone_offset=2.0)
    dt = datetime(2026, 6, 21, 12, 0, 0)
    expected_state = SunState(azimuth=180.0, altitude=70.0, datetime=dt)
    captured = {}

    def fake_calculate_sun_position(received_location, received_dt):
        captured["location"] = received_location
        captured["dt"] = received_dt
        return expected_state

    monkeypatch.setattr(
        daylight_service_module, "calculate_sun_position", fake_calculate_sun_position
    )

    service = daylight_service_module.DaylightService()
    result = service.get_sun_state(location, dt)

    assert result is expected_state
    assert captured["location"] == location
    assert captured["dt"] == dt

