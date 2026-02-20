from html import escape
from typing import Callable

import streamlit as st

from models import RouteOption


def format_duration_minutes(duration_minutes: float) -> str:
    total_minutes = max(0, int(round(duration_minutes)))
    hours, minutes = divmod(total_minutes, 60)
    if hours:
        return f"{hours}h{minutes:02d}"
    return f"{minutes} min"


def render_route_stops(stop_names: list[str]) -> None:
    visible_limit = 5
    has_more = len(stop_names) > visible_limit
    visible_stops = stop_names[: visible_limit - 1] if has_more else stop_names[:visible_limit]
    chips_html = "".join(
        f'<span class="route-stop-pill">{escape(stop_name)}</span>'
        for stop_name in visible_stops
    )
    if has_more:
        chips_html += '<span class="route-stop-dots">...</span>'
    st.markdown(
        f'<div class="route-stops-wrap"><div class="route-stops-track">{chips_html}</div></div>',
        unsafe_allow_html=True,
    )


def render_routes_results(
    routes: list[RouteOption] | None,
    route_error: str | None,
    on_select_route: Callable[[RouteOption], None],
) -> None:
    if route_error:
        st.error(f"❌ {route_error}")
        return
    if routes is None:
        return
    if not routes:
        st.warning("Aucun trajet trouvé pour cette recherche.")
        return
    st.subheader(f"🚆 {len(routes)} meilleur(s) trajet(s)")
    for i, route in enumerate(routes):
        if not route.path:
            continue
        departure = route.path[0].name
        destination = route.path[-1].name
        stop_names = [step.name for step in route.path]
        with st.container(border=True):
            st.write(
                f"**Option {i + 1}** - {format_duration_minutes(route.duration_minutes)}"
            )
            st.caption(f"{departure} → {destination}")
            st.caption(f"{len(route.path)} étape(s)")
            render_route_stops(stop_names)
            if st.button(
                "Voir l'itinéraire",
                key=f"route_option_{i}",
                type="primary",
                use_container_width=True,
            ):
                on_select_route(route)
