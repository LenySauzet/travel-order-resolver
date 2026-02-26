from typing import Any
from huggingface_hub import snapshot_download
import spacy
import unicodedata
import re

import torch
from transformers import AutoTokenizer, AutoModelForTokenClassification, pipeline

from ..models.travel import TravelOrderResponse, TravelServiceConfig
from .time_normalizer import TimeNormalizer
from .station_matcher import StationMatcher
from .geolocation import GeoLocationService


NER_MODELS: dict[str, dict[str, str]] = {
    "spacy": {
        "name": "SpaCy NER",
        "repo": "YanisC/fr_travel_order_ner_model",
        "type": "spacy",
    },
    "camembert": {
        "name": "CamemBERT NER",
        "repo": "YanisC/camembert-ner-travel",
        "type": "transformers",
    },
}


def normalize_text(text: str) -> str:
    text = text.lower()
    normalized = unicodedata.normalize('NFD', text)
    text = ''.join(c for c in normalized if not unicodedata.combining(c))
    text = re.sub(r'[^A-Za-z0-9\s]', ' ', text)
    return re.sub(r'\s+', ' ', text).strip()


class TravelService:
    _instance: "TravelService | None" = None
    _models: dict[str, Any] = {}

    def __init__(self, config: TravelServiceConfig | None = None):
        self._config = config or TravelServiceConfig()
        self._station_matcher = StationMatcher.get_instance()
        self._geolocation = GeoLocationService.get_instance()

    @classmethod
    def get_instance(cls, config: TravelServiceConfig | None = None) -> "TravelService":
        if cls._instance is None:
            cls._instance = cls(config)
        return cls._instance

    def _load_model(self, key: str) -> Any:
        if key in TravelService._models:
            return TravelService._models[key]

        model_info = NER_MODELS[key]
        model_repo = model_info["repo"]

        if model_info["type"] == "spacy":
            model_path = snapshot_download(repo_id=model_repo)
            loaded = spacy.load(model_path)
        elif model_info["type"] == "transformers":

            bert_tokenizer = AutoTokenizer.from_pretrained(model_repo)
            bert_model = AutoModelForTokenClassification.from_pretrained(model_repo)

            device = 0 if torch.cuda.is_available() else -1
            loaded = pipeline("ner", model=bert_model, tokenizer=bert_tokenizer, aggregation_strategy="simple", device=device)
        else:
            raise ValueError(f"Unknown model type: {model_info['type']}")

        TravelService._models[key] = loaded
        return loaded

    def get_available_models(self) -> dict[str, str]:
        return {key: info["name"] for key, info in NER_MODELS.items()}

    def _match_station_id(self, text: str | None) -> int | None:
        if not text:
            return None
        match = self._station_matcher.match(text)
        return match.id if match else None

    def _get_nearest_station_id(self, coords: tuple[float, float]) -> int | None:
        return self._geolocation.find_nearest_station_id(*coords)

    def identify_travel_order(
        self, text: str, coords: tuple[float, float] | None = None, model_key: str = "spacy"
    ) -> TravelOrderResponse:
        available = self.get_available_models()
        if model_key not in available:
            model_key = "spacy"

        loaded = self._load_model(model_key)
        normalized = normalize_text(text)
        model_type = NER_MODELS[model_key]["type"]

        raw_departure: str | None = None
        raw_destination: str | None = None
        datetime_iso: str | None = None

        if model_type == "spacy":
            doc = loaded(normalized)
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
        elif model_type == "transformers":
            results = loaded(normalized)
            entities: dict[str, list[str]] = {"DEPARTURE": [], "DESTINATION": [], "TIME": []}
            for ent in results:
                if ent["entity_group"] in entities:
                    entities[ent["entity_group"]].append(ent["word"])
            raw_departure = entities["DEPARTURE"][0] if entities["DEPARTURE"] else None
            raw_destination = entities["DESTINATION"][0] if entities["DESTINATION"] else None
            if entities["TIME"]:
                raw_time = entities["TIME"][0]
                print("raw time", raw_time)
                print("normalized time", TimeNormalizer.normalize(raw_time))
                print("end time normalize")
                datetime_iso = TimeNormalizer.normalize(raw_time)

        departure_id = self._match_station_id(raw_departure)

        # Fallback: use geolocation if no departure found
        if departure_id is None and coords:
            departure_id = self._get_nearest_station_id(coords)

        return TravelOrderResponse(
            departure_id=departure_id,
            destination_id=self._match_station_id(raw_destination),
            datetime_iso=datetime_iso,
        )
