from typing import Callable

import streamlit as st


@st.dialog("Paramètres", width="small")
def render_settings_modal(
    current_mode: str,
    apply_mode: Callable[[str], bool],
    ner_models: dict[str, str],
) -> None:
    shortcuts_enabled = current_mode == "shortcuts"
    with st.form("routing_settings_form"):
        st.write("Mode de routage")
        toggled = st.toggle("Inclure les directs", value=shortcuts_enabled)
        target_mode = "shortcuts" if toggled else "no_shortcuts"
        st.caption("Directs activés" if target_mode == "shortcuts" else "Directs désactivés")

        st.divider()

        st.write("Moteur de routage")
        routing_engines = {
            "dijkstra": "Dijkstra (CSV)",
            "neo4j_fastest": "Neo4j (Plus rapide)",
            "neo4j_fewest": "Neo4j (Moins d'arrêts)",
        }
        engine_keys = list(routing_engines.keys())
        engine_labels = list(routing_engines.values())
        current_engine = st.session_state.get("routing_engine", "dijkstra")
        current_engine_idx = engine_keys.index(current_engine) if current_engine in engine_keys else 0
        selected_engine_label = st.selectbox(
            "Moteur de routage",
            options=engine_labels,
            index=current_engine_idx,
            label_visibility="collapsed",
        )
        selected_engine_key = engine_keys[engine_labels.index(selected_engine_label)] if selected_engine_label else engine_keys[0]

        st.divider()

        st.write("Modèle NER")
        model_keys = list(ner_models.keys())
        model_labels = list(ner_models.values())
        current_key = st.session_state.get("ner_model", "spacy")
        current_idx = model_keys.index(current_key) if current_key in model_keys else 0
        selected_label = st.selectbox(
            "Modèle de reconnaissance",
            options=model_labels,
            index=current_idx,
            label_visibility="collapsed",
        )
        selected_key = model_keys[model_labels.index(selected_label)] if selected_label else model_keys[0]

        submitted = st.form_submit_button("Appliquer", use_container_width=True)
    if submitted:
        if target_mode != current_mode:
            apply_mode(target_mode)
        st.session_state.ner_model = selected_key
        st.session_state.routing_engine = selected_engine_key
        st.rerun()


def render_settings_trigger(
    current_mode: str,
    apply_mode: Callable[[str], bool],
    ner_models: dict[str, str],
) -> None:
    with st.container(key="settings_trigger"):
        if st.button(
            "",
            icon=":material/settings:",
            key="open_settings_modal",
            type="secondary",
            help="Ouvrir les paramètres",
        ):
            render_settings_modal(current_mode, apply_mode, ner_models)
