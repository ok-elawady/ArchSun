import math
from datetime import datetime, timedelta

from archsun.core.models import Location, SunState


def calculate_sun_position(location: Location, dt: datetime) -> SunState:
    """
    Calculate solar azimuth and altitude using a fuller NOAA-style model.

    Inputs are a local naive datetime plus a manual UTC offset,
    the calculation itself is performed in UTC and includes apparent solar
    position plus a standard atmospheric refraction correction.

    Returns:
    - azimuth in degrees from North, clockwise
    - altitude in degrees above the horizon
    """

    latitude_deg = float(location.latitude)
    longitude_deg = float(location.longitude)
    timezone_offset = float(location.timezone_offset)

    dt_utc = dt - timedelta(hours=timezone_offset)
    julian_day = _julian_day(dt_utc)
    julian_century = (julian_day - 2451545.0) / 36525.0

    geom_mean_long = _normalize_angle(
        280.46646 + julian_century * (36000.76983 + julian_century * 0.0003032)
    )
    geom_mean_anom = 357.52911 + julian_century * (
        35999.05029 - 0.0001537 * julian_century
    )
    eccentricity = 0.016708634 - julian_century * (
        0.000042037 + 0.0000001267 * julian_century
    )

    sun_eq_center = (
        math.sin(math.radians(geom_mean_anom))
        * (1.914602 - julian_century * (0.004817 + 0.000014 * julian_century))
        + math.sin(math.radians(2.0 * geom_mean_anom))
        * (0.019993 - 0.000101 * julian_century)
        + math.sin(math.radians(3.0 * geom_mean_anom)) * 0.000289
    )

    sun_true_long = geom_mean_long + sun_eq_center
    omega = 125.04 - 1934.136 * julian_century
    sun_app_long = sun_true_long - 0.00569 - 0.00478 * math.sin(math.radians(omega))

    mean_obliq = (
        23.0
        + (
            26.0
            + (
                21.448
                - julian_century
                * (46.815 + julian_century * (0.00059 - julian_century * 0.001813))
            )
            / 60.0
        )
        / 60.0
    )
    obliq_corr = mean_obliq + 0.00256 * math.cos(math.radians(omega))

    declination = math.degrees(
        math.asin(
            math.sin(math.radians(obliq_corr)) * math.sin(math.radians(sun_app_long))
        )
    )

    var_y = math.tan(math.radians(obliq_corr / 2.0)) ** 2
    equation_of_time = 4.0 * math.degrees(
        var_y * math.sin(2.0 * math.radians(geom_mean_long))
        - 2.0 * eccentricity * math.sin(math.radians(geom_mean_anom))
        + 4.0
        * eccentricity
        * var_y
        * math.sin(math.radians(geom_mean_anom))
        * math.cos(2.0 * math.radians(geom_mean_long))
        - 0.5 * var_y * var_y * math.sin(4.0 * math.radians(geom_mean_long))
        - 1.25
        * eccentricity
        * eccentricity
        * math.sin(2.0 * math.radians(geom_mean_anom))
    )

    local_minutes = dt.hour * 60.0 + dt.minute + dt.second / 60.0
    true_solar_time = (
        local_minutes
        + equation_of_time
        + (4.0 * longitude_deg)
        - 60.0 * timezone_offset
    ) % 1440.0

    hour_angle_deg = true_solar_time / 4.0 - 180.0
    if hour_angle_deg < -180.0:
        hour_angle_deg += 360.0

    latitude_rad = math.radians(latitude_deg)
    declination_rad = math.radians(declination)
    hour_angle_rad = math.radians(hour_angle_deg)

    cos_zenith = math.sin(latitude_rad) * math.sin(declination_rad) + math.cos(
        latitude_rad
    ) * math.cos(declination_rad) * math.cos(hour_angle_rad)
    cos_zenith = max(min(cos_zenith, 1.0), -1.0)

    zenith_deg = math.degrees(math.acos(cos_zenith))
    elevation_deg = 90.0 - zenith_deg
    altitude_deg = elevation_deg + _refraction_correction_degrees(elevation_deg)

    azimuth_deg = _solar_azimuth_degrees(
        latitude_rad=latitude_rad,
        declination_rad=declination_rad,
        zenith_deg=zenith_deg,
        hour_angle_deg=hour_angle_deg,
    )

    return SunState(azimuth=azimuth_deg, altitude=altitude_deg, datetime=dt)


def _julian_day(dt_utc: datetime) -> float:
    year = dt_utc.year
    month = dt_utc.month
    day = dt_utc.day

    if month <= 2:
        year -= 1
        month += 12

    a = year // 100
    b = 2 - a + (a // 4)
    day_fraction = (
        dt_utc.hour
        + dt_utc.minute / 60.0
        + dt_utc.second / 3600.0
        + dt_utc.microsecond / 3_600_000_000.0
    ) / 24.0

    return (
        math.floor(365.25 * (year + 4716))
        + math.floor(30.6001 * (month + 1))
        + day
        + day_fraction
        + b
        - 1524.5
    )


def _solar_azimuth_degrees(
    latitude_rad: float,
    declination_rad: float,
    zenith_deg: float,
    hour_angle_deg: float,
) -> float:
    zenith_rad = math.radians(zenith_deg)
    azimuth_denom = math.cos(latitude_rad) * math.sin(zenith_rad)

    if abs(azimuth_denom) <= 1e-12:
        return 180.0 if latitude_rad >= 0.0 else 0.0

    azimuth_cos = (
        (math.sin(latitude_rad) * math.cos(zenith_rad)) - math.sin(declination_rad)
    ) / azimuth_denom
    azimuth_cos = max(min(azimuth_cos, 1.0), -1.0)
    azimuth = math.degrees(math.acos(azimuth_cos))

    if hour_angle_deg > 0.0:
        return (azimuth + 180.0) % 360.0
    return (540.0 - azimuth) % 360.0


def _refraction_correction_degrees(elevation_deg: float) -> float:
    if elevation_deg > 85.0:
        return 0.0

    tan_elevation = math.tan(math.radians(elevation_deg))

    if elevation_deg > 5.0:
        correction_arcseconds = (
            58.1 / tan_elevation
            - 0.07 / (tan_elevation**3)
            + 0.000086 / (tan_elevation**5)
        )
        return correction_arcseconds / 3600.0

    if elevation_deg > -0.575:
        correction_arcseconds = 1735.0 + elevation_deg * (
            -518.2
            + elevation_deg * (103.4 + elevation_deg * (-12.79 + elevation_deg * 0.711))
        )
        return correction_arcseconds / 3600.0

    correction_arcseconds = -20.774 / tan_elevation
    return correction_arcseconds / 3600.0


def _normalize_angle(angle_degrees: float) -> float:
    return angle_degrees % 360.0
