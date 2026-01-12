"""Travel Order Resolver - Streamlit Frontend."""

import time
from datetime import datetime, timedelta

import streamlit as st
from streamlit_js_eval import get_geolocation

from api import get_stations, identify_travel_order, search_journeys, transcribe_audio
from components.ItineraryCard import ItineraryCard
from models import Journey, Station

# =============================================================================
# Configuration
# =============================================================================

st.set_page_config(
    page_title="Travel Order Resolver",
    page_icon="./public/favicon.svg",
    layout="centered",
)

st.markdown(
    """<style>iframe[title="streamlit_js_eval.streamlit_js_eval"]{display:none}</style>""",
    unsafe_allow_html=True,
)

st.logo("./public/logo.svg", size="large", link="https://www.sncf.com/fr/sncf-connect")

# =============================================================================
# Constants
# =============================================================================

SESSION_DEFAULTS: dict[str, object] = {
    "messages": [],
    "show_form": False,
    "processing": False,
    "searching": False,
    "user_coords": None,
    "journeys": None,
    "search_error": None,
    "process_result": None,  # Stores last processing result for display
    # Persistent form values (survive page navigation)
    "saved_dep_idx": None,
    "saved_dest_idx": None,
    "saved_datetime": None,
}


# =============================================================================
# Session State
# =============================================================================


def init_session_state() -> None:
    """Initialize session state with default values."""
    if "stations" not in st.session_state:
        st.session_state.stations = get_stations()
        # Pre-compute ID -> index lookup for O(1) access
        st.session_state._station_lookup = {
            s.id: i for i, s in enumerate(st.session_state.stations)
        }

    for key, default in SESSION_DEFAULTS.items():
        if key not in st.session_state:
            st.session_state[key] = default if not isinstance(default, list) else []


def get_station_idx(station_id: int | None) -> int | None:
    """Return station index by ID (O(1) lookup)."""
    if station_id is None:
        return None
    return st.session_state._station_lookup.get(station_id)


def reset_search_results() -> None:
    """Reset search results."""
    st.session_state.journeys = None
    st.session_state.search_error = None


# =============================================================================
# Callbacks (called before rerun)
# =============================================================================


def on_swap_stations() -> None:
    """Swap departure and destination stations and trigger search."""
    dep = st.session_state.get("_dep_select")
    dest = st.session_state.get("_dest_select")
    st.session_state["_dep_select"] = dest
    st.session_state["_dest_select"] = dep
    # Save to persistent keys
    st.session_state.saved_dep_idx = dest
    st.session_state.saved_dest_idx = dep
    st.session_state.searching = True


def on_search_param_change() -> None:
    """Callback when any search parameter changes."""
    # Save current values to persistent keys
    st.session_state.saved_dep_idx = st.session_state.get("_dep_select")
    st.session_state.saved_dest_idx = st.session_state.get("_dest_select")
    st.session_state.saved_datetime = st.session_state.get("_datetime_select")
    st.session_state.searching = True


def on_process_request(text: str) -> None:
    """Process a new user request."""
    st.session_state.processing = True
    st.session_state.show_form = False
    st.session_state.process_result = None
    st.session_state.messages = [{"role": "user", "content": text}]
    reset_search_results()


# =============================================================================
# Actions
# =============================================================================


def update_user_coords() -> None:
    """Update user coordinates via geolocation."""
    if loc := get_geolocation():
        if coords := loc.get("coords"):
            st.session_state.user_coords = (coords["latitude"], coords["longitude"])


def execute_search() -> float:
    """Execute journey search. Returns elapsed time."""
    start = time.perf_counter()
    reset_search_results()

    dep_idx = st.session_state.get("_dep_select")
    dest_idx = st.session_state.get("_dest_select")

    if dep_idx is None or dest_idx is None:
        return time.perf_counter() - start

    stations: list[Station] = st.session_state.stations
    dt_value = st.session_state.get("_datetime_select")
    dt_iso: str | None = None
    if dt_value is not None and hasattr(dt_value, "isoformat"):
        dt_iso = dt_value.isoformat()
    elif isinstance(dt_value, str):
        dt_iso = dt_value

    if result := search_journeys(stations[dep_idx].id, stations[dest_idx].id, dt_iso):
        if result.error:
            st.session_state.search_error = result.error
        else:
            st.session_state.journeys = result.journeys

    return time.perf_counter() - start


def process_identification() -> tuple[bool, float]:
    """Identify request and update state. Returns (success, elapsed_time)."""
    start = time.perf_counter()
    
    result = identify_travel_order(
        st.session_state.messages[-1]["content"],
        st.session_state.user_coords,
    )

    if not result:
        return False, time.perf_counter() - start

    dep_idx = get_station_idx(result.departure_id)
    dest_idx = get_station_idx(result.destination_id)
    
    # Convert ISO string to datetime for the widget
    dt_value = None
    if result.datetime_iso:
        try:
            dt_value = datetime.fromisoformat(result.datetime_iso)
        except ValueError:
            pass
    
    # Store in widget keys for selectbox/datetime_input
    st.session_state["_dep_select"] = dep_idx
    st.session_state["_dest_select"] = dest_idx
    st.session_state["_datetime_select"] = dt_value
    
    # Save to persistent keys (survive page navigation)
    st.session_state.saved_dep_idx = dep_idx
    st.session_state.saved_dest_idx = dest_idx
    st.session_state.saved_datetime = dt_value
    
    st.session_state.show_form = True
    
    return True, time.perf_counter() - start


