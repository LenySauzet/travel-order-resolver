from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel

from ...models.travel import TravelOrderResponse
from ...models.journey import JourneySearchResponse
from ...services.travel_service import TravelService
from ...services.station_matcher import StationMatcher
from ...services.navitia_service import NavitiaService

router = APIRouter()


class StationsListResponse(BaseModel):
    stations: list[dict]


def get_travel_service() -> TravelService:
    return TravelService.get_instance()


def get_station_matcher() -> StationMatcher:
    return StationMatcher.get_instance()


def get_navitia_service() -> NavitiaService:
    return NavitiaService.get_instance()

@router.get("/identify-travel-order", response_model=TravelOrderResponse)
async def identify_travel_order(
    text: str = Query(...),
    lat: float | None = Query(None),
    lon: float | None = Query(None),
    service: TravelService = Depends(get_travel_service),
) -> TravelOrderResponse:
    print("latlon", lat, lon)
    coords = (lat, lon) if lat is not None and lon is not None else None
    return service.identify_travel_order(text, coords)


@router.get("/stations", response_model=StationsListResponse)
async def get_stations(
    matcher: StationMatcher = Depends(get_station_matcher),
) -> StationsListResponse:
    entries = matcher.get_all_entries()
    return StationsListResponse(stations=[{"id": e["id"], "name": e["raw"]} for e in entries])


@router.get("/journeys", response_model=JourneySearchResponse)
async def search_journeys(
    departure_id: int = Query(..., description="ID de la station de départ"),
    destination_id: int = Query(..., description="ID de la station d'arrivée"),
    datetime_iso: str | None = Query(None, description="Date/heure ISO (ex: 2024-01-15T14:30:00)"),
    datetime_represents: str = Query("departure", description="'departure' ou 'arrival'"),
    service: NavitiaService = Depends(get_navitia_service),
) -> JourneySearchResponse:
    """
    Search for journeys between two stations via the Navitia API.
        
    Returns a list of journeys with the details of each section
    (walking, public transport, transfers).
    """
    return await service.search_journeys(
        departure_station_id=departure_id,
        destination_station_id=destination_id,
        datetime_iso=datetime_iso,
        datetime_represents=datetime_represents,
    )
