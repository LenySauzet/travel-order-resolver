"""API client for the Travel Order Resolver backend."""

import requests
import streamlit as st

from models import (
    JourneySearchResponse,
    Station,
    TravelOrderResponse,
    ShortestPathResponse,
    BestRoutesResponse,
    RoutingModeResponse,
)

API_BASE_URL = "http://localhost:8000/api/v1"
DEFAULT_TIMEOUT = 10
SEARCH_TIMEOUT = 35


def transcribe_audio(audio_bytes: bytes) -> str:
    """Transcribe an audio file to text."""
    try:
        response = requests.post(
            f"{API_BASE_URL}/transcribe",
            files={"file": ("audio.wav", audio_bytes, "audio/wav")},
            timeout=DEFAULT_TIMEOUT,
        )
        response.raise_for_status()
        return response.json().get("text", "")
    except requests.exceptions.RequestException:
        st.toast("❌ Erreur transcription")
        return ""


def identify_travel_order(
    text: str, coords: tuple[float, float] | None = None, model: str = "spacy"
) -> TravelOrderResponse | None:
    """Identify a travel order from text."""
    try:
        params: dict[str, str] = {"text": text, "model": model}
        if coords:
            params["lat"] = str(coords[0])
            params["lon"] = str(coords[1])

        response = requests.get(
            f"{API_BASE_URL}/identify-travel-order",
            params=params,
            timeout=DEFAULT_TIMEOUT,
        )
        response.raise_for_status()
        return TravelOrderResponse.model_validate(response.json())
    except requests.exceptions.RequestException:
        st.toast("❌ Erreur transcription")
        return None


@st.cache_data(ttl=600)
def get_ner_models() -> dict[str, str]:
    """Fetch the available NER models (cached for 10 minutes)."""
    try:
        response = requests.get(f"{API_BASE_URL}/ner-models", timeout=DEFAULT_TIMEOUT)
        response.raise_for_status()
        return response.json().get("models", {})
    except requests.exceptions.RequestException:
        return {"spacy": "SpaCy NER"}


@st.cache_data(ttl=3600)
def get_stations() -> list[Station]:
    """Fetch the list of stations (cached for 1 hour)."""
    try:
        response = requests.get(f"{API_BASE_URL}/stations", timeout=DEFAULT_TIMEOUT)
        response.raise_for_status()
        data = response.json().get("stations", [])
        return [Station.model_validate(s) for s in data]
    except requests.exceptions.RequestException:
        return []


def search_journeys(
    departure_id: int,
    destination_id: int,
    datetime_iso: str | None = None,
    datetime_represents: str = "departure",
) -> JourneySearchResponse | None:
    """
    Search for journeys via the Navitia API.
    """
    try:
        params: dict[str, str | int] = {
            "departure_id": departure_id,
            "destination_id": destination_id,
            "datetime_represents": datetime_represents,
        }
        if datetime_iso:
            params["datetime_iso"] = datetime_iso

        response = requests.get(
            f"{API_BASE_URL}/journeys",
            params=params,
            timeout=SEARCH_TIMEOUT,
        )
        response.raise_for_status()
        return JourneySearchResponse.model_validate(response.json())
    except requests.exceptions.RequestException as e:
        st.toast(f"❌ Error recherche de trajets: {e}")
        return None

def get_shortest_path(start_id: int, end_id: int) -> ShortestPathResponse | None:
    """
    Get the shortest path between two stations.
    """
    try:
        params: dict[str, int] = {
            "start_id": start_id,
            "end_id": end_id,
        }
        
        response = requests.get(
            f"{API_BASE_URL}/shortest-path",
            params=params,
            timeout=SEARCH_TIMEOUT,
        )
        response.raise_for_status()
        return ShortestPathResponse.model_validate(response.json())
    except requests.exceptions.RequestException as e:
        st.toast(f"❌ Erreur calcul itinéraire: {e}")
        return None


def get_best_routes(start_id: int, end_id: int, limit: int = 5) -> BestRoutesResponse | None:
    """Get best Dijkstra routes between two stations."""
    try:
        params: dict[str, int] = {
            "start_id": start_id,
            "end_id": end_id,
            "limit": limit,
        }

        response = requests.get(
            f"{API_BASE_URL}/best-routes",
            params=params,
            timeout=SEARCH_TIMEOUT,
        )
        response.raise_for_status()
        return BestRoutesResponse.model_validate(response.json())
    except requests.exceptions.RequestException as e:
        st.toast(f"❌ Erreur calcul itinéraires: {e}")
        return None


def get_routing_mode() -> RoutingModeResponse | None:
    try:
        response = requests.get(
            f"{API_BASE_URL}/routing-mode",
            timeout=DEFAULT_TIMEOUT,
        )
        response.raise_for_status()
        return RoutingModeResponse.model_validate(response.json())
    except requests.exceptions.RequestException as e:
        st.toast(f"❌ Erreur lecture mode routing: {e}")
        return None


def set_routing_mode(mode: str) -> RoutingModeResponse | None:
    try:
        response = requests.post(
            f"{API_BASE_URL}/routing-mode",
            params={"mode": mode},
            timeout=DEFAULT_TIMEOUT,
        )
        response.raise_for_status()
        return RoutingModeResponse.model_validate(response.json())
    except requests.exceptions.RequestException as e:
        st.toast(f"❌ Erreur changement mode routing: {e}")
        return None
