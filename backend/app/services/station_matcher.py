import pandas as pd
from pathlib import Path
from thefuzz import process, fuzz
from pydantic import BaseModel


class StationMatch(BaseModel):
    id: int
    raw: str
    matched: str
    score: int


class StationMatcher:
    """Fuzzy matching service for station names."""

    _instance: "StationMatcher | None" = None
    _entries_list: list[str] | None = None
    _entries_lookup: dict[str, tuple[int, str]] | None = None
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
        
        StationMatcher._entries_list = df['entries'].tolist()
        StationMatcher._entries_lookup = {
            row['entries']: (row['index'], row['raw'])
            for _, row in df.iterrows()
        }
        StationMatcher._all_entries = [
            {"id": row['index'], "raw": row['raw'], "entries": row['entries']}
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
            scorer=fuzz.token_sort_ratio
        )

        if result is None:
            return None

        matched_entry, score = result[0], result[1]
        entry_id, raw_name = self._entries_lookup[matched_entry]  # type: ignore

        return StationMatch(id=entry_id, raw=raw_name, matched=matched_entry, score=score)

    def get_by_id(self, entry_id: int) -> StationMatch | None:
        for entry in self._all_entries or []:
            if entry["id"] == entry_id:
                return StationMatch(
                    id=entry["id"],
                    raw=entry["raw"],
                    matched=entry["entries"],
                    score=100
                )
        return None

    def get_all_entries(self) -> list[dict]:
        return self._all_entries or []
