import spacy
from spacy.language import Language
import unicodedata
import re

from ..models.travel import TravelOrderResponse, TravelServiceConfig
from .time_normalizer import TimeNormalizer
from .station_matcher import StationMatcher
from .geolocation import GeoLocationService


def normalize_text(text: str) -> str:
    text = text.lower()
    normalized = unicodedata.normalize('NFD', text)
    text = ''.join(c for c in normalized if not unicodedata.combining(c))
    text = re.sub(r'[^A-Za-z0-9\s]', ' ', text)
    return re.sub(r'\s+', ' ', text).strip()


class TravelService:
    _instance: "TravelService | None" = None
    _model: Language | None = None

    def __init__(self, config: TravelServiceConfig | None = None):
        self._config = config or TravelServiceConfig()
        self._station_matcher = StationMatcher.get_instance()
        self._geolocation = GeoLocationService.get_instance()

    @classmethod
    def get_instance(cls, config: TravelServiceConfig | None = None) -> "TravelService":
        if cls._instance is None:
            cls._instance = cls(config)
        return cls._instance

    def _get_model(self) -> Language:
        if TravelService._model is None:
            TravelService._model = spacy.load(self._config.model_path)
        return TravelService._model

    def _match_station_id(self, text: str | None) -> int | None:
        if not text:
            return None
        match = self._station_matcher.match(text)
        return match.id if match else None

    def _get_nearest_station_id(self, coords: tuple[float, float]) -> int | None:
        return self._geolocation.find_nearest_station_id(*coords)

    def identify_travel_order(
        self, text: str, coords: tuple[float, float] | None = None
    ) -> TravelOrderResponse:
        doc = self._get_model()(normalize_text(text))

        raw_departure: str | None = None
        raw_destination: str | None = None
        datetime_iso: str | None = None

        for ent in doc.ents:
            if ent.label_ == "DEPARTURE":
                raw_departure = ent.text
            elif ent.label_ == "DESTINATION":
                raw_destination = ent.text
            elif ent.label_ == "TIME":
                print("raw time", ent.text)
                print("normalized time", TimeNormalizer.normalize(ent.text))
                print("end time normalize")
                datetime_iso = TimeNormalizer.normalize(ent.text)

        departure_id = self._match_station_id(raw_departure)
        
        # Fallback: use geolocation if no departure found
        if departure_id is None and coords:
            departure_id = self._get_nearest_station_id(coords)

        return TravelOrderResponse(
            departure_id=departure_id,
            destination_id=self._match_station_id(raw_destination),
            datetime_iso=datetime_iso,
        )
