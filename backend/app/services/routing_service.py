import heapq
import pandas as pd
from .station_matcher import StationMatcher


class RoutingService:
    _instance: "RoutingService | None" = None
    _graph: dict[str, dict[str, float]] | None = None
    _uic_to_id: dict[str, int] | None = None
    _id_to_uic: dict[int, str] | None = None
    MODES = {
        "shortcuts": "base/data/station_durations.csv",
        "no_shortcuts": "base/data/station_durations_infra.csv",
    }
    DEFAULT_MODE = "shortcuts"

    def __init__(self):
        self._station_matcher = StationMatcher.get_instance()
        self._mode = self.DEFAULT_MODE
        self._load_graph()

    @classmethod
    def get_instance(cls) -> "RoutingService":
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def _load_graph(self) -> None:
        print("Loading routing graph...")
        try:
            durations_path = self.MODES[self._mode]
            df = pd.read_csv(durations_path)
            df['source_uic'] = df['source_uic'].astype(str)
            df['target_uic'] = df['target_uic'].astype(str)
        except Exception as e:
            print(f"Error loading station durations: {e}")
            self._graph = {}
            return

        self._graph = {}
        count = 0
        for _, row in df.iterrows():
            u_uic = row['source_uic']
            v_uic = row['target_uic']
            weight = float(row['weight_minutes'])
            if u_uic not in self._graph:
                self._graph[u_uic] = {}
            if v_uic in self._graph[u_uic]:
                self._graph[u_uic][v_uic] = min(self._graph[u_uic][v_uic], weight)
            else:
                self._graph[u_uic][v_uic] = weight
            count += 1
        print(f"Graph loaded with {len(self._graph)} nodes and {count} edges.")

    def get_mode(self) -> str:
        return self._mode

    def get_modes(self) -> list[str]:
        return list(self.MODES.keys())

    def set_mode(self, mode: str) -> bool:
        if mode not in self.MODES:
            return False
        if mode == self._mode:
            return True
        self._mode = mode
        self._load_graph()
        return True

    def _ensure_mappings(self) -> None:
        if self._uic_to_id is not None and self._id_to_uic is not None:
            return
        self._uic_to_id = {}
        self._id_to_uic = {}
        for entry in self._station_matcher.get_all_entries():
            station_id = entry.get("id")
            uic = str(entry.get("uic", ""))
            if station_id is None or not uic:
                continue
            if uic not in self._uic_to_id:
                self._uic_to_id[uic] = station_id
            if station_id not in self._id_to_uic:
                self._id_to_uic[station_id] = uic

    def _get_uic_for_id(self, station_id: int) -> str | None:
        self._ensure_mappings()
        if self._id_to_uic is None:
            return None
        return self._id_to_uic.get(station_id)

    def _get_id_for_uic(self, uic: str) -> int | None:
        self._ensure_mappings()
        if self._uic_to_id is None:
            return None
        return self._uic_to_id.get(uic)

    def _dijkstra_uic(self, start_uic: str, end_uic: str) -> tuple[float, list[str]]:
        if not self._graph:
            return float('inf'), []
        queue: list[tuple[float, str, list[str]]] = [(0.0, start_uic, [start_uic])]
        best_cost: dict[str, float] = {start_uic: 0.0}
        while queue:
            cost, node, path = heapq.heappop(queue)
            if cost > best_cost.get(node, float('inf')):
                continue
            if node == end_uic:
                return cost, path
            for neighbor, weight in self._graph.get(node, {}).items():
                next_cost = cost + weight
                if next_cost < best_cost.get(neighbor, float('inf')):
                    best_cost[neighbor] = next_cost
                    heapq.heappush(queue, (next_cost, neighbor, path + [neighbor]))
        return float('inf'), []

    def _uic_path_to_id_path(self, uic_path: list[str]) -> list[int]:
        id_path: list[int] = []
        for uic in uic_path:
            station_id = self._get_id_for_uic(uic)
            if station_id is not None:
                id_path.append(station_id)
        return id_path

    def compute_shortest_path(self, start_id: int, end_id: int) -> tuple[float, list[int]]:
        if not self._graph:
            return float('inf'), []
        start_uic = self._get_uic_for_id(start_id)
        end_uic = self._get_uic_for_id(end_id)
        if not start_uic or not end_uic:
            return float('inf'), []
        duration, uic_path = self._dijkstra_uic(start_uic, end_uic)
        if duration == float('inf') or not uic_path:
            return float('inf'), []
        id_path = self._uic_path_to_id_path(uic_path)
        if not id_path:
            return float('inf'), []
        return duration, id_path

    def compute_best_routes(self, start_id: int, end_id: int, k: int = 5) -> list[tuple[float, list[int]]]:
        if k <= 0:
            return []
        shortest = self.compute_shortest_path(start_id, end_id)
        if shortest[0] == float('inf'):
            return []
        return [shortest][:k]
