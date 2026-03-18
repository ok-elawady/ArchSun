from datetime import datetime
from archsun.core.models import Location
from archsun.core.solar import calculate_sun_position


class DaylightService:

    def get_sun_state(self, location: Location, dt: datetime):
        return calculate_sun_position(location, dt)
