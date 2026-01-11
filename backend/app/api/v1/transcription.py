from fastapi import APIRouter, UploadFile, File, HTTPException, Depends

from ...models.transcription import TranscriptionResponse
from ...services.transcription_service import TranscriptionService

router = APIRouter()

def get_transcription_service() -> TranscriptionService:
    """Dependency injection for transcription service."""
    return TranscriptionService.get_instance()


@router.post("/transcribe", response_model=TranscriptionResponse)
async def transcribe_audio(
    file: UploadFile = File(...),
    service: TranscriptionService = Depends(get_transcription_service),
) -> TranscriptionResponse:
    """Transcribe audio file to text using Whisper."""
    if not file.content_type or not file.content_type.startswith("audio/"):
        raise HTTPException(status_code=400, detail="File must be an audio file")

    try:
        content = await file.read()
        return service.transcribe(content)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Transcription failed: {str(e)}")
