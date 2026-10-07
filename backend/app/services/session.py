from pathlib import Path

from fastapi import HTTPException, UploadFile, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config import settings
from app.models.clinical import Patient, Session as ClinicalSession, SessionStatus, UploadedVideo
from app.schemas.session import SessionCreate


ALLOWED_VIDEO_EXTENSIONS = {".mp4", ".mov", ".avi", ".webm", ".mkv"}


def _initial_processing_steps() -> dict[str, bool]:
    return {
        "video_uploaded": False,
        "audio_extracted": False,
        "frames_extracted": False,
        "transcript_generated": False,
        "emotion_analysis_complete": False,
        "fusion_complete": False,
    }


def _owned_patient(db: Session, psychologist_id: int, patient_id: int) -> Patient:
    patient = db.scalar(
        select(Patient).where(
            Patient.id == patient_id,
            Patient.psychologist_id == psychologist_id,
        )
    )
    if patient is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Patient not found")
    return patient


def create_session(db: Session, psychologist_id: int, data: SessionCreate) -> ClinicalSession:
    _owned_patient(db, psychologist_id, data.patient_id)
    session = ClinicalSession(
        patient_id=data.patient_id,
        session_date=data.session_date,
        session_type=data.session_type,
        consent_confirmed=data.consent_confirmed,
        notes=data.notes,
        status=SessionStatus.created,
        processing_steps=_initial_processing_steps(),
    )
    db.add(session)
    db.commit()
    db.refresh(session)
    return session


def get_owned_session(db: Session, psychologist_id: int, session_id: int) -> ClinicalSession:
    session = db.scalar(
        select(ClinicalSession)
        .join(Patient, Patient.id == ClinicalSession.patient_id)
        .where(
            ClinicalSession.id == session_id,
            Patient.psychologist_id == psychologist_id,
        )
    )
    if session is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session not found")
    return session


def _upload_root() -> Path:
    configured = Path(settings.upload_dir)
    if configured.is_absolute():
        return configured
    return Path(__file__).resolve().parents[3] / configured


def upload_video(
    db: Session,
    psychologist_id: int,
    session_id: int,
    video: UploadFile,
) -> ClinicalSession:
    session = get_owned_session(db, psychologist_id, session_id)
    if not session.consent_confirmed:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Consent must be confirmed before uploading a video",
        )

    suffix = Path(video.filename or "").suffix.lower()
    if suffix not in ALLOWED_VIDEO_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Unsupported video file type",
        )

    destination = _upload_root() / str(session.patient_id) / str(session.id) / "original_video.mp4"
    destination.parent.mkdir(parents=True, exist_ok=True)
    try:
        with destination.open("wb") as output:
            while chunk := video.file.read(1024 * 1024):
                output.write(chunk)
    except OSError as exc:
        if destination.exists():
            destination.unlink()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Unable to save uploaded video",
        ) from exc
    finally:
        video.file.close()

    if session.uploaded_video is not None:
        session.uploaded_video.file_path = str(destination)
        session.uploaded_video.original_filename = video.filename or "original_video.mp4"
    else:
        session.uploaded_video = UploadedVideo(
            file_path=str(destination),
            original_filename=video.filename or "original_video.mp4",
        )
    session.processing_steps = {**_initial_processing_steps(), "video_uploaded": True}
    session.processing_error = None
    session.status = SessionStatus.uploaded
    db.commit()
    db.refresh(session)
    return session
