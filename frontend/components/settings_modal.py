from typing import Callable

import streamlit as st


@st.dialog("Paramètres", width="small")
def render_settings_modal(current_mode: str, apply_mode: Callable[[str], bool]) -> None:
    shortcuts_enabled = current_mode == "shortcuts"
    with st.form("routing_settings_form"):
        st.write("Mode de routage")
        toggled = st.toggle("Inclure les directs", value=shortcuts_enabled)
        target_mode = "shortcuts" if toggled else "no_shortcuts"
        st.caption("Directs activés" if target_mode == "shortcuts" else "Directs désactivés")
        submitted = st.form_submit_button("Appliquer", use_container_width=True)
    if submitted:
        if target_mode != current_mode:
            apply_mode(target_mode)
        st.rerun()


def render_settings_trigger(current_mode: str, apply_mode: Callable[[str], bool]) -> None:
    with st.container(key="settings_trigger"):
        if st.button(
            "",
            icon=":material/settings:",
            key="open_settings_modal",
            type="secondary",
            help="Ouvrir les paramètres",
        ):
            render_settings_modal(current_mode, apply_mode)
