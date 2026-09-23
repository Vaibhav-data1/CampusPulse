from datetime import datetime
from enum import Enum

from pydantic import BaseModel, ConfigDict, Field, field_validator

from .config import CATEGORIES, get_locations


class Category(str, Enum):
    WIFI_CONNECTIVITY = "Wi-Fi / Connectivity"
    CROWDING = "Crowding"
    CLEANLINESS = "Cleanliness"
    NOISE = "Noise"
    MAINTENANCE = "Maintenance"
    SAFETY = "Safety"
    FACILITIES = "Facilities"
    OTHER = "Other"


class ObservationCreate(BaseModel):
    location: str = Field(..., min_length=1, max_length=200)
    category: Category
    severity: int = Field(..., ge=1, le=5)
    description: str = Field(..., min_length=1, max_length=2000)
    observed_at: datetime | None = None
    approximate_location_id: str | None = Field(default=None, min_length=1, max_length=100)
    crowd_level: int | None = Field(default=None, ge=1, le=5)
    environmental_rating: int | None = Field(default=None, ge=1, le=5)

    @field_validator("location", "description", "approximate_location_id")
    @classmethod
    def strip_text(cls, value: str | None) -> str | None:
        if value is None:
            return value
        value = value.strip()
        if not value:
            raise ValueError("must not be blank")
        return value

    @field_validator("location")
    @classmethod
    def validate_location(cls, value: str) -> str:
        if value not in get_locations():
            raise ValueError("location is not an available controlled location")
        return value


class Observation(ObservationCreate):
    model_config = ConfigDict(from_attributes=True)

    id: int
    created_at: datetime


class ObservationMetadata(BaseModel):
    categories: list[str]
    locations: list[str]
