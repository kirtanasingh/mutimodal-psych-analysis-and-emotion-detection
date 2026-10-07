from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.security import get_current_user
from app.db.session import get_db
from app.models.clinical import (
    FusionResult,
    Patient,
    Report,
    Session as ClinicalSession,
    SessionStatus,
    SignalDivergence,
    User,
)

router = APIRouter(prefix="/api/dashboard", tags=["dashboard"])


def _owned_sessions(current_user: User):
    return (
        select(ClinicalSession)
        .join(Patient, Patient.id == ClinicalSession.patient_id)
        .where(Patient.psychologist_id == current_user.id)
    )


@router.get("/summary")
def summary(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)) -> dict:
    week_start = (datetime.now(timezone.utc) - timedelta(days=7)).date()
    patients = db.scalar(select(func.count(Patient.id)).where(Patient.psychologist_id == current_user.id)) or 0
    sessions_week = db.scalar(
        select(func.count(ClinicalSession.id))
        .join(Patient)
        .where(Patient.psychologist_id == current_user.id, ClinicalSession.session_date >= week_start)
    ) or 0
    reports = db.scalar(
        select(func.count(Report.id))
        .join(ClinicalSession)
        .join(Patient)
        .where(Patient.psychologist_id == current_user.id, Report.status == "draft")
    ) or 0
    processing = db.scalar(
        select(func.count(ClinicalSession.id))
        .join(Patient)
        .where(
            Patient.psychologist_id == current_user.id,
            ClinicalSession.status.notin_([SessionStatus.analysis_complete, SessionStatus.reviewed, SessionStatus.upload_failed]),
        )
    ) or 0
    return {
        "total_patients": patients,
        "sessions_this_week": sessions_week,
        "reports_awaiting_review": reports,
        "sessions_processing": processing,
    }


@router.get("/recent-sessions")
def recent_sessions(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)) -> list[dict]:
    rows = db.execute(
        select(ClinicalSession, Patient.display_id)
        .join(Patient, Patient.id == ClinicalSession.patient_id)
        .where(Patient.psychologist_id == current_user.id)
        .order_by(ClinicalSession.session_date.desc(), ClinicalSession.created_at.desc())
        .limit(8)
    ).all()
    return [_session_payload(db, session, display_id) for session, display_id in rows]


EMOTIONS = ("anger", "disgust", "fear", "joy", "neutral", "sadness", "surprise")


def _session_payload(db: Session, session: ClinicalSession, display_id: str) -> dict:
    fusion_rows = db.scalars(
        select(FusionResult)
        .where(FusionResult.session_id == session.id)
        .order_by(FusionResult.window_start)
    ).all()
    distribution = {
        emotion: sum((row.probabilities_json or {}).get(emotion, 0) for row in fusion_rows)
        / max(len(fusion_rows), 1)
        for emotion in EMOTIONS
    }
    return {
        "id": session.id,
        "patient_display_id": display_id,
        "session_date": session.session_date,
        "duration_seconds": session.duration_seconds,
        "status": session.status.value,
        "emotion_distribution": distribution,
    }


@router.get("/priority-queue")
def priority_queue(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)) -> list[dict]:
    today = datetime.now(timezone.utc).date()
    rows = db.execute(
        select(ClinicalSession, Patient.display_id)
        .join(Patient, Patient.id == ClinicalSession.patient_id)
        .where(
            Patient.psychologist_id == current_user.id,
            ClinicalSession.status == SessionStatus.analysis_complete,
        )
        .order_by(ClinicalSession.session_date.asc())
    ).all()
    results = []
    for session, display_id in rows:
        divergences = db.scalars(
            select(SignalDivergence).where(SignalDivergence.session_id == session.id)
        ).all()
        fusion_rows = db.scalars(select(FusionResult).where(FusionResult.session_id == session.id)).all()
        reasons = []
        divergence_count = len(divergences)
        score = divergence_count * 3
        if divergence_count:
            reasons.append(f"{divergence_count} divergence{'s' if divergence_count != 1 else ''}")
        confidences = sorted(row.confidence for row in fusion_rows)
        if confidences:
            bottom_quartile_index = max(0, int(len(confidences) * 0.25) - 1)
            if any(row.confidence <= confidences[bottom_quartile_index] for row in fusion_rows):
                score += 2
                reasons.append("low confidence")
        age_days = max(0, (today - session.session_date).days)
        score += age_days
        reasons.append("awaiting review")
        payload = _session_payload(db, session, display_id)
        payload.update({
            "urgency_score": score,
            "divergence_count": divergence_count,
            "reason_tags": reasons,
        })
        results.append(payload)
    return sorted(results, key=lambda item: (-item["urgency_score"], item["session_date"], item["id"]))[:10]


@router.get("/caseload-snapshot")
def caseload_snapshot(
    days: int = 7,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> dict:
    period_days = max(1, min(days, 365))
    start_date = (datetime.now(timezone.utc) - timedelta(days=period_days - 1)).date()
    session_ids = db.scalars(
        select(ClinicalSession.id)
        .join(Patient, Patient.id == ClinicalSession.patient_id)
        .where(Patient.psychologist_id == current_user.id, ClinicalSession.session_date >= start_date)
    ).all()
    fusion_rows = db.scalars(
        select(FusionResult).where(FusionResult.session_id.in_(session_ids))
    ).all() if session_ids else []
    distribution = {
        emotion: sum((row.probabilities_json or {}).get(emotion, 0) for row in fusion_rows)
        / max(len(fusion_rows), 1)
        for emotion in EMOTIONS
    }
    return {"period_days": period_days, "session_count": len(session_ids), "emotion_distribution": distribution}


@router.get("/recent-reports")
def recent_reports(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)) -> list[dict]:
    rows = db.execute(
        select(Report, Patient.display_id, ClinicalSession.session_date)
        .join(ClinicalSession, ClinicalSession.id == Report.session_id)
        .join(Patient, Patient.id == ClinicalSession.patient_id)
        .where(Patient.psychologist_id == current_user.id)
        .order_by(Report.generated_at.desc())
        .limit(8)
    ).all()
    return [
        {
            "id": report.id,
            "session_id": report.session_id,
            "patient_display_id": display_id,
            "session_date": session_date,
            "generated_at": report.generated_at,
            "pdf_available": bool(report.pdf_file_path),
            "download_url": f"/api/sessions/{report.session_id}/report/pdf",
        }
        for report, display_id, session_date in rows
    ]
