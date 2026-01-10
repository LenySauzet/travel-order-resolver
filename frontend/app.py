import streamlit as st
from faster_whisper import WhisperModel
import tempfile
import os


st.set_page_config(
    page_title="Travel Order Resolver",
    page_icon="🚄",
    layout="wide",
)

@st.cache_resource
def load_whisper_model():
    """ Load the Whisper model once and cache it."""
    return WhisperModel("small", device="cpu", compute_type="int8")


def transcribe_audio(audio_bytes: bytes) -> str:
    """ Transcribe the audio to text with faster_whisper."""
    model = load_whisper_model()
    
    # Save the audio temporarily because faster_whisper needs a file
    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp_file:
        tmp_file.write(audio_bytes)
        tmp_path = tmp_file.name
    
    try:
        segments, info = model.transcribe(tmp_path, language="fr")
        transcription = " ".join([segment.text for segment in segments])
        return transcription.strip()
    finally:
        os.unlink(tmp_path)


def main():
    st.title("🚄 Travel Order Resolver")
    st.caption("This repository contains an **NLP-powered system** designed to process natural language trip requests in French, extracting departure and destination points to generate optimal train itineraries using pathfinding algorithms.")
    
    if "messages" not in st.session_state:
        st.session_state.messages = []
    
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.write(message["content"])
    
    prompt = st.chat_input(
        "Say or record something",
        accept_audio=True,
    )
    
    if prompt:
        # Text processing
        if prompt.text:
            st.session_state.messages.append({"role": "user", "content": prompt.text})
            with st.chat_message("user"):
                st.write(prompt.text)
        
        # Audio processing
        if prompt.audio:
            with st.chat_message("user"):
                with st.spinner("🎙️ Transcribing..."):
                    audio_bytes = prompt.audio.getvalue()
                    transcription = transcribe_audio(audio_bytes)
                
                if transcription:
                    st.session_state.messages.append({"role": "user", "content": {transcription}})
                else:
                    st.warning("⚠️ No text detected in the audio")


if __name__ == "__main__":
    main()
