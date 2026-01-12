import pandas as pd
from pathlib import Path
from math import radians, cos, sin, sqrt, atan2


class GeoLocationService:
    _instance: "GeoLocationService | None" = None
    _stations_with_coords: list[dict] | None = None

    STATIONS_DATA_PATH = "base/data/processed/entries.csv"

    @classmethod
    def get_instance(cls) -> "GeoLocationService":
        if cls._instance is None:
            cls._instance = cls()
            cls._instance._load_stations()
        return cls._instance

    def _load_stations(self) -> None:
        if GeoLocationService._stations_with_coords is not None:
            return

        path = Path(self.STATIONS_DATA_PATH)
        if not path.exists():
            GeoLocationService._stations_with_coords = []
            return

        df = pd.read_csv(path)

        GeoLocationService._stations_with_coords = [
            {"id": row["index"], "lat": float(row["Y_WGS84"]), "lon": float(row["X_WGS84"])}
            for _, row in df.iterrows()
            if pd.notna(row["Y_WGS84"]) and pd.notna(row["X_WGS84"])
        ]

    @staticmethod
    def _haversine(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        R = 6371
        lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])
        dlat, dlon = lat2 - lat1, lon2 - lon1
        a = sin(dlat / 2) ** 2 + cos(lat1) * cos(lat2) * sin(dlon / 2) ** 2
        return R * 2 * atan2(sqrt(a), sqrt(1 - a))

    def find_nearest_station_id(self, lat: float, lon: float) -> int | None:
        if not self._stations_with_coords:
            return None
        nearest = min(
            self._stations_with_coords,
            key=lambda s: self._haversine(lat, lon, s["lat"], s["lon"])
        )
        return nearest["id"]
