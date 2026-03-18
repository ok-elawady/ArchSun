import pytest

from archsun.core.locations import CITIES, find_nearest_city, haversine_distance


pytestmark = pytest.mark.unit


def test_haversine_distance_is_zero_for_identical_points():
    assert haversine_distance(10.0, 20.0, 10.0, 20.0) == pytest.approx(0.0)


def test_haversine_distance_is_symmetric():
    first = haversine_distance(40.7128, -74.0060, 34.0522, -118.2437)
    second = haversine_distance(34.0522, -118.2437, 40.7128, -74.0060)
    assert first == pytest.approx(second)


def test_find_nearest_city_returns_expected_city_for_nearby_coordinate():
    city = find_nearest_city(40.7130, -74.0062)
    assert city is not None
    assert city.name == "New York"


def test_find_nearest_city_returns_none_when_outside_threshold():
    assert find_nearest_city(0.0, -140.0, max_distance_km=100) is None


def test_find_nearest_city_respects_threshold_override():
    coordinate = (40.7306, -73.9352)
    assert find_nearest_city(*coordinate, max_distance_km=1) is None

    city = find_nearest_city(*coordinate, max_distance_km=20)
    assert city is not None
    assert city.name == "New York"


def test_city_names_do_not_embed_utc_offset_labels():
    assert all("UTC" not in city.name for city in CITIES)
