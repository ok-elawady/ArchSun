import pytest

from archsun.core.models import AppliedLightingState
from archsun.ui import status_text


pytestmark = pytest.mark.unit


def test_initial_message_matches_expected_text():
    assert (
        status_text.initial_message()
        == "Press Update Lighting to create the ArchSun rig."
    )


def test_dirty_message_matches_expected_text():
    assert status_text.dirty_message() == "Settings changed.\nClick Update Lighting to apply."


def test_build_applied_message_uses_added_and_updated_prefixes():
    applied_state = AppliedLightingState(
        final_azimuth=135.0,
        altitude=10.0,
        final_intensity=2.0,
    )

    added = status_text.build_applied_message(True, applied_state)
    updated = status_text.build_applied_message(False, applied_state)

    assert added.startswith("ArchSun rig added.\n")
    assert updated.startswith("ArchSun rig updated.\n")


@pytest.mark.parametrize(
    ("azimuth", "expected"),
    [
        (0.0, "north"),
        (22.4, "north"),
        (22.5, "north-east"),
        (67.4, "north-east"),
        (67.5, "east"),
        (337.5, "north"),
    ],
)
def test_direction_bucket_boundaries(azimuth, expected):
    assert status_text._direction_name(azimuth) == expected


@pytest.mark.parametrize(
    ("intensity", "expected"),
    [
        (0.74, "dim"),
        (0.75, "soft"),
        (1.49, "soft"),
        (1.50, "bright"),
        (2.99, "bright"),
        (3.00, "very bright"),
    ],
)
def test_brightness_bucket_boundaries(intensity, expected):
    assert status_text._brightness_name(intensity) == expected


@pytest.mark.parametrize(
    ("altitude", "warmth", "height"),
    [
        (-1.0, "", "twilight"),
        (0.0, "warm", "low sun"),
        (9.9, "warm", "low sun"),
        (10.0, "soft", "low sun"),
        (24.9, "soft", "daylight"),
        (25.0, "clear", "daylight"),
        (45.0, "clear", "high sun"),
    ],
)
def test_warmth_and_height_wording_changes_at_thresholds(altitude, warmth, height):
    assert status_text._warmth_name(altitude) == warmth
    assert status_text._height_name(altitude) == height


def test_twilight_summary_omits_warmth_wording():
    applied_state = AppliedLightingState(
        final_azimuth=270.0,
        altitude=-5.0,
        final_intensity=0.2,
    )
    assert status_text.build_status_summary(applied_state) == "Dim twilight from the west"


def test_night_summary_replaces_twilight_when_sun_is_well_below_horizon():
    applied_state = AppliedLightingState(
        final_azimuth=270.0,
        altitude=-12.0,
        final_intensity=0.2,
    )
    assert status_text.build_status_summary(applied_state) == "Dim night from the west"


def test_daylight_summary_includes_brightness_warmth_and_height():
    applied_state = AppliedLightingState(
        final_azimuth=180.0,
        altitude=5.0,
        final_intensity=2.0,
    )
    assert (
        status_text.build_status_summary(applied_state)
        == "Bright warm low sun from the south"
    )
