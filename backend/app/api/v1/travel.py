from fastapi import APIRouter, Depends, Query

from ...models.travel import TravelOrderResponse
from ...services.travel_service import TravelService

router = APIRouter()


def get_travel_service() -> TravelService:
    """Dependency injection for travel service."""
    return TravelService.get_instance()


@router.get("/identify-travel-order", response_model=TravelOrderResponse)
async def identify_travel_order(
    text: str = Query(..., description="The travel order text to analyze"),
    service: TravelService = Depends(get_travel_service),
) -> TravelOrderResponse:
    """
    Identify travel order entities from text using NER.
    
    Extracts:
    - DEPARTURE: The departure location
    - DESTINATION: The destination location
    - TIME: The travel time/date
    """
    return service.identify_travel_order(text)
