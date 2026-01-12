import httpx
from datetime import datetime

from ..core.config import config
from ..models.journey import (
    Journey,
    JourneySection,
    JourneyPlace,
    JourneySearchResponse,
)
from .geolocation import GeoLocationService


class NavitiaService:
    """Service to interact with the Navitia API."""

    _instance: "NavitiaService | None" = None

    def __init__(self):
        self._api_key = config.navitia_api_key
        self._base_url = config.navitia_base_url
        self._coverage = config.navitia_coverage
        self._geolocation = GeoLocationService.get_instance()

    @classmethod
    def get_instance(cls) -> "NavitiaService":
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def _get_station_coords(self, station_id: int) -> tuple[float, float] | None:
        """Get the coordinates of a station by its ID."""
        stations = self._geolocation._stations_with_coords or []
        for station in stations:
            if station["id"] == station_id:
                return (station["lon"], station["lat"])
        return None

    def _format_coords(self, coords: tuple[float, float]) -> str:
        """Format the coordinates for the Navitia API (lon;lat)."""
        return f"{coords[0]};{coords[1]}"

    def _parse_place(self, place_data: dict) -> JourneyPlace:
        """Parse a place from the Navitia response."""
        name = place_data.get("name", "Inconnu")
        
        # Try to get the name of the stop_area or stop_point
        if "stop_point" in place_data:
            name = place_data["stop_point"].get("name", name)
        elif "stop_area" in place_data:
            name = place_data["stop_area"].get("name", name)
        elif "address" in place_data:
            name = place_data["address"].get("name", name)
        
        coord = None
        if "stop_point" in place_data and "coord" in place_data["stop_point"]:
            c = place_data["stop_point"]["coord"]
            coord = (float(c["lon"]), float(c["lat"]))
        elif "address" in place_data and "coord" in place_data["address"]:
            c = place_data["address"]["coord"]
            coord = (float(c["lon"]), float(c["lat"]))
        
        return JourneyPlace(name=name, coord=coord)

    def _parse_section(self, section_data: dict) -> JourneySection:
        """Parse a section of a journey from the Navitia response."""
        section_type = section_data.get("type", "unknown")
        mode = section_data.get("mode")
        
        from_place = self._parse_place(section_data.get("from", {}))
        to_place = self._parse_place(section_data.get("to", {}))
        
        # Public transport information
        line_name = None
        line_code = None
        commercial_mode = None
        direction = None
        network = None
        
        if "display_informations" in section_data:
            display = section_data["display_informations"]
            line_name = display.get("label")
            line_code = display.get("code")
            commercial_mode = display.get("commercial_mode")
            direction = display.get("direction")
            network = display.get("network")
        
        return JourneySection(
            type=section_type,
            mode=mode,
            from_place=from_place,
            to_place=to_place,
            departure_datetime=section_data.get("departure_date_time", ""),
            arrival_datetime=section_data.get("arrival_date_time", ""),
            duration=section_data.get("duration", 0),
            line_name=line_name,
            line_code=line_code,
            commercial_mode=commercial_mode,
            direction=direction,
            network=network,
        )

    def _parse_journey(self, journey_data: dict) -> Journey:
        """Parse a complete journey from the Navitia response."""
        sections = [
            self._parse_section(s) 
            for s in journey_data.get("sections", [])
        ]
        
        co2 = None
        if "co2_emission" in journey_data and journey_data["co2_emission"]:
            co2 = journey_data["co2_emission"].get("value")
        
        return Journey(
            departure_datetime=journey_data.get("departure_date_time", ""),
            arrival_datetime=journey_data.get("arrival_date_time", ""),
            duration=journey_data.get("duration", 0),
            nb_transfers=journey_data.get("nb_transfers", 0),
            walking_duration=journey_data.get("durations", {}).get("walking", 0),
            co2_emission=co2,
            sections=sections,
        )

    async def search_journeys(
        self,
        departure_station_id: int,
        destination_station_id: int,
        datetime_iso: str | None = None,
        datetime_represents: str = "departure",
    ) -> JourneySearchResponse:
        """
        Search for journeys between two stations.
        """
        if not self._api_key:
            return JourneySearchResponse(
                journeys=[],
                error="Clé API Navitia non configurée"
            )
        
        # Get the coordinates of the stations
        dep_coords = self._get_station_coords(departure_station_id)
        dest_coords = self._get_station_coords(destination_station_id)
        
        if not dep_coords:
            return JourneySearchResponse(
                journeys=[],
                error=f"Station de départ introuvable (ID: {departure_station_id})"
            )
        
        if not dest_coords:
            return JourneySearchResponse(
                journeys=[],
                error=f"Station d'arrivée introuvable (ID: {destination_station_id})"
            )
        
        # Build the API URL
        url = f"{self._base_url}/coverage/{self._coverage}/journeys"
        
        # Request parameters
        params = {
            "from": self._format_coords(dep_coords),
            "to": self._format_coords(dest_coords),
            "datetime_represents": datetime_represents,
            "count": 1,  # Number of journeys to return
            "depth": 2,  # Detail level
        }
        
        # Add the datetime if provided
        if datetime_iso:
            # Convert ISO to Navitia format (YYYYMMDDTHHmmss)
            try:
                dt = datetime.fromisoformat(datetime_iso.replace("Z", "+00:00"))
                params["datetime"] = dt.strftime("%Y%m%dT%H%M%S")
            except ValueError:
                pass
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    url,
                    params=params,
                    headers={"Authorization": self._api_key},
                    timeout=30.0,
                )
                
                if response.status_code == 401:
                    return JourneySearchResponse(
                        journeys=[],
                        error="Clé API Navitia invalide"
                    )
                
                if response.status_code == 404:
                    return JourneySearchResponse(
                        journeys=[],
                        error="Aucun trajet trouvé"
                    )
                
                response.raise_for_status()
                data = response.json()
                
                # Parse the journeys
                journeys = []
                for journey_data in data.get("journeys", []):
                    try:
                        journey = self._parse_journey(journey_data)
                        journeys.append(journey)
                    except Exception:
                        continue
                
                if not journeys and "error" in data:
                    return JourneySearchResponse(
                        journeys=[],
                        error=data["error"].get("message", "Erreur inconnue")
                    )
                
                return JourneySearchResponse(journeys=journeys)
                
        except httpx.TimeoutException:
            return JourneySearchResponse(
                journeys=[],
                error="Timeout lors de la requête Navitia"
            )
        except httpx.HTTPStatusError as e:
            return JourneySearchResponse(
                journeys=[],
                error=f"Erreur HTTP: {e.response.status_code}"
            )
        except Exception as e:
            return JourneySearchResponse(
                journeys=[],
                error=f"Erreur: {str(e)}"
            )
