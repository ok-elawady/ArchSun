import math
from datetime import datetime

from archsun.core.models import Location, SunState


def calculate_sun_position(location: Location, dt: datetime) -> SunState:
    """
    Calculate solar azimuth and altitude using a simplified NOAA-based model.

    Returns azimuth (degrees from North, clockwise)
    and altitude (degrees above horizon).
    """

    # --- Convert inputs ---
    latitude = math.radians(location.latitude)
    longitude = location.longitude
    timezone_offset = location.timezone_offset

    # Day of year
    day_of_year = dt.timetuple().tm_yday

    # Fractional hour
    hour = dt.hour + dt.minute / 60 + dt.second / 3600

    # --- Fractional year (radians) ---
    gamma = 2.0 * math.pi / 365.0 * (day_of_year - 1 + (hour - 12) / 24.0)

    # --- Equation of time (minutes) ---
    eq_time = 229.18 * (
        0.000075
        + 0.001868 * math.cos(gamma)
        - 0.032077 * math.sin(gamma)
        - 0.014615 * math.cos(2 * gamma)
        - 0.040849 * math.sin(2 * gamma)
    )

    # --- Solar declination (radians) ---
    decl = (
        0.006918
        - 0.399912 * math.cos(gamma)
        + 0.070257 * math.sin(gamma)
        - 0.006758 * math.cos(2 * gamma)
        + 0.000907 * math.sin(2 * gamma)
        - 0.002697 * math.cos(3 * gamma)
        + 0.00148 * math.sin(3 * gamma)
    )

    # --- Time offset (minutes) ---
    time_offset = eq_time + 4.0 * longitude - 60.0 * timezone_offset

    # True solar time (minutes)
    tst = hour * 60.0 + time_offset

    # Hour angle (degrees → radians)
    hour_angle = math.radians((tst / 4.0) - 180.0)

    # --- Solar zenith angle ---
    cos_zenith = math.sin(latitude) * math.sin(decl) + math.cos(latitude) * math.cos(
        decl
    ) * math.cos(hour_angle)

    # Clamp for safety
    cos_zenith = max(min(cos_zenith, 1.0), -1.0)

    zenith = math.acos(cos_zenith)

    # Altitude
    altitude = 90.0 - math.degrees(zenith)

    # --- Azimuth calculation ---
    sin_azimuth = (
        -math.sin(hour_angle) * math.cos(decl) / math.sin(zenith)
        if math.sin(zenith) != 0
        else 0
    )

    cos_azimuth = (
        (math.sin(decl) - math.sin(latitude) * math.cos(zenith))
        / (math.cos(latitude) * math.sin(zenith))
        if math.sin(zenith) != 0
        else 0
    )

    azimuth = math.degrees(math.atan2(sin_azimuth, cos_azimuth))

    # Convert from math convention to compass bearing
    azimuth = (azimuth + 360.0) % 360.0

    return SunState(azimuth=azimuth, altitude=altitude, datetime=dt)
