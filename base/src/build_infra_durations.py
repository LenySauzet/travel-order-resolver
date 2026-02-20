import math
import re
from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[2]
INPUT_GARES = ROOT / "base/data/raw/liste-des-gares.csv"
INPUT_GTFS_DURATIONS = ROOT / "base/data/station_durations.csv"
OUTPUT_INFRA_DURATIONS = ROOT / "base/data/station_durations_infra.csv"
AVG_SPEED_KMH = 110.0
MIN_EDGE_MINUTES = 1.0
WALK_SPEED_KMH = 4.5
TRANSFER_BUFFER_MINUTES = 5.0
TRANSFER_MAX_DISTANCE_KM = 4.0


def normalize_uic(value: str) -> str | None:
    if value is None:
        return None
    raw = str(value).strip()
    if not raw:
        return None
    digits = re.findall(r"\d+", raw)
    if not digits:
        return None
    return digits[0]


def parse_pk_km(value: str) -> float | None:
    if value is None:
        return None
    raw = str(value).strip().replace(",", ".")
    if not raw:
        return None
    m = re.match(r"^\s*(\d+)\+(\d+)\s*$", raw)
    if m:
        return float(m.group(1)) + float(m.group(2)) / 1000.0
    try:
        return float(raw)
    except ValueError:
        return None


def to_float(value: str) -> float | None:
    if value is None:
        return None
    raw = str(value).strip().replace(",", ".")
    if not raw:
        return None
    try:
        return float(raw)
    except ValueError:
        return None


def haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    r = 6371.0
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)
    a = math.sin(dphi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2) ** 2
    return 2 * r * math.atan2(math.sqrt(a), math.sqrt(1 - a))


def build_gtfs_duration_lookup(path: Path) -> dict[tuple[str, str], float]:
    if not path.exists():
        return {}
    df = pd.read_csv(path, dtype=str)
    if "weight_minutes" not in df.columns:
        return {}
    lookup: dict[tuple[str, str], float] = {}
    for _, row in df.iterrows():
        src = normalize_uic(row.get("source_uic"))
        dst = normalize_uic(row.get("target_uic"))
        w = to_float(row.get("weight_minutes"))
        if not src or not dst or w is None:
            continue
        key = (src, dst)
        if key not in lookup or w < lookup[key]:
            lookup[key] = w
    return lookup


def estimate_minutes(distance_km: float) -> float:
    if distance_km <= 0:
        return MIN_EDGE_MINUTES
    return max(MIN_EDGE_MINUTES, (distance_km / AVG_SPEED_KMH) * 60.0)


def estimate_transfer_minutes(distance_km: float) -> float:
    walk = (distance_km / WALK_SPEED_KMH) * 60.0
    return max(TRANSFER_BUFFER_MINUTES, TRANSFER_BUFFER_MINUTES + walk)


