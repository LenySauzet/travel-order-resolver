"""Itinerary card component."""

from datetime import datetime

import streamlit as st

from models import Journey, JourneySection


def format_time(dt_str: str) -> str:
    """Format Navitia datetime (YYYYMMDDTHHmmss) to HH:MM."""
    if not dt_str:
        return ""
    try:
        return datetime.strptime(dt_str, "%Y%m%dT%H%M%S").strftime("%H:%M")
    except ValueError:
        return dt_str


def format_duration(seconds: int) -> str:
    """Format duration in hours and minutes."""
    hours, remainder = divmod(seconds, 3600)
    minutes = remainder // 60
    return f"{hours}h{minutes:02d}" if hours else f"{minutes} min"


def get_transport_info(sections: list[JourneySection]) -> tuple[str, str, str]:
    """Extract main transport info from sections."""
    for section in sections:
        if section.type == "public_transport":
            mode = section.commercial_mode or "Train"
            line = section.line_name or section.line_code or ""
            icon = "🚄" if "tgv" in mode.lower() else "🚃" if "ter" in mode.lower() else "🚆"
            return icon, mode, line
    return "🚆", "Train", ""


def get_departure_destination(sections: list[JourneySection]) -> tuple[str, str]:
    """Get departure and destination names from sections."""
    departure = ""
    destination = ""
    
    for section in sections:
        if section.type == "public_transport":
            if not departure:
                departure = section.from_place.name
            destination = section.to_place.name
    
    # Fallback to first/last section
    if not departure and sections:
        departure = sections[0].from_place.name
    if not destination and sections:
        destination = sections[-1].to_place.name
    
    return departure, destination


def ItineraryCard(journey: Journey, key: str) -> None:
    """
    Display an itinerary card for a journey.
    
    Args:
        journey: The journey to display
        key: Unique key for the card
    """
    dep_time = format_time(journey.departure_datetime)
    arr_time = format_time(journey.arrival_datetime)
    duration = format_duration(journey.duration)
    
    icon, transport_mode, line_name = get_transport_info(journey.sections)
    departure, destination = get_departure_destination(journey.sections)
    
    transfers = journey.nb_transfers
    
    with st.container(border=True):
        col1, col2 = st.columns([3, 2], vertical_alignment="bottom")
        
        with col1:
            # Header with times and duration
            st.subheader(f"{icon} {dep_time} → {arr_time} | {duration}")
            
            # Departure and arrival
            st.write(f"Départ : **{departure}**")
            st.write(f"Arrivée : **{destination}**")
            
            # Transport info
            transport_info = f"{transport_mode}"
            if line_name:
                transport_info += f" {line_name}"
            if transfers > 0:
                transport_info += f" &nbsp;|&nbsp; {transfers} correspondance(s)"
            st.write(transport_info, unsafe_allow_html=True)
            
            # CO2 emission if available
            if journey.co2_emission:
                st.caption(f"🌱 {journey.co2_emission:.0f}g CO2")
        
        with col2:
            # Walking duration info
            if journey.walking_duration > 0:
                walk_duration = format_duration(journey.walking_duration)
                st.info(f"🚶 {walk_duration} de marche", icon="ℹ️")
            
            if st.button(
                "Voir le trajet",
                use_container_width=True,
                type="primary",
                key=key
            ):
                # Store selected journey in session state
                st.session_state.selected_journey = journey
                st.switch_page("pages/itinerary.py")
