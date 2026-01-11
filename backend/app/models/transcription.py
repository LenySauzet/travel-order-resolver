from pydantic import BaseModel


class TranscriptionResponse(BaseModel):
    """Response model for audio transcription."""
    text: str


class TranscriptionConfig(BaseModel):
    """Configuration for the Whisper model."""
    model_name: str = "large-v3"
    device: str = "cpu"
    compute_type: str = "int8"
    language: str = "fr"
    beam_size: int = 1
    initial_prompt: str = "Je suis un assistant de réservation de billets de train. Je suis capable de transcrire des requêtes de voyage en texte."
