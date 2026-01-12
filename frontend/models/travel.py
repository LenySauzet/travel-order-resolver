"""Travel order models."""

from pydantic import BaseModel


class TravelOrderResponse(BaseModel):
    """Travel order identification response."""

    departure_id: int | None = None
    destination_id: int | None = None
    datetime_iso: str | None = None
