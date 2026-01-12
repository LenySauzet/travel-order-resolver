"""Itinerary detail page."""

import os
from datetime import datetime

import folium
import googlemaps
import polyline
import streamlit as st
from dotenv import load_dotenv
from streamlit_folium import st_folium

from models import Journey, JourneySection

load_dotenv()

GOOGLE_MAPS_API_KEY = os.getenv("GOOGLE_MAPS_API_KEY", "")

st.set_page_config(
    page_title="Votre trajet",
    page_icon="./public/favicon.svg",
    layout="centered"
)

st.logo(
    "./public/logo.svg",
    size="large",
    link="https://www.sncf.com/fr/sncf-connect",
)

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


def get_transport_icon(commercial_mode: str | None, section_type: str) -> str:
    """Return emoji based on transport type."""
    if section_type == "street_network":
        return "🚶"
    if section_type == "transfer":
        return "🔄"
    if section_type == "waiting":
        return "⏳"
    
    mode = (commercial_mode or "").lower()
    if "tgv" in mode or "intercités" in mode:
        return "🚄"
    if "ter" in mode:
        return "🚃"
    if "rer" in mode:
        return "🚇"
    if "metro" in mode:
        return "🚇"
    if "bus" in mode:
        return "🚌"
    if "tram" in mode:
        return "🚊"
    return "🚆"


def get_section_color(section_type: str) -> str:
    """Return badge color based on section type."""
    colors = {
        "public_transport": "blue",
        "street_network": "green",
        "transfer": "orange",
        "waiting": "gray",
    }
    return colors.get(section_type, "gray")

def render_section_card(section: JourneySection, index: int) -> None:
    """Render a section card."""
    if section.type == "waiting":
        return
    
    icon = get_transport_icon(section.commercial_mode, section.type)
    color = get_section_color(section.type)
    dep_time = format_time(section.departure_datetime)
    arr_time = format_time(section.arrival_datetime)
    duration = format_duration(section.duration)
    
    with st.container(border=True):
        col1, col2 = st.columns([1, 3])
        
        with col1:
            st.badge(dep_time, icon=":material/pace:", color=color) # type: ignore
            if arr_time and arr_time != dep_time:
                st.caption(f"→ {arr_time}")
        
        with col2:
            if section.type == "street_network":
                mode_label = "Marche à pied" if section.mode == "walking" else (section.mode or "").capitalize()
                st.subheader(f"{icon} {mode_label}")
                st.caption(f"{section.from_place.name} → {section.to_place.name}")
                st.caption(f"⏱️ {duration}")
                
            elif section.type == "public_transport":
                transport_mode = section.commercial_mode or "Train"
                line_info = section.line_name or section.line_code or ""
                
                st.subheader(f"{section.from_place.name}")
                st.info(
                    f"{icon} **{transport_mode}** {line_info} - {duration}",
                    icon=":material/train:"
                )
                
                if section.direction:
                    st.caption(f"➡️ Direction: {section.direction}")
                
                st.caption(f"📍 Arrivée: **{section.to_place.name}**")
                
            elif section.type == "transfer":
                st.subheader(f"{icon} Correspondance")
                st.caption(f"{section.from_place.name} → {section.to_place.name}")
                st.caption(f"⏱️ {duration}")


def render_journey_summary(journey: Journey) -> None:
    """Render journey summary header."""
    dep_time = format_time(journey.departure_datetime)
    arr_time = format_time(journey.arrival_datetime)
    duration = format_duration(journey.duration)
    
    # Get first and last station
    first_station = ""
    last_station = ""
    for section in journey.sections:
        if section.type == "public_transport":
            if not first_station:
                first_station = section.from_place.name
            last_station = section.to_place.name
    
    st.title(f"🚆 {first_station} → {last_station}")
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Départ", dep_time)
    with col2:
        st.metric("Arrivée", arr_time)
    with col3:
        st.metric("Durée", duration)
    
    # Additional info
    info_parts = []
    if journey.nb_transfers > 0:
        info_parts.append(f"🔄 {journey.nb_transfers} correspondance(s)")
    if journey.walking_duration > 0:
        info_parts.append(f"🚶 {format_duration(journey.walking_duration)} de marche")
    if journey.co2_emission:
        info_parts.append(f"🌱 {journey.co2_emission:.0f}g CO2")
    
    if info_parts:
        st.caption(" | ".join(info_parts))


