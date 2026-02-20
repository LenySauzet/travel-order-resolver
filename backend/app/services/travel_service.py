import os
from typing import Any

import spacy
from spacy.language import Language
import unicodedata
import re

from ..models.travel import TravelOrderResponse, TravelServiceConfig
from .time_normalizer import TimeNormalizer
from .station_matcher import StationMatcher
from .geolocation import GeoLocationService


NER_MODELS: dict[str, dict[str, str]] = {
    "spacy": {
        "name": "SpaCy NER",
        "path": "base/models/travel-order-ner-model",
        "type": "spacy",
    },
    "camembert": {
        "name": "CamemBERT NER",
        "path": "base/models/BERT/camembert-ner-travel",
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
        model_path = model_info["path"]

        if model_info["type"] == "spacy":
            loaded = spacy.load(model_path)
        elif model_info["type"] == "transformers":
            import torch
            from transformers import AutoTokenizer, AutoModelForTokenClassification

            tokenizer = AutoTokenizer.from_pretrained(model_path)
            model = AutoModelForTokenClassification.from_pretrained(model_path)
            device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
            model.to(device)
            model.eval()
            loaded = (model, tokenizer)
        else:
            raise ValueError(f"Unknown model type: {model_info['type']}")

        TravelService._models[key] = loaded
        return loaded

    def get_available_models(self) -> dict[str, str]:
        """Return models whose path exists on disk."""
        available = {}
        for key, info in NER_MODELS.items():
            if os.path.exists(info["path"]):
                available[key] = info["name"]
        return available

    def _match_station_id(self, text: str | None) -> int | None:
        if not text:
            return None
        match = self._station_matcher.match(text)
        return match.id if match else None

    def _get_nearest_station_id(self, coords: tuple[float, float]) -> int | None:
        return self._geolocation.find_nearest_station_id(*coords)

    def _predict_camembert(self, text: str, model: Any, tokenizer: Any) -> dict[str, list[str]]:
        """Run CamemBERT NER inference, reusing logic from test_camembert.py."""
        import torch

        device = next(model.parameters()).device
        model_id2label = model.config.id2label

        inputs = tokenizer(
            text,
            return_tensors="pt",
            return_offsets_mapping=True,
            padding=True,
            truncation=True,
            max_length=128,
        )

        offset_mapping = inputs.pop("offset_mapping").squeeze().tolist()
        inputs = {k: v.to(device) for k, v in inputs.items()}

        with torch.no_grad():
            outputs = model(**inputs)
            predictions = torch.argmax(outputs.logits, dim=2).squeeze().tolist()

        if not isinstance(predictions, list):
            predictions = [predictions]

        entities: dict[str, list[str]] = {"DEPARTURE": [], "DESTINATION": [], "TIME": []}
        current_entity: str | None = None
        current_tokens: list[tuple[int, int]] = []

        for pred, (start, end) in zip(predictions, offset_mapping):
            if start == 0 and end == 0:
                continue

            label = model_id2label.get(pred, "O")

            if label.startswith("B-"):
                if current_entity and current_tokens:
                    entity_text = text[current_tokens[0][0]:current_tokens[-1][1]].strip()
                    entities[current_entity].append(entity_text)
                current_entity = label[2:]
                current_tokens = [(start, end)]
            elif label.startswith("I-") and current_entity == label[2:]:
                current_tokens.append((start, end))
            else:
                if current_entity and current_tokens:
                    entity_text = text[current_tokens[0][0]:current_tokens[-1][1]].strip()
                    entities[current_entity].append(entity_text)
                current_entity = None
                current_tokens = []

        if current_entity and current_tokens:
            entity_text = text[current_tokens[0][0]:current_tokens[-1][1]].strip()
            entities[current_entity].append(entity_text)

        return entities

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
            model, tokenizer = loaded
            entities = self._predict_camembert(normalized, model, tokenizer)
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