# =============================================================================
# UI Components
# =============================================================================


def render_journeys_results() -> None:
    """Render search results using ItineraryCard component."""
    if error := st.session_state.search_error:
        st.error(f"❌ {error}")
        return

    journeys: list[Journey] | None = st.session_state.journeys
    if journeys is None:
        return

    if not journeys:
        st.warning("Aucun trajet trouvé pour cette recherche.")
        return

    st.subheader(f"🚆 {len(journeys)} trajet(s) trouvé(s)")
    for i, journey in enumerate(journeys):
        ItineraryCard(journey, f"journey_{i}")


def render_search_form() -> None:
    """Render the search form."""
    stations: list[Station] = st.session_state.stations

    # Restore saved values to widget keys if not already set
    if "_dep_select" not in st.session_state and st.session_state.saved_dep_idx is not None:
        st.session_state["_dep_select"] = st.session_state.saved_dep_idx
    if "_dest_select" not in st.session_state and st.session_state.saved_dest_idx is not None:
        st.session_state["_dest_select"] = st.session_state.saved_dest_idx
    if "_datetime_select" not in st.session_state and st.session_state.saved_datetime is not None:
        st.session_state["_datetime_select"] = st.session_state.saved_datetime

    with st.container(border=True):
        col1, col2, col3 = st.columns([3, 3, 1], vertical_alignment="bottom")

        with col1:
            st.selectbox(
                "Départ",
                options=range(len(stations)),
                format_func=lambda i: stations[i].name,
                placeholder="Sélectionner une gare",
                key="_dep_select",
                on_change=on_search_param_change,
            )

        with col2:
            st.selectbox(
                "Destination",
                options=range(len(stations)),
                format_func=lambda i: stations[i].name,
                placeholder="Sélectionner une gare",
                key="_dest_select",
                on_change=on_search_param_change,
            )

        with col3:
            st.button(
                "",
                icon=":material/compare_arrows:",
                use_container_width=True,
                on_click=on_swap_stations,
                help="Inverser",
            )

        st.datetime_input(
            "Date et heure",
            min_value=datetime.now(),
            max_value=datetime.now() + timedelta(days=30),
            key="_datetime_select",
            on_change=on_search_param_change,
        )

    # Execute search if triggered by callback
    if st.session_state.searching:
        st.session_state.searching = False
        with st.spinner("Recherche en cours"):
            execute_search()

    render_journeys_results()


def render_process_result() -> None:
    """Render the stored process result."""
    result = st.session_state.process_result
    if not result:
        return
    
    total_time = result["identification_time"] + result["search_time"]
    state = "complete" if result["success"] else "error"
    
    with st.status(f"Réflexion : {total_time:.1f}s", expanded=False, state=state):
        if result["success"]:
            st.write(f"Identification de la demande ({result['identification_time']:.1f}s)")
            st.write(f"Recherche des trajets ({result['search_time']:.1f}s)")
        else:
            st.write("Impossible d'identifier la demande")


def render_thinking_status() -> None:
    """Render the thinking status with identification and search."""
    with st.status("Réflexion", expanded=True) as status:
        # Step 1: Identification
        id_placeholder = st.empty()
        id_placeholder.write("Identification de la demande")
        success, id_time = process_identification()
        id_placeholder.write(f"Identification de la demande ({id_time:.1f}s)")
        
        search_time = 0.0
        if success:
            # Step 2: Search
            search_placeholder = st.empty()
            search_placeholder.write("Recherche des trajets")
            search_time = execute_search()
            search_placeholder.write(f"Recherche des trajets ({search_time:.1f}s)")
        else:
            st.write("Impossible d'identifier la demande")

        # Store result for persistent display
        st.session_state.process_result = {
            "success": success,
            "identification_time": id_time,
            "search_time": search_time,
        }
        
        st.session_state.processing = False
        total_time = id_time + search_time
        status.update(
            label=f"Réflexion : {total_time:.1f}s",
            state="complete" if success else "error",
            expanded=False,
        )


def render_chat() -> None:
    """Handle the chat interface."""
    input_container = st.container()
    messages_container = st.container()

    # Display existing messages
    for message in st.session_state.messages:
        with messages_container.chat_message(message["role"]):
            st.write(message["content"])

    # Handle user input
    if prompt := input_container.chat_input("Où souhaitez-vous aller ?", accept_audio=True):
        text = None

        if prompt.text:
            text = prompt.text
        elif prompt.audio:
            with st.spinner("Transcription"):
                text = transcribe_audio(prompt.audio.getvalue())
            if not text or not text.strip():
                st.warning("Aucun texte détecté dans l'audio.")
                return

        if text:
            on_process_request(text.strip())
            st.rerun()

    # Display AI response (only if we have messages)
    if st.session_state.messages:
        with messages_container.chat_message("ai"):
            if st.session_state.processing:
                render_thinking_status()
            else:
                # Show stored process result
                render_process_result()
            
            # Show form if ready
            if st.session_state.show_form:
                render_search_form()


# =============================================================================
# Main
# =============================================================================


def main() -> None:
    """Main entry point."""
    init_session_state()
    update_user_coords()

    st.title("Bonjour !")
    render_chat()


if __name__ == "__main__":
    main()