def build_edges() -> pd.DataFrame:
    df = pd.read_csv(INPUT_GARES, sep=";", dtype=str)
    df = df[df["VOYAGEURS"].fillna("").str.upper().eq("O")].copy()
    df["uic"] = df["CODE_UIC"].apply(normalize_uic)
    df["line"] = df["CODE_LIGNE"].fillna("").str.strip()
    df["commune"] = df["COMMUNE"].fillna("").str.strip().str.lower()
    df["pk_km"] = df["PK"].apply(parse_pk_km)
    df["lon"] = df["X_WGS84"].apply(to_float)
    df["lat"] = df["Y_WGS84"].apply(to_float)
    df["name"] = df["LIBELLE"].fillna("").str.strip()
    df = df.dropna(subset=["uic", "pk_km"])
    df = df[df["line"] != ""]

    gtfs_lookup = build_gtfs_duration_lookup(INPUT_GTFS_DURATIONS)
    uic_to_name = (
        df[df["name"] != ""]
        .drop_duplicates(subset=["uic"])
        .set_index("uic")["name"]
        .to_dict()
    )

    edges: dict[tuple[str, str], float] = {}

    grouped = df.groupby(["line"], sort=False)
    for _, g in grouped:
        g = g.sort_values("pk_km")
        rows = g.to_dict(orient="records")
        deduped: list[dict] = []
        seen_seq: set[tuple[str, float]] = set()
        for row in rows:
            key = (row["uic"], row["pk_km"])
            if key in seen_seq:
                continue
            seen_seq.add(key)
            if deduped and deduped[-1]["uic"] == row["uic"]:
                continue
            deduped.append(row)
        for i in range(len(deduped) - 1):
            a = deduped[i]
            b = deduped[i + 1]
            ua = a["uic"]
            ub = b["uic"]
            if ua == ub:
                continue

            pk_distance = abs(float(b["pk_km"]) - float(a["pk_km"]))
            if pk_distance > 0:
                base_minutes = estimate_minutes(pk_distance)
            else:
                la, loa = a.get("lat"), a.get("lon")
                lb, lob = b.get("lat"), b.get("lon")
                if la is not None and loa is not None and lb is not None and lob is not None:
                    base_minutes = estimate_minutes(haversine_km(float(la), float(loa), float(lb), float(lob)))
                else:
                    base_minutes = MIN_EDGE_MINUTES

            for src, dst in ((ua, ub), (ub, ua)):
                gtfs_w = gtfs_lookup.get((src, dst))
                if gtfs_w is None:
                    gtfs_w = gtfs_lookup.get((dst, src))
                w = min(base_minutes, gtfs_w) if gtfs_w is not None else base_minutes
                key = (src, dst)
                if key not in edges or w < edges[key]:
                    edges[key] = w

    city_candidates = (
        df.dropna(subset=["lat", "lon"])
        .drop_duplicates(subset=["uic"])
        .to_dict(orient="records")
    )
    by_commune: dict[str, list[dict]] = {}
    for row in city_candidates:
        commune = str(row.get("commune", "")).strip().lower()
        if not commune:
            continue
        by_commune.setdefault(commune, []).append(row)

    for stations in by_commune.values():
        n = len(stations)
        for i in range(n):
            a = stations[i]
            for j in range(i + 1, n):
                b = stations[j]
                ua = a["uic"]
                ub = b["uic"]
                if ua == ub:
                    continue
                dist = haversine_km(float(a["lat"]), float(a["lon"]), float(b["lat"]), float(b["lon"]))
                if dist > TRANSFER_MAX_DISTANCE_KM:
                    continue
                transfer_minutes = estimate_transfer_minutes(dist)
                key_ab = (ua, ub)
                key_ba = (ub, ua)
                if key_ab not in edges or transfer_minutes < edges[key_ab]:
                    edges[key_ab] = transfer_minutes
                if key_ba not in edges or transfer_minutes < edges[key_ba]:
                    edges[key_ba] = transfer_minutes

    out_rows = []
    for (src, dst), w in edges.items():
        out_rows.append(
            {
                "source_uic": src,
                "target_uic": dst,
                "weight_minutes": round(float(w), 3),
                "source_name": uic_to_name.get(src, src),
                "target_name": uic_to_name.get(dst, dst),
            }
        )

    out_df = pd.DataFrame(out_rows)
    out_df = out_df.sort_values(["source_uic", "target_uic"]).reset_index(drop=True)
    return out_df


def main() -> None:
    out_df = build_edges()
    OUTPUT_INFRA_DURATIONS.parent.mkdir(parents=True, exist_ok=True)
    out_df.to_csv(OUTPUT_INFRA_DURATIONS, index=False)
    print(f"saved={OUTPUT_INFRA_DURATIONS}")
    print(f"edges={len(out_df)}")
    print(f"nodes={len(set(out_df['source_uic']).union(set(out_df['target_uic'])))}")


if __name__ == "__main__":
    main()
