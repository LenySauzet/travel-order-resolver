import pandas as pd
from pathlib import Path
from thefuzz import process, fuzz
from pydantic import BaseModel


class StationMatch(BaseModel):
    id: int
    raw: str
    matched: str
    score: int
    uic: str | None = None
    lat: float | None = None
    lon: float | None = None


class StationMatcher:
    """Fuzzy matching service for station names."""

    _instance: "StationMatcher | None" = None
    _entries_list: list[str] | None = None
    _entries_lookup: dict[str, tuple[int, str, str, float | None, float | None]] | None = None
    _all_entries: list[dict] | None = None

    DEFAULT_DATA_PATH = "base/data/processed/entries.csv"
    MIN_SCORE_THRESHOLD = 60

    def __init__(self, data_path: str | None = None):
        self._data_path = data_path or self.DEFAULT_DATA_PATH

    @classmethod
    def get_instance(cls, data_path: str | None = None) -> "StationMatcher":
        if cls._instance is None:
            cls._instance = cls(data_path)
            cls._instance._load_data()
        return cls._instance

    def _load_data(self) -> None:
        if StationMatcher._entries_list is not None:
            return
            
        path = Path(self._data_path)
        if not path.exists():
            raise FileNotFoundError(f"Data file not found: {self._data_path}")
        
        df = pd.read_csv(path)
        
        def parse_coord(value) -> float | None:
            if pd.notna(value):
                return float(value)
            return None

        def parse_uic(value) -> str | None:
            if pd.notna(value):
                return str(value)
            return None

        StationMatcher._entries_list = df['entries'].tolist()
        StationMatcher._entries_lookup = {
            row['entries']: (
                int(row['index']),
                row['raw'],
                parse_uic(row.get('uic')) or "",
                parse_coord(row.get('lat')),
                parse_coord(row.get('lon')),
            )
            for _, row in df.iterrows()
        }
        StationMatcher._all_entries = [
            {
                "id": int(row['index']),
                "raw": row['raw'],
                "entries": row['entries'],
                "uic": parse_uic(row.get('uic')),
                "lat": parse_coord(row.get('lat')),
                "lon": parse_coord(row.get('lon')),
            }
            for _, row in df.iterrows()
        ]

    def match(self, query: str, score_cutoff: int | None = None) -> StationMatch | None:
        if not query or not query.strip():
            return None

        cutoff = score_cutoff or self.MIN_SCORE_THRESHOLD
        result = process.extractOne(
            query.lower().strip(),
            self._entries_list,
            score_cutoff=cutoff,
            scorer=fuzz.partial_ratio
        )
        
        print("query", query)
        print("result", result)

        if result is None:
            return None

        matched_entry, score = result[0], result[1]
        entry_id, raw_name, uic_code, lat, lon = self._entries_lookup[matched_entry]  # type: ignore

        return StationMatch(
            id=entry_id,
            raw=raw_name,
            matched=matched_entry,
            score=score,
            uic=uic_code,
            lat=lat,
            lon=lon,
        )

    def get_by_id(self, entry_id: int) -> StationMatch | None:
        for entry in self._all_entries or []:
            if entry["id"] == entry_id:
                return StationMatch(
                    id=entry["id"],
                    raw=entry["raw"],
                    matched=entry["entries"],
                    score=100,
                    uic=entry.get("uic"),
                    lat=entry.get("lat"),
                    lon=entry.get("lon"),
                )
        return None

    def get_all_entries(self) -> list[dict]:
        return self._all_entries or []
