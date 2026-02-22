from fastapi import APIRouter, Depends, HTTPException, Query

from ...models.neo4j import Neo4jFastestPathResponse, Neo4jFewestStopsResponse
from ...services.neo4j_service import Neo4jService

router = APIRouter()


def get_neo4j_service() -> Neo4jService:
    return Neo4jService.get_instance()


@router.get("/neo4j/fastest-path", response_model=Neo4jFastestPathResponse)
async def neo4j_fastest_path(
    from_stop: str = Query(..., description="Departure station name"),
    to_stop: str = Query(..., description="Arrival station name"),
    depart_after: str = Query("08:00:00", description="Earliest departure (HH:MM:SS)"),
    service: Neo4jService = Depends(get_neo4j_service),
):
    result = service.fastest_path(from_stop, to_stop, depart_after)
    if result is None:
        raise HTTPException(status_code=404, detail="No path found")
    return Neo4jFastestPathResponse(
        duration_minutes=result["totalCost"],
        nb_steps=result["nb_steps"],
        stations=result["stations"],
        trips=result["trips"],
    )


@router.get("/neo4j/fewest-stops", response_model=Neo4jFewestStopsResponse)
async def neo4j_fewest_stops(
    from_stop: str = Query(..., description="Departure station name"),
    to_stop: str = Query(..., description="Arrival station name"),
    depart_after: str = Query("08:00:00", description="Earliest departure (HH:MM:SS)"),
    service: Neo4jService = Depends(get_neo4j_service),
):
    routes = service.fewest_stops(from_stop, to_stop, depart_after)
    if not routes:
        raise HTTPException(status_code=404, detail="No path found")
    return Neo4jFewestStopsResponse(routes=routes)
