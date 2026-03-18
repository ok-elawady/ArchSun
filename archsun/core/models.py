from dataclasses import dataclass
from datetime import datetime


@dataclass
class Location:
    latitude: float
    longitude: float
    timezone_offset: float


@dataclass
class SunState:
    azimuth: float
    altitude: float
    datetime: datetime


@dataclass
class AppliedLightingState:
    final_azimuth: float
    altitude: float
    final_intensity: float
