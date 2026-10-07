from pathlib import Path

import whisper
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config import settings
from app.models.clinical import Transcript, TranscriptSegment


class TranscriptionResult(list[dict[str, float | str]]):
    def __init__(self, segments: list[dict[str, float | str]], language: str | None):
        super().__init__(segments)
        self.language = language


# Loaded once when the Celery worker imports this module, not once per task.
model = whisper.load_model(settings.whisper_model_size)


def transcribe_audio(audio_wav_path: str | Path) -> list[dict[str, float | str]]:
    audio_path = Path(audio_wav_path)
    if not audio_path.is_file():
        raise FileNotFoundError(f"Audio file does not exist: {audio_path}")
    result = model.transcribe(str(audio_path))
    segments = [
        {
            "start_time": float(segment["start"]),
            "end_time": float(segment["end"]),
            "text": str(segment["text"]).strip(),
        }
        for segment in result.get("segments", [])
    ]
    return TranscriptionResult(segments, result.get("language"))


def save_transcript(
    db: Session,
    session_id: int,
    language: str | None,
    segments: list[dict[str, float | str]],
) -> Transcript:
    transcript = db.scalar(select(Transcript).where(Transcript.session_id == session_id))
    if transcript is not None:
        db.delete(transcript)
        db.flush()

    transcript = Transcript(session_id=session_id, language=language)
    transcript.segments = [
        # Whisper has no speaker diarization; speaker_label remains null until the advanced phase.
        TranscriptSegment(
            start_time=float(segment["start_time"]),
            end_time=float(segment["end_time"]),
            text=str(segment["text"]),
        )
        for segment in segments
    ]
    db.add(transcript)
    db.flush()
    return transcript