# Theme colors from config.toml (dark theme)
THEME_COLORS = {
    "primary": "#437991",
    "red": "#DB735E",
    "orange": "#f2be69",
    "yellow": "#f7e05c",
    "blue": "#b7b6ff",
    "green": "#6ccb70",
    "violet": "#e39dfd",
}


def get_transport_color(section_type: str, commercial_mode: str | None) -> str:
    """Return color for route based on transport type, matching app theme."""
    if section_type == "street_network":
        return THEME_COLORS["green"]  # Green for walking
    if section_type == "transfer":
        return THEME_COLORS["orange"]  # Orange for transfer
    if section_type == "waiting":
        return "#6b7280"  # Gray for waiting
    
    mode = (commercial_mode or "").lower()
    if "tgv" in mode or "intercités" in mode:
        return THEME_COLORS["red"]  # Red for TGV/Intercités
    if "ter" in mode:
        return THEME_COLORS["blue"]  # Blue for TER
    if "rer" in mode:
        return THEME_COLORS["violet"]  # Violet for RER
    if "metro" in mode:
        return THEME_COLORS["primary"]  # Primary for Metro
    if "bus" in mode:
        return THEME_COLORS["green"]  # Green for Bus
    if "tram" in mode:
        return THEME_COLORS["yellow"]  # Yellow for Tram
    return THEME_COLORS["primary"]  # Default primary for train


def get_google_directions(
    gmaps: googlemaps.Client,
    origin: tuple[float, float],
    destination: tuple[float, float],
    mode: str = "walking"
) -> list[tuple[float, float]] | None:
    """Get route polyline from Google Maps Directions API."""
    try:
        result = gmaps.directions(
            origin={"lat": origin[0], "lng": origin[1]},
            destination={"lat": destination[0], "lng": destination[1]},
            mode=mode,
        )
        if result and result[0].get("overview_polyline"):
            encoded = result[0]["overview_polyline"]["points"]
            return polyline.decode(encoded)
    except Exception:
        pass
    return None


