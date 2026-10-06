from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, Field


class PatientCreate(BaseModel):
    basic_info_json: dict | None = Field(default=None)


class SessionSummary(BaseModel):
    id: int
    session_date: date
    duration_seconds: int | None
    status: str


class PatientOut(BaseModel):
    id: int
    display_id: str
    basic_info_json: dict | None
    created_at: datetime
    session_count: int = 0
    last_session_date: date | None = None

    model_config = ConfigDict(from_attributes=True)


class PatientDetail(PatientOut):
    # This will be populated when Phase 4 session APIs are implemented.
    sessions: list[SessionSummary] = Field(default_factory=list)
