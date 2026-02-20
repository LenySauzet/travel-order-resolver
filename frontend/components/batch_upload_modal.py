import csv
from io import StringIO
from typing import Callable

import streamlit as st

from api import get_best_routes, identify_travel_order
from models import Station


RESULTS_COLUMN = "Résultat"


def parse_csv_sentences(text: str) -> list[str]:
    values: list[str] = []
    for row in csv.reader(StringIO(text)):
        cleaned = next((cell.strip() for cell in row if cell and cell.strip()), "")
        if cleaned:
            values.append(cleaned)
    if values and values[0].lower() in {"sentence", "sentences", "phrase", "phrases", "text", "texte"}:
        return values[1:]
    return values


def parse_batch_sentences(file_content: bytes, filename: str) -> list[str]:
    text = file_content.decode("utf-8", errors="ignore")
    if filename.lower().endswith(".csv"):
        return parse_csv_sentences(text)
    return [line.strip() for line in text.splitlines() if line.strip()]


def run_batch_routing(
    sentences: list[str],
    user_coords: tuple[float, float] | None,
    stations: list[Station],
    get_station_idx: Callable[[int | None], int | None],
) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for sentence in sentences:
        result = identify_travel_order(sentence, user_coords)
        if not result or result.departure_id is None or result.destination_id is None:
            rows.append({"Sentence": sentence, RESULTS_COLUMN: "Demande non reconnue"})
            continue
        dep_idx = get_station_idx(result.departure_id)
        dest_idx = get_station_idx(result.destination_id)
        dep_name = stations[dep_idx].name if dep_idx is not None else "Inconnu"
        dest_name = stations[dest_idx].name if dest_idx is not None else "Inconnu"
        routes = get_best_routes(result.departure_id, result.destination_id, limit=1)
        if not routes or routes.error or not routes.routes:
            error_text = routes.error if routes and routes.error else "Aucun trajet trouvé"
            rows.append({"Sentence": sentence, RESULTS_COLUMN: f"{dep_name} → {dest_name} | {error_text}"})
            continue
        rows.append({"Sentence": sentence, RESULTS_COLUMN: f"{dep_name} → {dest_name}"})
    return rows


@st.dialog("Batch upload", width="large")
def render_batch_upload_modal(
    routing_mode: str,
    user_coords: tuple[float, float] | None,
    stations: list[Station],
    get_station_idx: Callable[[int | None], int | None],
) -> None:
    uploaded_file = st.file_uploader(
        "Importer un fichier de phrases (.txt ou .csv)",
        type=["txt", "csv"],
        accept_multiple_files=False,
    )
    if not uploaded_file:
        return
    signature = f"{uploaded_file.name}:{uploaded_file.size}:{routing_mode}"
    if st.session_state.batch_upload_signature != signature:
        sentences = parse_batch_sentences(uploaded_file.getvalue(), uploaded_file.name)
        if not sentences:
            st.session_state.batch_upload_results = []
            st.session_state.batch_upload_signature = signature
        else:
            with st.spinner("Analyse des phrases..."):
                st.session_state.batch_upload_results = run_batch_routing(
                    sentences,
                    user_coords,
                    stations,
                    get_station_idx,
                )
                st.session_state.batch_upload_signature = signature
    if not st.session_state.batch_upload_results:
        st.info("Aucun résultat à afficher.")
        return
    st.dataframe(st.session_state.batch_upload_results, use_container_width=True, hide_index=True)


def render_batch_upload_trigger(
    routing_mode: str,
    user_coords: tuple[float, float] | None,
    stations: list[Station],
    get_station_idx: Callable[[int | None], int | None],
) -> None:
    if st.button(
        "",
        icon=":material/upload_file:",
        key="open_batch_upload",
        type="secondary",
        help="Batch upload",
    ):
        render_batch_upload_modal(routing_mode, user_coords, stations, get_station_idx)
