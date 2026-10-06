import secrets

from fastapi import HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.clinical import Patient, Session as ClinicalSession
from app.schemas.patient import PatientCreate


def _generate_display_id(db: Session, psychologist_id: int) -> str:
    for _ in range(20):
        candidate = f"P-{secrets.randbelow(9000) + 1000}"
        exists = db.scalar(
            select(Patient.id).where(
                Patient.psychologist_id == psychologist_id,
                Patient.display_id == candidate,
            )
        )
        if exists is None:
            return candidate
    raise HTTPException(
        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        detail="Unable to allocate a unique patient identifier",
    )


def _add_session_summary(db: Session, patient: Patient) -> Patient:
    session_count, last_session_date = db.execute(
        select(func.count(ClinicalSession.id), func.max(ClinicalSession.session_date)).where(
            ClinicalSession.patient_id == patient.id
        )
    ).one()
    patient.session_count = int(session_count or 0)
    patient.last_session_date = last_session_date
    return patient


def create_patient(db: Session, psychologist_id: int, data: PatientCreate) -> Patient:
    patient = Patient(
        psychologist_id=psychologist_id,
        display_id=_generate_display_id(db, psychologist_id),
        basic_info_json=data.basic_info_json,
    )
    db.add(patient)
    db.commit()
    db.refresh(patient)
    return _add_session_summary(db, patient)


def list_patients(db: Session, psychologist_id: int) -> list[Patient]:
    patients = list(
        db.scalars(
            select(Patient)
            .where(Patient.psychologist_id == psychologist_id)
            .order_by(Patient.created_at.desc(), Patient.id.desc())
        )
    )
    return [_add_session_summary(db, patient) for patient in patients]


def get_patient(db: Session, psychologist_id: int, patient_id: int) -> Patient:
    patient = db.scalar(
        select(Patient).where(
            Patient.id == patient_id,
            Patient.psychologist_id == psychologist_id,
        )
    )
    if patient is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Patient not found")
    return _add_session_summary(db, patient)
