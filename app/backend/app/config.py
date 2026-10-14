import os

CATEGORIES = (
    "Wi-Fi / Connectivity",
    "Crowding",
    "Cleanliness",
    "Noise",
    "Maintenance",
    "Safety",
    "Facilities",
    "Other",
)

DEFAULT_LOCATIONS = (
    "Library",
    "Cafeteria",
    "Main Gate",
    "Academic Block",
    "Laboratory",
    "Sports Ground",
    "Hostel",
    "Auditorium",
    "Other",
)


def get_locations() -> tuple[str, ...]:
    """Return configured controlled locations, with safe defaults."""
    configured = os.getenv("CAMPUSPULSE_LOCATIONS")
    if not configured:
        return DEFAULT_LOCATIONS
    locations = tuple(item.strip() for item in configured.split(",") if item.strip())
    return locations or DEFAULT_LOCATIONS


def get_cors_origins() -> list[str]:
    """Return explicitly configured browser origins plus local development defaults."""
    configured = os.getenv("CAMPUSPULSE_CORS_ORIGINS", "")
    origins = [item.strip().rstrip("/") for item in configured.split(",") if item.strip()]
    local_origins = ["http://localhost:5173", "http://127.0.0.1:5173"]
    return list(dict.fromkeys(local_origins + origins))
