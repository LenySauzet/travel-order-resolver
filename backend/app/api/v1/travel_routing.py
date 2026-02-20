from fastapi import APIRouter, Depends, HTTPException, Query

from ...models.travel import BestRoutesResponse, RoutingModeResponse, ShortestPathResponse
from ...services.routing_service import RoutingService
from ...services.station_matcher import StationMatcher

router = APIRouter()


def get_station_matcher() -> StationMatcher:
    return StationMatcher.get_instance()


def get_routing_service() -> RoutingService:
    return RoutingService.get_instance()


@router.get("/shortest-path", response_model=ShortestPathResponse)
async def compute_shortest_path(
    start_id: int = Query(..., description="ID de la station de départ"),
    end_id: int = Query(..., description="ID de la station d'arrivée"),
    routing_service: RoutingService = Depends(get_routing_service),
    matcher: StationMatcher = Depends(get_station_matcher),
) -> ShortestPathResponse:
    duration, path_ids = routing_service.compute_shortest_path(start_id, end_id)
    if duration == float("inf"):
        return ShortestPathResponse(duration_minutes=-1.0, path=[])
    path_details = []
    for station_id in path_ids:
        match = matcher.get_by_id(station_id)
        path_details.append(
            {
                "id": station_id,
                "name": match.raw if match else f"Unknown Station ({station_id})",
            }
        )
    return ShortestPathResponse(duration_minutes=duration, path=path_details)


@router.get("/best-routes", response_model=BestRoutesResponse)
async def compute_best_routes(
    start_id: int = Query(..., description="ID de la station de départ"),
    end_id: int = Query(..., description="ID de la station d'arrivée"),
    limit: int = Query(5, ge=1, le=10),
    routing_service: RoutingService = Depends(get_routing_service),
    matcher: StationMatcher = Depends(get_station_matcher),
) -> BestRoutesResponse:
    routes = routing_service.compute_best_routes(start_id, end_id, k=limit)
    if not routes:
        return BestRoutesResponse(routes=[], error="Aucun chemin trouvé")
    route_options = []
    for duration, path_ids in routes:
        route_steps = []
        for station_id in path_ids:
            match = matcher.get_by_id(station_id)
            route_steps.append(
                {
                    "id": station_id,
                    "name": match.raw if match else f"Unknown Station ({station_id})",
                    "lat": match.lat if match else None,
                    "lon": match.lon if match else None,
                }
            )
        route_options.append({"duration_minutes": duration, "path": route_steps})
    return BestRoutesResponse(routes=route_options)


@router.get("/routing-mode", response_model=RoutingModeResponse)
async def get_routing_mode(
    routing_service: RoutingService = Depends(get_routing_service),
) -> RoutingModeResponse:
    return RoutingModeResponse(
        mode=routing_service.get_mode(),
        options=routing_service.get_modes(),
    )


@router.post("/routing-mode", response_model=RoutingModeResponse)
async def set_routing_mode(
    mode: str = Query(..., description="shortcuts or no_shortcuts"),
    routing_service: RoutingService = Depends(get_routing_service),
) -> RoutingModeResponse:
    if not routing_service.set_mode(mode):
        raise HTTPException(status_code=400, detail="Invalid routing mode")
    return RoutingModeResponse(
        mode=routing_service.get_mode(),
        options=routing_service.get_modes(),
    )
