from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.security import get_current_user
from app.db.session import get_db
from app.models.clinical import FusionResult, User
from sqlalchemy import select
from app.schemas.patient import PatientCreate, PatientDetail, PatientOut, PatientUpdate
from app.services.patient import create_patient, get_patient, list_patients, update_patient


router = APIRouter(prefix="/api/patients", tags=["patients"])


@router.post("", response_model=PatientOut, status_code=status.HTTP_201_CREATED)
def create(
    payload: PatientCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> PatientOut:
    return _patient_response(create_patient(db, current_user.id, payload))


@router.get("", response_model=list[PatientOut])
def list_all(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[PatientOut]:
    return [_patient_response(patient) for patient in list_patients(db, current_user.id)]


@router.get("/{patient_id}", response_model=PatientDetail)
def detail(
    patient_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> PatientDetail:
    patient = get_patient(db, current_user.id, patient_id)
    sessions = []
    for session in sorted(patient.sessions, key=lambda item: item.session_date, reverse=True):
        fusion = db.scalar(
            select(FusionResult)
            .where(FusionResult.session_id == session.id)
            .order_by(FusionResult.confidence.desc())
        )
        probabilities = fusion.probabilities_json if fusion else {}
        distribution = {
            emotion: float(probabilities.get(emotion, 0))
            for emotion in ("anger", "disgust", "fear", "joy", "neutral", "sadness", "surprise")
        }
        sessions.append({
            "id": session.id,
            "session_date": session.session_date,
            "duration_seconds": session.duration_seconds,
            "status": session.status.value,
            "dominant_emotion": fusion.dominant_emotion if fusion else None,
            "dominant_proportion": float(probabilities.get(fusion.dominant_emotion, 0)) if fusion else None,
            "emotion_distribution": distribution,
        })
    patient_data = _patient_response(patient).model_dump()
    return PatientDetail.model_validate({**patient_data, "sessions": sessions})


@router.patch("/{patient_id}", response_model=PatientOut)
def update(
    patient_id: int,
    payload: PatientUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> PatientOut:
    return _patient_response(update_patient(db, current_user.id, patient_id, payload))


def _patient_response(patient) -> PatientOut:
    info = patient.basic_info_json or {}
    return PatientOut.model_validate({
        "id": patient.id,
        "display_id": patient.display_id,
        "basic_info_json": patient.basic_info_json,
        "created_at": patient.created_at,
        "session_count": patient.session_count,
        "last_session_date": patient.last_session_date,
        "full_name": info.get("full_name"),
        "age": info.get("age"),
        "profession": info.get("profession"),
    })


@router.get("/{patient_id}/sessions/compare")
def compare_sessions(
    patient_id: int,
    session_a: int,
    session_b: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> dict:
    patient = get_patient(db, current_user.id, patient_id)
    sessions = {session.id: session for session in patient.sessions}
    if session_a not in sessions or session_b not in sessions or session_a == session_b:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Sessions do not belong to this patient")

    def payload(session_id: int) -> dict:
        rows = db.scalars(
            select(FusionResult)
            .where(FusionResult.session_id == session_id)
            .order_by(FusionResult.window_start)
        ).all()
        timeline = [
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
        averages = {
            emotion: sum(item["probabilities"].get(emotion, 0) for item in timeline) / max(len(timeline), 1)
            for emotion in ("anger", "disgust", "fear", "joy", "neutral", "sadness", "surprise")
        }
        return {
            "id": session_id,
            "session_date": sessions[session_id].session_date,
            "duration_seconds": sessions[session_id].duration_seconds,
            "distribution": averages,
            "timeline": timeline,
        }

    return {"session_a": payload(session_a), "session_b": payload(session_b)}
