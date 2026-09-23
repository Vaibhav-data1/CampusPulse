from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator


class ObservationCreate(BaseModel):
    location: str = Field(..., min_length=1, max_length=200)
    category: str = Field(..., min_length=1, max_length=100)
    severity: int = Field(..., ge=1, le=5)
    description: str = Field(..., min_length=1, max_length=2000)

    @field_validator("location", "category", "description")
    @classmethod
    def strip_text(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("must not be blank")
        return value


class Observation(ObservationCreate):
    model_config = ConfigDict(from_attributes=True)

    id: int
    created_at: datetime