def render_map(journey: Journey) -> None:
    """Render journey map with Google Maps directions."""
    # Collect all coordinates for bounds
    all_coords: list[tuple[float, float]] = []
    sections_data: list[dict] = []
    
    for section in journey.sections:
        if section.type == "waiting":
            continue
            
        from_coord = section.from_place.coord
        to_coord = section.to_place.coord
        
        if from_coord and to_coord:
            # Navitia returns (lon, lat), we need (lat, lon)
            from_latlon = (from_coord[1], from_coord[0])
            to_latlon = (to_coord[1], to_coord[0])
            
            all_coords.append(from_latlon)
            all_coords.append(to_latlon)
            
            sections_data.append({
                "from": from_latlon,
                "to": to_latlon,
                "type": section.type,
                "mode": section.mode,
                "commercial_mode": section.commercial_mode,
                "from_name": section.from_place.name,
                "to_name": section.to_place.name,
            })
    
    if not all_coords:
        st.info("Aucune donnée de localisation disponible pour ce trajet.")
        return
    
    # Calculate map center
    center_lat = sum(c[0] for c in all_coords) / len(all_coords)
    center_lon = sum(c[1] for c in all_coords) / len(all_coords)
    
    # Hide map attribution with CSS
    st.markdown(
        """<style>.leaflet-control-attribution{display:none!important}</style>""",
        unsafe_allow_html=True,
    )
    
    # Create folium map with dark theme (no attribution)
    m = folium.Map(
        location=[center_lat, center_lon],
        zoom_start=6,
        tiles=None,
        attr=" ",
    )
    # Add dark tile layer without attribution
    folium.TileLayer(
        tiles="https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png",
        attr=" ",
        name="Dark",
    ).add_to(m)
    
    # Initialize Google Maps client if API key available
    gmaps_client = None
    if GOOGLE_MAPS_API_KEY:
        try:
            gmaps_client = googlemaps.Client(key=GOOGLE_MAPS_API_KEY)
        except Exception:
            pass
    
    # Add routes for each section
    for section_data in sections_data:
        color = get_transport_color(section_data["type"], section_data["commercial_mode"])
        from_coord = section_data["from"]
        to_coord = section_data["to"]
        
        route_coords = None
        section_type = section_data["type"]
        
        # Use Google Maps for walking segments (street_network and transfer)
        if gmaps_client and section_type in ("street_network", "transfer"):
            mode = section_data["mode"]
            google_mode = "walking" if mode in ("walking", None) else "driving"
            route_coords = get_google_directions(gmaps_client, from_coord, to_coord, google_mode)
        
        # Try Google transit for public transport if no route found
        if gmaps_client and section_type == "public_transport" and route_coords is None:
            route_coords = get_google_directions(gmaps_client, from_coord, to_coord, "transit")
        
        # Fallback to straight line if no Google route
        if route_coords is None:
            route_coords = [from_coord, to_coord]
        
        # Add polyline with themed styling
        folium.PolyLine(
            locations=route_coords,
            color=color,
            weight=5,
            opacity=0.9,
            popup=f"{section_data['from_name']} → {section_data['to_name']}",
        ).add_to(m)
    
    # Add markers for stations with custom colors
    added_markers: set[tuple[float, float]] = set()
    for i, section_data in enumerate(sections_data):
        for coord, name, is_start in [
            (section_data["from"], section_data["from_name"], True),
            (section_data["to"], section_data["to_name"], False),
        ]:
            if coord not in added_markers:
                added_markers.add(coord)
                # Determine marker color
                if is_start and i == 0:
                    icon_color = "green"  # Start
                elif not is_start and i == len(sections_data) - 1:
                    icon_color = "red"  # End
                else:
                    icon_color = "lightblue"  # Intermediate
                
                folium.Marker(
                    location=coord,
                    popup=name,
                    tooltip=name,
                    icon=folium.Icon(color=icon_color, icon="train", prefix="fa"),
                ).add_to(m)
    
    # Fit bounds to show all markers
    if len(all_coords) >= 2:
        m.fit_bounds(all_coords)
    
    # Render map
    st_folium(m, use_container_width=True, height=400)


def render_sections_timeline(journey: Journey) -> None:
    """Render sections as a timeline."""
    # Filter out waiting sections
    visible_sections = [s for s in journey.sections if s.type != "waiting"]
    
    # Count public transport sections for stops
    pt_sections = [s for s in visible_sections if s.type == "public_transport"]
    
    for i, section in enumerate(visible_sections):
        render_section_card(section, i)
    
    # Show expandable stops if multiple PT sections
    if len(pt_sections) > 1:
        with st.expander(f"📍 {len(pt_sections)} étapes du trajet"):
            for section in pt_sections:
                st.write(f"• {section.from_place.name} → {section.to_place.name}")

def main() -> None:
    """Main entry point."""
    # Back button
    if st.button(
        "Retour à la recherche",
        type="secondary",
        icon=":material/arrow_back_ios_new:"
    ):
        st.switch_page("app.py")
    
    # Check if journey is selected
    if "selected_journey" not in st.session_state or st.session_state.selected_journey is None:
        st.warning("Aucun trajet sélectionné. Veuillez retourner à la recherche.")
        return
    
    journey: Journey = st.session_state.selected_journey
    
    # Journey summary
    render_journey_summary(journey)
    
    st.divider()
    
    # Main content
    with st.container(border=True):
        # Map
        render_map(journey)
        
        st.subheader("📋 Détail du trajet")
        
        # Sections timeline
        render_sections_timeline(journey)
        
        st.divider()
        
        # Action button
        if st.button(
            "🎫 Acheter votre billet",
            use_container_width=True,
            type="primary"
        ):
            st.toast("Billet acheté avec succès", icon=":material/check_circle:")
        


if __name__ == "__main__":
    main()
else:
    main()
