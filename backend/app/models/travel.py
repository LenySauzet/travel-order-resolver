from pydantic import BaseModel


class TravelOrderResponse(BaseModel):
    departure_id: int | None = None
    destination_id: int | None = None
    datetime_iso: str | None = None


class TravelServiceConfig(BaseModel):
    model_path: str = "base/models/travel-order-ner-model"


class RouteStep(BaseModel):
    id: int
    name: str
    lat: float | None = None
    lon: float | None = None


class RouteOption(BaseModel):
    duration_minutes: float
    path: list[RouteStep]


class BestRoutesResponse(BaseModel):
    routes: list[RouteOption]
    error: str | None = None


class RoutingModeResponse(BaseModel):
    mode: str
    options: list[str]


class ShortestPathResponse(BaseModel):
    duration_minutes: float
    path: list[dict]

