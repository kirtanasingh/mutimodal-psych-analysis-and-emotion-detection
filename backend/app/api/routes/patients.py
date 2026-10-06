from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.core.security import get_current_user
from app.db.session import get_db
from app.models.clinical import User
from app.schemas.patient import PatientCreate, PatientDetail, PatientOut
from app.services.patient import create_patient, get_patient, list_patients


router = APIRouter(prefix="/api/patients", tags=["patients"])


@router.post("", response_model=PatientOut, status_code=status.HTTP_201_CREATED)
def create(
    payload: PatientCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> PatientOut:
    return create_patient(db, current_user.id, payload)


@router.get("", response_model=list[PatientOut])
def list_all(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[PatientOut]:
    return list_patients(db, current_user.id)


@router.get("/{patient_id}", response_model=PatientDetail)
def detail(
    patient_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> PatientDetail:
    patient = get_patient(db, current_user.id, patient_id)
    return PatientDetail.model_validate(patient).model_copy(update={"sessions": []})
