import math
from dataclasses import dataclass


@dataclass
class City:
    name: str
    latitude: float
    longitude: float
    utc_offset: float


CITIES = sorted(
[
    City("Pago Pago", -14.2756, -170.7020, -11),
    City("Honolulu", 21.3069, -157.8583, -10),
    City("Anchorage", 61.2181, -149.9003, -9),
    City("Los Angeles", 34.0522, -118.2437, -8),
    City("Denver", 39.7392, -104.9903, -7),
    City("Chicago", 41.8781, -87.6298, -6),
    City("Mexico City", 19.4326, -99.1332, -6),
    City("Bogota", 4.7110, -74.0721, -5),
    City("Lima", -12.0464, -77.0428, -5),
    City("New York", 40.7128, -74.0060, -5),
    City("Toronto", 43.6532, -79.3832, -5),
    City("Caracas", 10.4806, -66.9036, -4),
    City("Santiago", -33.4489, -70.6693, -4),
    City("Buenos Aires", -34.6037, -58.3816, -3),
    City("Rio de Janeiro", -22.9068, -43.1729, -3),
    City("Sao Paulo", -23.5505, -46.6333, -3),
    City("Praia", 14.9330, -23.5133, -1),
    City("Dublin", 53.3498, -6.2603, 0),
    City("Lisbon", 38.7223, -9.1393, 0),
    City("London", 51.5074, -0.1278, 0),
    City("Berlin", 52.5200, 13.4050, 1),
    City("Madrid", 40.4168, -3.7038, 1),
    City("Paris", 48.8566, 2.3522, 1),
    City("Rome", 41.9028, 12.4964, 1),
    City("Athens", 37.9838, 23.7275, 2),
    City("Cairo", 30.0444, 31.2357, 2),
    City("Johannesburg", -26.2041, 28.0473, 2),
    City("Istanbul", 41.0082, 28.9784, 3),
    City("Moscow", 55.7558, 37.6173, 3),
    City("Nairobi", -1.2921, 36.8219, 3),
    City("Riyadh", 24.7136, 46.6753, 3),
    City("Tehran", 35.6892, 51.3890, 3.5),
    City("Baku", 40.4093, 49.8671, 4),
    City("Dubai", 25.2048, 55.2708, 4),
    City("Kabul", 34.5553, 69.2075, 4.5),
    City("Karachi", 24.8607, 67.0011, 5),
    City("Tashkent", 41.2995, 69.2401, 5),
    City("Colombo", 6.9271, 79.8612, 5.5),
    City("Mumbai", 19.0760, 72.8777, 5.5),
    City("New Delhi", 28.6139, 77.2090, 5.5),
    City("Kathmandu", 27.7172, 85.3240, 5.75),
    City("Almaty", 43.2220, 76.8512, 6),
    City("Dhaka", 23.8103, 90.4125, 6),
    City("Yangon", 16.8409, 96.1735, 6.5),
    City("Bangkok", 13.7563, 100.5018, 7),
    City("Jakarta", -6.2088, 106.8456, 7),
    City("Beijing", 39.9042, 116.4074, 8),
    City("Hong Kong", 22.3193, 114.1694, 8),
    City("Perth", -31.9523, 115.8613, 8),
    City("Shanghai", 31.2304, 121.4737, 8),
    City("Singapore", 1.3521, 103.8198, 8),
    City("Seoul", 37.5665, 126.9780, 9),
    City("Tokyo", 35.6895, 139.6917, 9),
    City("Adelaide", -34.9285, 138.6007, 9.5),
    City("Darwin", -12.4634, 130.8456, 9.5),
    City("Brisbane", -27.4698, 153.0251, 10),
    City("Sydney", -33.8688, 151.2093, 10),
    City("Noumea", -22.2758, 166.4580, 11),
    City("Auckland", -36.8485, 174.7633, 12),
    City("Wellington", -41.2865, 174.7762, 12),
    City("Nuku'alofa", -21.1394, -175.2042, 13),
    City("Kiritimati", 1.8721, -157.4278, 14),
],
key=lambda city: city.name.lower(),
)


def haversine_distance(lat1, lon1, lat2, lon2):
    """
    Distance between two lat/lon points in kilometers.
    """

    R = 6371.0  # Earth radius in km

    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)

    a = (
        math.sin(dphi / 2.0) ** 2
        + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2.0) ** 2
    )

    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

    return R * c


def find_nearest_city(lat, lon, max_distance_km=300):
    """
    Returns nearest City object if within threshold distance.
    Otherwise, returns None.
    """

    nearest = None
    min_dist = float("inf")

    for city in CITIES:
        dist = haversine_distance(lat, lon, city.latitude, city.longitude)
        if dist < min_dist:
            min_dist = dist
            nearest = city

    if min_dist <= max_distance_km:
        return nearest

    return None
