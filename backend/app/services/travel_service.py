import spacy
from spacy.language import Language

from ..models.travel import (
    TravelEntity,
    TravelOrderResponse,
    TravelServiceConfig,
)


class TravelService:
    """Service for identifying travel order entities using NER."""

    _instance: "TravelService | None" = None
    _model: Language | None = None

    def __init__(self, config: TravelServiceConfig | None = None):
        self._config = config or TravelServiceConfig()

    @classmethod
    def get_instance(cls, config: TravelServiceConfig | None = None) -> "TravelService":
        """Get or create singleton instance of the service."""
        if cls._instance is None:
            cls._instance = cls(config)
        return cls._instance

    def _get_model(self) -> Language:
        """Load the spaCy NER model (lazy loading with caching)."""
        if TravelService._model is None:
            TravelService._model = spacy.load(self._config.model_path)
        return TravelService._model

    def identify_travel_order(self, text: str) -> TravelOrderResponse:
        """Extract travel entities (departure, destination, time) from text."""
        model = self._get_model()
        doc = model(text)

        entities = []
        departure = None
        destination = None
        time = None

        for ent in doc.ents:
            entity = TravelEntity(
                text=ent.text,
                label=ent.label_,
                start=ent.start_char,
                end=ent.end_char,
            )
            entities.append(entity)

            if ent.label_ == "DEPARTURE":
                departure = ent.text
            elif ent.label_ == "DESTINATION":
                destination = ent.text
            elif ent.label_ == "TIME":
                time = ent.text

        return TravelOrderResponse(
            departure=departure,
            destination=destination,
            time=time,
            entities=entities,
        )
