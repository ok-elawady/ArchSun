import math
from datetime import datetime

import pytest

from archsun.core.models import Location
from archsun.core.solar import calculate_sun_position


pytestmark = pytest.mark.unit


NEW_YORK = Location(latitude=40.7128, longitude=-74.0060, timezone_offset=-5.0)


def test_calculate_sun_position_returns_finite_values_in_expected_range():
    state = calculate_sun_position(NEW_YORK, datetime(2026, 6, 21, 12, 0, 0))
    assert 0.0 <= state.azimuth < 360.0
    assert math.isfinite(state.azimuth)
    assert math.isfinite(state.altitude)


def test_noon_altitude_is_higher_than_morning_altitude():
    morning = calculate_sun_position(NEW_YORK, datetime(2026, 6, 21, 9, 0, 0))
    noon = calculate_sun_position(NEW_YORK, datetime(2026, 6, 21, 12, 0, 0))
    assert noon.altitude > morning.altitude


def test_midnight_altitude_is_lower_than_daytime_altitude():
    midnight = calculate_sun_position(NEW_YORK, datetime(2026, 6, 21, 0, 0, 0))
    daytime = calculate_sun_position(NEW_YORK, datetime(2026, 6, 21, 12, 0, 0))
    assert midnight.altitude < daytime.altitude


def test_summer_noon_altitude_is_higher_than_winter_noon_altitude():
    summer = calculate_sun_position(NEW_YORK, datetime(2026, 6, 21, 12, 0, 0))
    winter = calculate_sun_position(NEW_YORK, datetime(2026, 12, 21, 12, 0, 0))
    assert summer.altitude > winter.altitude


def test_calculate_sun_position_stays_finite_near_poles():
    polar_location = Location(latitude=89.9, longitude=0.0, timezone_offset=0.0)
    state = calculate_sun_position(polar_location, datetime(2026, 6, 21, 12, 0, 0))
    assert math.isfinite(state.azimuth)
    assert math.isfinite(state.altitude)

