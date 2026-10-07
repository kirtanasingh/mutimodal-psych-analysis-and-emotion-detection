from fastapi import APIRouter, Depends, File, HTTPException, Response, UploadFile, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.security import get_current_user
from app.db.session import get_db
from app.models.clinical import EmotionPrediction, FusionResult, SignalDivergence, Transcript, User
from app.schemas.session import SessionCreate, SessionOut
from app.schemas.transcript import TranscriptOut
from app.services.session import create_session, get_owned_session, upload_video
from app.workers.tasks import process_session_video


router = APIRouter(prefix="/api/sessions", tags=["sessions"])


@router.post("", response_model=SessionOut, status_code=status.HTTP_201_CREATED)
def create(
    payload: SessionCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> SessionOut:
    return create_session(db, current_user.id, payload)


@router.get("/{session_id}/status")
def processing_status(
    session_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> dict:
    session = get_owned_session(db, current_user.id, session_id)
    return {
        "status": session.status.value,
        "processing_steps": session.processing_steps,
        "processing_error": session.processing_error,
    }


@router.get("/{session_id}", response_model=SessionOut)
def detail(
    session_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> SessionOut:
    return get_owned_session(db, current_user.id, session_id)


@router.get("/{session_id}/transcript", response_model=TranscriptOut)
def transcript(
    session_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Transcript:
    session = get_owned_session(db, current_user.id, session_id)
    if session.transcript is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Transcript not found")
    return session.transcript


@router.get("/{session_id}/analysis")
def analysis(
    session_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[dict]:
    session = get_owned_session(db, current_user.id, session_id)
    rows = db.scalars(
        select(EmotionPrediction)
        .where(EmotionPrediction.session_id == session.id)
        .order_by(EmotionPrediction.window_start, EmotionPrediction.modality)
    ).all()
    grouped: dict[tuple[float, float], dict] = {}
    for row in rows:
        key = (row.window_start, row.window_end)
        window = grouped.setdefault(
            key,
            {"window_start": row.window_start, "window_end": row.window_end, "text": None, "audio": None, "face": None},
        )
        window[row.modality.value] = {
            "probabilities": row.probabilities_json,
            "dominant_emotion": row.dominant_emotion,
            "confidence": row.confidence,
        }
    return list(grouped.values())


@router.get("/{session_id}/timeline")
def timeline(
    session_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[dict]:
    session = get_owned_session(db, current_user.id, session_id)
    rows = db.scalars(
        select(FusionResult)
        .where(FusionResult.session_id == session.id)
        .order_by(FusionResult.window_start)
    ).all()
    return [
        {
            "window_start": row.window_start,
            "window_end": row.window_end,
            "probabilities": row.probabilities_json,
            "dominant_emotion": row.dominant_emotion,
            "confidence": row.confidence,
            "modalities_used": row.modalities_used_json,
        }
        for row in rows
    ]


@router.get("/{session_id}/divergences")
def divergences(
    session_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[dict]:
    session = get_owned_session(db, current_user.id, session_id)
    rows = db.scalars(
        select(SignalDivergence)
        .where(SignalDivergence.session_id == session.id)
        .order_by(SignalDivergence.window_start)
    ).all()
    return [
        {
            "window_start": row.window_start,
            "window_end": row.window_end,
            "modalities_involved": row.modalities_involved_json,
            "divergence_score": row.divergence_score,
            "description": row.description,
        }
        for row in rows
    ]


@router.get("/{session_id}/summary")
def summary(
    session_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> dict:
    session = get_owned_session(db, current_user.id, session_id)
    from app.services.summary_service import generate_session_summary

    return {"summary": generate_session_summary(db, session.id)}


@router.get("/{session_id}/report/pdf")
def report_pdf(
    session_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Response:
    session = get_owned_session(db, current_user.id, session_id)
    from app.services.report_service import generate_report_pdf
    try:
        pdf = generate_report_pdf(db, session.id)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc
    return Response(
        content=pdf,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="session-{session.id}-analysis.pdf"'},
    )


@router.post("/{session_id}/upload", response_model=SessionOut)
def upload(
    session_id: int,
    video: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> SessionOut:
    session = upload_video(db, current_user.id, session_id, video)
    process_session_video.delay(session.id)
    return session
