"""Itinerary detail page."""

import folium
import streamlit as st
from streamlit_folium import st_folium

from models import RouteOption

st.set_page_config(
    page_title="Votre trajet",
    page_icon="./public/favicon.svg",
    layout="centered",
)

st.logo(
    "./public/logo.svg",
    size="large",
    link="https://www.sncf.com/fr/sncf-connect",
)


def format_duration_minutes(duration_minutes: float) -> str:
    total_minutes = max(0, int(round(duration_minutes)))
    hours, minutes = divmod(total_minutes, 60)
    if hours:
        return f"{hours}h{minutes:02d}"
    return f"{minutes} min"


def get_route_coords(route: RouteOption) -> list[tuple[float, float]]:
    coords: list[tuple[float, float]] = []
    for step in route.path:
        if step.lat is None or step.lon is None:
            continue
        coords.append((step.lat, step.lon))
    return coords


def render_map(route: RouteOption) -> None:
    coords = get_route_coords(route)
    if not coords:
        st.info("Aucune coordonnée disponible pour afficher la carte.")
        return

    center_lat = sum(lat for lat, _ in coords) / len(coords)
    center_lon = sum(lon for _, lon in coords) / len(coords)
    m = folium.Map(
        location=[center_lat, center_lon],
        zoom_start=6,
        tiles="cartodbpositron",
    )

    if len(coords) >= 2:
        folium.PolyLine(
            locations=coords,
            color="#437991",
            weight=6,
            opacity=0.9,
        ).add_to(m)

    for idx, step in enumerate(route.path):
        if step.lat is None or step.lon is None:
            continue
        if idx == 0:
            marker_color = "green"
        elif idx == len(route.path) - 1:
            marker_color = "red"
        else:
            marker_color = "blue"
        folium.Marker(
            location=(step.lat, step.lon),
            popup=step.name,
            tooltip=step.name,
            icon=folium.Icon(color=marker_color, icon="train", prefix="fa"),
        ).add_to(m)

    if len(coords) >= 2:
        m.fit_bounds(coords)

    st_folium(m, use_container_width=True, height=450)


def render_steps(route: RouteOption) -> None:
    st.subheader("📍 Étapes")
    if not route.path:
        st.warning("Aucune étape trouvée.")
        return
    for i, step in enumerate(route.path, start=1):
        st.write(f"{i}. {step.name}")


def get_selected_route() -> RouteOption | None:
    selected = st.session_state.get("selected_dijkstra_route")
    if selected is None:
        return None
    try:
        return RouteOption.model_validate(selected)
    except Exception:
        return None


def main() -> None:
    if st.button(
        "Retour à la recherche",
        type="secondary",
        icon=":material/arrow_back_ios_new:",
    ):
        st.switch_page("app.py")

    route = get_selected_route()
    if route is None:
        st.warning("Aucun trajet sélectionné. Veuillez retourner à la recherche.")
        return
    if not route.path:
        st.warning("Le trajet sélectionné ne contient aucune étape.")
        return

    departure = route.path[0].name
    destination = route.path[-1].name
    st.title(f"🚆 {departure} → {destination}")

    col1, col2 = st.columns(2)
    with col1:
        st.metric("Durée estimée", format_duration_minutes(route.duration_minutes))
    with col2:
        st.metric("Nombre d'étapes", len(route.path))

    with st.container(border=True):
        render_map(route)
        render_steps(route)


if __name__ == "__main__":
    main()
