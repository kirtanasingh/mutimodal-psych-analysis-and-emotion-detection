from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, Field, model_validator


class PatientCreate(BaseModel):
    basic_info_json: dict | None = Field(default=None)
    full_name: str | None = None
    age: int | None = None
    profession: str | None = None

    @model_validator(mode="after")
    def require_patient_information(self):
        basic_info = self.basic_info_json or {}
        has_json_value = any(
            value is not None and str(value).strip()
            for value in basic_info.values()
        )
        if not any((self.full_name and self.full_name.strip(), self.age is not None, self.profession and self.profession.strip(), has_json_value)):
            raise ValueError("Provide at least one patient detail before creating a patient")
        return self


class PatientUpdate(BaseModel):
    full_name: str | None = None
    age: int | None = None
    profession: str | None = None


class SessionSummary(BaseModel):
    id: int
    session_date: date
    duration_seconds: int | None
    status: str
    dominant_emotion: str | None = None
    dominant_proportion: float | None = None


class PatientOut(BaseModel):
    id: int
    display_id: str
    basic_info_json: dict | None
    created_at: datetime
    session_count: int = 0
    last_session_date: date | None = None
    full_name: str | None = None
    age: int | None = None
    profession: str | None = None

    model_config = ConfigDict(from_attributes=True)


class PatientDetail(PatientOut):
    # This will be populated when Phase 4 session APIs are implemented.
    sessions: list[SessionSummary] = Field(default_factory=list)
