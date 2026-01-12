"""Journey models."""

from pydantic import BaseModel


class JourneyPlace(BaseModel):
    """A departure or arrival location."""

    name: str
    coord: tuple[float, float] | None = None


class JourneySection(BaseModel):
    """A section of a journey."""

    type: str
    mode: str | None = None
    from_place: JourneyPlace
    to_place: JourneyPlace
    departure_datetime: str = ""
    arrival_datetime: str = ""
    duration: int = 0
    line_name: str | None = None
    line_code: str | None = None
    commercial_mode: str | None = None
    direction: str | None = None
    network: str | None = None


class Journey(BaseModel):
    """A complete journey."""

    departure_datetime: str = ""
    arrival_datetime: str = ""
    duration: int = 0
    nb_transfers: int = 0
    walking_duration: int = 0
    co2_emission: float | None = None
    sections: list[JourneySection] = []


class JourneySearchResponse(BaseModel):
    """Journey search response."""

    journeys: list[Journey] = []
    error: str | None = None
