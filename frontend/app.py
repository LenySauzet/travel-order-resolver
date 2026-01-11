import streamlit as st
import requests
from datetime import datetime, timedelta
from annotated_text import annotated_text
import time

API_BASE_URL = "http://localhost:8000/api/v1"

st.set_page_config(
    page_title="Travel Order Resolver",
    page_icon="./public/favicon.svg",
    layout="centered",
)

st.logo(
    "./public/logo.svg",
    size="large",
    link="https://www.sncf.com/fr/sncf-connect",
)
        
def transcribe_audio(audio_bytes: bytes) -> str:
    """Send audio to the API for transcription."""
    try:
        response = requests.post(
            f"{API_BASE_URL}/transcribe",
            files={"file": ("audio.wav", audio_bytes, "audio/wav")},
        )
        response.raise_for_status()
        return response.json().get("text", "")
    except requests.exceptions.RequestException as e:
        st.toast(f"❌ Erreur transcription")
        return ""
    
def identify_travel_order(text: str) -> dict | None:
    """Identify the travel order entities (departure, destination, time)."""
    try:
        response = requests.get(
            f"{API_BASE_URL}/identify-travel-order",
            params={"text": text},
        )
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        st.toast(f"❌ Erreur identification des entités")
        return None
    
def search_travel_order(validated_travel_order: dict):
    """Search for the travel order."""
    try:
        response = requests.get(
            f"{API_BASE_URL}/search-travel-order",
            params={"departure": validated_travel_order["departure"], "destination": validated_travel_order["destination"], "time": validated_travel_order["time"]},
        )
        response.raise_for_status()
        # return response.json()
        return "résultat de la recherche"
    except requests.exceptions.RequestException as e:
        st.toast(f"❌ Erreur recherche des trajets")
        return None

@st.dialog("Recherche")
def travel_order_validation_form_dialog(identified_departure: str, identified_destination: str, identified_time: datetime):
    with st.form("travel_order_validation_form"):
        departure = st.selectbox(
            "Départ",
            [identified_departure,"Lille", "Paris", "Lyon"],
            index=0,
            placeholder="Sélectionnez un départ",
            accept_new_options=True,
        )

        destination = st.selectbox(
            "Destination",
            [identified_destination, "Lille", "Paris", "Lyon"],
            index=0,
            placeholder="Sélectionnez une destination",
            accept_new_options=True,
        )

        time = st.datetime_input(
            "Heure",
            # value=identified_time,
            min_value=datetime.now(),
            max_value=datetime.now() + timedelta(days=30),
        )

        submit_button = st.form_submit_button("Rechercher")
        if submit_button:
            return {"departure": departure, "destination": destination, "time": time}
        
def search_result_card(departure: str, destination: str, key: str):
    with st.container(border=True):
        col1, col2 = st.columns([3, 2], vertical_alignment="bottom")
        with col1:
            st.subheader("🚄 07:16 → 08:10 | 54 min")
            st.write(f"Départ : **{departure}**")
            st.write(f"Arrivée : **{destination}**")
            st.write("Train : TGV Inoui &nbsp;|&nbsp; 2ème Classe", unsafe_allow_html=True)
        with col2:
            st.warning("1 place restante au tarif affiché", icon="⚠️")
            if st.button(
                "Réserver", 
                use_container_width=True, 
                type="primary",
                key=key
            ):
                st.switch_page("pages/itinerary.py")

def swap_departure_destination():
    """Inverse les valeurs de départ et de destination."""
    if st.session_state.search_results:
        departure = st.session_state.search_results["departure"]
        destination = st.session_state.search_results["destination"]
        st.session_state.search_results["departure"] = destination
        st.session_state.search_results["destination"] = departure

def main():
    st.title("Bonjour !")

    input_container = st.container()
    messages_container = st.container()

    if "messages" not in st.session_state:
        st.session_state.messages = []
    
    if "search_results" not in st.session_state:
        st.session_state.search_results = None

    for message in st.session_state.messages:
        with messages_container.chat_message(message["role"]):
            st.write(message["content"])

    prompt = input_container.chat_input(
        "Où souhaitez-vous aller ?",
        accept_audio=True,
    )

    if prompt:
        if prompt.text:
            st.session_state.messages = [{"role": "user", "content": prompt.text}]
            st.session_state.search_results = {
                "departure": "Paris",
                "destination": "Lyon",
                "show_status": True
            }
            st.rerun()

    if st.session_state.search_results:
        with messages_container.chat_message("ai"):
            if st.session_state.search_results.get("show_status"):
                with st.status("Réflexion", expanded=True) as status:
                    start_time = time.perf_counter()

                    st.write("Identification de la demande")
                    time.sleep(1)
                    st.write("Recherche des trajets disponibles")
                    time.sleep(1)

                    end_time = time.perf_counter()
                    elapsed = end_time - start_time
                    seconds = int(elapsed % 60)

                    status.update(
                        label=f"Réflexion : {seconds}s", state="complete", expanded=False
                    )
                st.session_state.search_results["show_status"] = False

            departure = st.session_state.search_results["departure"]
            destination = st.session_state.search_results["destination"]

            with st.container(border=True):
                col1, col2, col3 = st.columns([3, 3, 2], vertical_alignment="bottom")
                with col1:
                    st.text_input("Départ", value=departure)
                with col2:
                    st.text_input("Destination", value=destination)
                with col3:
                    st.button(label="", icon=":material/compare_arrows:", use_container_width=True, on_click=swap_departure_destination)
                
                st.datetime_input(
                    "Date",
                    value=datetime.now(),
                    min_value=datetime.now(),
                    max_value=datetime.now() + timedelta(days=30),
                )

            for i in range(3):
                search_result_card(departure, destination, f"search_result_{i}")



        #         identified_travel_order = identify_travel_order(prompt.text)

        #         if identified_travel_order:
        #             annotated_text(
        #                 "This ",
        #                 ("is", "verb"),
        #                 " some ",
        #                 ("annotated", "adj"),
        #                 ("text", "noun"),
        #                 " for those of ",
        #                 ("you", "pronoun"),
        #                 " who ",
        #                 ("like", "verb"),
        #                 " this sort of ",
        #                 ("thing", "noun"),
        #                 "."
        #             )
        #             validated_travel_order = travel_order_validation_form_dialog(identified_travel_order["departure"], identified_travel_order["destination"], identified_travel_order["time"])

        #             if validated_travel_order:
        #                 search_results = search_travel_order(validated_travel_order)

        # if prompt.audio:
        #     with messages_container.chat_message("user"):
        #         with st.spinner("🎙️ Transcribing..."):
        #             audio_bytes = prompt.audio.getvalue()
        #             transcription = transcribe_audio(audio_bytes)

        #         if transcription:
        #             st.session_state.messages.append({"role": "user", "content": transcription})
        #             st.write(transcription)
        #         else:
        #             st.warning("⚠️ No text detected in the audio")


if __name__ == "__main__":
    main()
