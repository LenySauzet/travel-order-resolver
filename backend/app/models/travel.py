from pydantic import BaseModel


class TravelOrderRequest(BaseModel):
    """Request model for travel order identification."""
    text: str


class TravelEntity(BaseModel):
    """A single extracted entity from the travel order."""
    text: str
    label: str
    start: int
    end: int


class TravelOrderResponse(BaseModel):
    """Response model for travel order identification."""
    departure: str | None = None
    destination: str | None = None
    time: str | None = None
    entities: list[TravelEntity] = []


class TravelServiceConfig(BaseModel):
    """Configuration for the NER model."""
    model_path: str = "base/models/travel-order-ner-model"
