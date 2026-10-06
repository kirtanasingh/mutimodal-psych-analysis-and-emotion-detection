from datetime import date, datetime

from pydantic import BaseModel, ConfigDict


class SessionCreate(BaseModel):
    patient_id: int
    session_date: date
    session_type: str
    consent_confirmed: bool
    notes: str | None = None


class SessionOut(BaseModel):
    id: int
    patient_id: int
    session_date: date
    session_type: str
    duration_seconds: int | None
    status: str
    consent_confirmed: bool
    notes: str | None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True, use_enum_values=True)
