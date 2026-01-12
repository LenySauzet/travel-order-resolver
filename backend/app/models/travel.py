from pydantic import BaseModel


class TravelOrderResponse(BaseModel):
    departure_id: int | None = None
    destination_id: int | None = None
    datetime_iso: str | None = None


class TravelServiceConfig(BaseModel):
    model_path: str = "base/models/travel-order-ner-model"
