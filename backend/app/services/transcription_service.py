import tempfile
import os

from faster_whisper import WhisperModel

from ..models.transcription import TranscriptionConfig, TranscriptionResponse


class TranscriptionService:
    """Service for handling audio transcription using Whisper."""

    _instance: "TranscriptionService | None" = None
    _model: WhisperModel | None = None

    def __init__(self, config: TranscriptionConfig | None = None):
        self._config = config or TranscriptionConfig()

    @classmethod
    def get_instance(cls, config: TranscriptionConfig | None = None) -> "TranscriptionService":
        """Get or create singleton instance of the service."""
        if cls._instance is None:
            cls._instance = cls(config)
        return cls._instance

    def _get_model(self) -> WhisperModel:
        """Load the Whisper model (lazy loading with caching)."""
        if TranscriptionService._model is None:
            TranscriptionService._model = WhisperModel(
                self._config.model_name,
                device=self._config.device,
                compute_type=self._config.compute_type,
            )
        return TranscriptionService._model

    def transcribe(self, audio_bytes: bytes) -> TranscriptionResponse:
        """Transcribe audio bytes to text."""
        model = self._get_model()

        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp_file:
            tmp_file.write(audio_bytes)
            tmp_path = tmp_file.name

        try:
            segments, _ = model.transcribe(
                tmp_path,
                language=self._config.language,
                beam_size=self._config.beam_size,
                initial_prompt=self._config.initial_prompt,
            )
            text = " ".join([segment.text for segment in segments])
            return TranscriptionResponse(text=text.strip())
        finally:
            os.unlink(tmp_path)
