from pydantic import BaseModel

class JourneyPlace(BaseModel):
    name: str
    coord: tuple[float, float] | None = None


class JourneySection(BaseModel):
    type: str
    mode: str | None = None
    from_place: JourneyPlace
    to_place: JourneyPlace
    departure_datetime: str
    arrival_datetime: str
    duration: int

    line_name: str | None = None
    line_code: str | None = None
    commercial_mode: str | None = None
    direction: str | None = None
    network: str | None = None


class Journey(BaseModel):
    departure_datetime: str
    arrival_datetime: str
    duration: int
    nb_transfers: int
    walking_duration: int
    co2_emission: float | None = None
    sections: list[JourneySection]


class JourneySearchRequest(BaseModel):
    departure_station_id: int
    destination_station_id: int
    datetime_iso: str | None = None
    datetime_represents: str = "departure"


class JourneySearchResponse(BaseModel):
    journeys: list[Journey]
    error: str | None = None
