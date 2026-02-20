"""Travel order models."""

from pydantic import BaseModel


class TravelOrderResponse(BaseModel):
    """Travel order identification response."""

    departure_id: int | None = None
    destination_id: int | None = None
    datetime_iso: str | None = None


class RouteStep(BaseModel):
    """Route step."""

    id: int
    name: str
    lat: float | None = None
    lon: float | None = None


class RouteOption(BaseModel):
    """Dijkstra route option."""

    duration_minutes: float
    path: list[RouteStep]


class BestRoutesResponse(BaseModel):
    """Best routes response."""

    routes: list[RouteOption] = []
    error: str | None = None


class RoutingModeResponse(BaseModel):
    """Routing mode response."""

    mode: str
    options: list[str]


class ShortestPathResponse(BaseModel):
    """Shortest path response."""

    duration_minutes: float
    path: list[dict]

