import streamlit as st

st.set_page_config(page_title="Votre trajet", page_icon="./public/favicon.svg", layout="centered")

st.logo(
    "./public/logo.svg",
    size="large",
    link="https://www.sncf.com/fr/sncf-connect",
)

def itinerary_card():
    with st.container(border=True):
        col1, col2 = st.columns([1, 2])
        with col1:
            st.badge("05:44", icon=":material/pace:", color="violet")
            st.subheader("Béziers")
            st.caption("Accès plein pied ou par ascenseur")
        # with col2:
            # st.warning("Travaux prévues entre les gares de Béziers et de Lunel", icon="⚠️")
        st.info("Train lio **876532** - train moyen", icon=":material/train:")

if st.button("Revenir à la page de recherche", type="secondary", icon=":material/arrow_back_ios_new:"):
    st.switch_page("app.py")

with st.container(border=True):
    st.map()
    st.badge("Durée **47 min**", icon=":material/timelapse:", color="blue")

    col1, col2 = st.columns(2)

    itinerary_card()

    with st.expander("3 arrêts"):
        itinerary_card()
        itinerary_card()
        itinerary_card()

    itinerary_card()

    st.button("Acheter votre billet de train", use_container_width=True, type="primary")