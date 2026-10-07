import re
from pathlib import Path

from app.db.session import SessionLocal
from app.config import settings
from app.models.clinical import Session as ClinicalSession

_FRAME_TIMESTAMP = re.compile(r"frame_(?P<timestamp>\d+(?:\.\d+)?)s\.jpg$")


def _upload_root() -> Path:
    configured = Path(settings.upload_dir)
    return configured if configured.is_absolute() else Path(__file__).resolve().parents[3] / configured


def build_analysis_windows(
    session_id: int,
    window_seconds: float = 7.5,
) -> list[dict]:
    if window_seconds <= 0:
        raise ValueError("window_seconds must be greater than zero")
    with SessionLocal() as db:
        session = db.get(ClinicalSession, session_id)
        if session is None:
            raise ValueError(f"Session {session_id} was not found")
        duration = float(session.duration_seconds or 0)
        if duration <= 0 or session.uploaded_video is None:
            return []

        session_dir = _upload_root() / str(session.patient_id) / str(session.id)
        audio_path = session_dir / "audio.wav"
        frames = []
        for frame_path in (session_dir / "frames").glob("frame_*.jpg"):
            match = _FRAME_TIMESTAMP.match(frame_path.name)
            if match:
                frames.append((float(match.group("timestamp")), str(frame_path)))
        frames.sort()
        segments = session.transcript.segments if session.transcript else []
        windows = []
        start = 0.0
        while start < duration:
            end = min(start + window_seconds, duration)
            text = " ".join(
                segment.text.strip()
                for segment in segments
                if float(segment.start_time) < end and float(segment.end_time) > start and segment.text.strip()
            )
            windows.append(
                {
                    "window_start": start,
                    "window_end": end,
                    "text": text,
                    "audio_slice_path": str(audio_path),
                    "audio_start": start,
                    "audio_end": end,
                    "frame_paths": [path for timestamp, path in frames if start <= timestamp < end],
                }
            )
            start = end
        return windows
