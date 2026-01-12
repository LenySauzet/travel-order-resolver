"""API client for the Travel Order Resolver backend."""

import requests
import streamlit as st

from models import JourneySearchResponse, Station, TravelOrderResponse

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
    text: str, coords: tuple[float, float] | None = None
) -> TravelOrderResponse | None:
    """Identify a travel order from text."""
    try:
        params: dict[str, str] = {"text": text}
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


@st.cache_data(ttl=3600)
def get_stations() -> list[Station]:
    """Fetch the list of stations (cached for 1 hour)."""
    try:
        response = requests.get(f"{API_BASE_URL}/stations", timeout=DEFAULT_TIMEOUT)
        response.raise_for_status()
        data = response.json().get("stations", [])
        return [Station.model_validate(s) for s in data]
    except requests.exceptions.RequestException:
        st.toast("❌ Erreur transcription")
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
