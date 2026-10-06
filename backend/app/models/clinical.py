import enum
from datetime import date, datetime

from sqlalchemy import Boolean, Date, DateTime, Enum, Float, ForeignKey, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class UserRole(str, enum.Enum):
    psychologist = "psychologist"
    admin = "admin"


class SessionStatus(str, enum.Enum):
    uploaded = "uploaded"
    processing = "processing"
    analysis_complete = "analysis_complete"
    reviewed = "reviewed"


class Modality(str, enum.Enum):
    text = "text"
    audio = "audio"
    face = "face"


class MomentType(str, enum.Enum):
    high_intensity = "high_intensity"
    sudden_transition = "sudden_transition"
    divergence = "divergence"
    sustained_emotion = "sustained_emotion"
    rapid_transitions = "rapid_transitions"


class AIObservationStatus(str, enum.Enum):
    accepted = "accepted"
    modified = "modified"
    dismissed = "dismissed"


class ReportStatus(str, enum.Enum):
    draft = "draft"
    finalized = "finalized"


class TimestampMixin:
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)


class User(TimestampMixin, Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[UserRole] = mapped_column(Enum(UserRole, name="user_role"), nullable=False)

    patients: Mapped[list["Patient"]] = relationship(back_populates="psychologist")
    clinician_notes: Mapped[list["ClinicianNote"]] = relationship(back_populates="author")


class Patient(TimestampMixin, Base):
    __tablename__ = "patients"

    id: Mapped[int] = mapped_column(primary_key=True)
    psychologist_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False, index=True)
    display_id: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    basic_info_json: Mapped[dict | None] = mapped_column(JSONB)

    psychologist: Mapped["User"] = relationship(back_populates="patients")
    sessions: Mapped[list["Session"]] = relationship(back_populates="patient", cascade="all, delete-orphan")


class Session(TimestampMixin, Base):
    __tablename__ = "sessions"

    id: Mapped[int] = mapped_column(primary_key=True)
    patient_id: Mapped[int] = mapped_column(ForeignKey("patients.id"), nullable=False, index=True)
    session_date: Mapped[date] = mapped_column(Date, nullable=False)
    session_type: Mapped[str] = mapped_column(String(100), nullable=False)
    duration_seconds: Mapped[int | None] = mapped_column(Integer)
    status: Mapped[SessionStatus] = mapped_column(
        Enum(SessionStatus, name="session_status"), default=SessionStatus.uploaded, nullable=False
    )
    consent_confirmed: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    notes: Mapped[str | None] = mapped_column(Text)

    patient: Mapped["Patient"] = relationship(back_populates="sessions")
    uploaded_video: Mapped["UploadedVideo | None"] = relationship(
        back_populates="session", cascade="all, delete-orphan", uselist=False
    )
    transcript: Mapped["Transcript | None"] = relationship(
        back_populates="session", cascade="all, delete-orphan", uselist=False
    )
    audio_features: Mapped[list["AudioFeature"]] = relationship(back_populates="session", cascade="all, delete-orphan")
    facial_analysis: Mapped[list["FacialAnalysis"]] = relationship(back_populates="session", cascade="all, delete-orphan")
    emotion_predictions: Mapped[list["EmotionPrediction"]] = relationship(
        back_populates="session", cascade="all, delete-orphan"
    )
    fusion_results: Mapped[list["FusionResult"]] = relationship(back_populates="session", cascade="all, delete-orphan")
    important_moments: Mapped[list["ImportantMoment"]] = relationship(
        back_populates="session", cascade="all, delete-orphan"
    )
    signal_divergences: Mapped[list["SignalDivergence"]] = relationship(
        back_populates="session", cascade="all, delete-orphan"
    )
    clinician_notes: Mapped[list["ClinicianNote"]] = relationship(back_populates="session", cascade="all, delete-orphan")
    report: Mapped["Report | None"] = relationship(back_populates="session", cascade="all, delete-orphan", uselist=False)


class UploadedVideo(Base):
    __tablename__ = "uploaded_videos"

    id: Mapped[int] = mapped_column(primary_key=True)
    session_id: Mapped[int] = mapped_column(ForeignKey("sessions.id"), unique=True, nullable=False)
    file_path: Mapped[str] = mapped_column(String(1024), nullable=False)
    original_filename: Mapped[str] = mapped_column(String(255), nullable=False)
    duration_seconds: Mapped[int | None] = mapped_column(Integer)
    uploaded_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    session: Mapped["Session"] = relationship(back_populates="uploaded_video")


class Transcript(Base):
    __tablename__ = "transcripts"

    id: Mapped[int] = mapped_column(primary_key=True)
    session_id: Mapped[int] = mapped_column(ForeignKey("sessions.id"), unique=True, nullable=False)
    language: Mapped[str | None] = mapped_column(String(50))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    session: Mapped["Session"] = relationship(back_populates="transcript")
    segments: Mapped[list["TranscriptSegment"]] = relationship(back_populates="transcript", cascade="all, delete-orphan")


class TranscriptSegment(Base):
    __tablename__ = "transcript_segments"

    id: Mapped[int] = mapped_column(primary_key=True)
    transcript_id: Mapped[int] = mapped_column(ForeignKey("transcripts.id"), nullable=False, index=True)
    start_time: Mapped[float] = mapped_column(Float, nullable=False)
    end_time: Mapped[float] = mapped_column(Float, nullable=False)
    speaker_label: Mapped[str | None] = mapped_column(String(100))
    text: Mapped[str] = mapped_column(Text, nullable=False)

    transcript: Mapped["Transcript"] = relationship(back_populates="segments")


class AudioFeature(Base):
    __tablename__ = "audio_features"

    id: Mapped[int] = mapped_column(primary_key=True)
    session_id: Mapped[int] = mapped_column(ForeignKey("sessions.id"), nullable=False, index=True)
    window_start: Mapped[float] = mapped_column(Float, nullable=False)
    window_end: Mapped[float] = mapped_column(Float, nullable=False)
    pitch_mean: Mapped[float | None] = mapped_column(Float)
    pitch_std: Mapped[float | None] = mapped_column(Float)
    energy_mean: Mapped[float | None] = mapped_column(Float)
    speaking_rate: Mapped[float | None] = mapped_column(Float)
    pause_count: Mapped[int | None] = mapped_column(Integer)
    pause_duration_total: Mapped[float | None] = mapped_column(Float)

    session: Mapped["Session"] = relationship(back_populates="audio_features")


class FacialAnalysis(Base):
    __tablename__ = "facial_analysis"

    id: Mapped[int] = mapped_column(primary_key=True)
    session_id: Mapped[int] = mapped_column(ForeignKey("sessions.id"), nullable=False, index=True)
    window_start: Mapped[float] = mapped_column(Float, nullable=False)
    window_end: Mapped[float] = mapped_column(Float, nullable=False)
    frames_sampled: Mapped[int] = mapped_column(Integer, nullable=False)
    face_detected_ratio: Mapped[float | None] = mapped_column(Float)
    probabilities_json: Mapped[dict | None] = mapped_column(JSONB)

    session: Mapped["Session"] = relationship(back_populates="facial_analysis")


class EmotionPrediction(Base):
    __tablename__ = "emotion_predictions"

    id: Mapped[int] = mapped_column(primary_key=True)
    session_id: Mapped[int] = mapped_column(ForeignKey("sessions.id"), nullable=False, index=True)
    window_start: Mapped[float] = mapped_column(Float, nullable=False)
    window_end: Mapped[float] = mapped_column(Float, nullable=False)
    modality: Mapped[Modality] = mapped_column(Enum(Modality, name="modality"), nullable=False)
    probabilities_json: Mapped[dict] = mapped_column(JSONB, nullable=False)
    dominant_emotion: Mapped[str] = mapped_column(String(50), nullable=False)
    confidence: Mapped[float] = mapped_column(Float, nullable=False)

    session: Mapped["Session"] = relationship(back_populates="emotion_predictions")


class FusionResult(Base):
    __tablename__ = "fusion_results"

    id: Mapped[int] = mapped_column(primary_key=True)
    session_id: Mapped[int] = mapped_column(ForeignKey("sessions.id"), nullable=False, index=True)
    window_start: Mapped[float] = mapped_column(Float, nullable=False)
    window_end: Mapped[float] = mapped_column(Float, nullable=False)
    probabilities_json: Mapped[dict] = mapped_column(JSONB, nullable=False)
    dominant_emotion: Mapped[str] = mapped_column(String(50), nullable=False)
    confidence: Mapped[float] = mapped_column(Float, nullable=False)
    modalities_used_json: Mapped[dict] = mapped_column(JSONB, nullable=False)
    weights_used_json: Mapped[dict] = mapped_column(JSONB, nullable=False)

    session: Mapped["Session"] = relationship(back_populates="fusion_results")


class ImportantMoment(Base):
    __tablename__ = "important_moments"

    id: Mapped[int] = mapped_column(primary_key=True)
    session_id: Mapped[int] = mapped_column(ForeignKey("sessions.id"), nullable=False, index=True)
    timestamp: Mapped[float] = mapped_column(Float, nullable=False)
    moment_type: Mapped[MomentType] = mapped_column(Enum(MomentType, name="moment_type"), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    related_window_ids_json: Mapped[dict | None] = mapped_column(JSONB)

    session: Mapped["Session"] = relationship(back_populates="important_moments")


class SignalDivergence(Base):
    __tablename__ = "signal_divergences"

    id: Mapped[int] = mapped_column(primary_key=True)
    session_id: Mapped[int] = mapped_column(ForeignKey("sessions.id"), nullable=False, index=True)
    window_start: Mapped[float] = mapped_column(Float, nullable=False)
    window_end: Mapped[float] = mapped_column(Float, nullable=False)
    modalities_involved_json: Mapped[dict] = mapped_column(JSONB, nullable=False)
    divergence_score: Mapped[float] = mapped_column(Float, nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)

    session: Mapped["Session"] = relationship(back_populates="signal_divergences")


class ClinicianNote(Base):
    __tablename__ = "clinician_notes"

    id: Mapped[int] = mapped_column(primary_key=True)
    session_id: Mapped[int] = mapped_column(ForeignKey("sessions.id"), nullable=False, index=True)
    author_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False, index=True)
    body: Mapped[str] = mapped_column(Text, nullable=False)
    ai_observation_status: Mapped[AIObservationStatus | None] = mapped_column(
        Enum(AIObservationStatus, name="ai_observation_status")
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    session: Mapped["Session"] = relationship(back_populates="clinician_notes")
    author: Mapped["User"] = relationship(back_populates="clinician_notes")


class Report(Base):
    __tablename__ = "reports"

    id: Mapped[int] = mapped_column(primary_key=True)
    session_id: Mapped[int] = mapped_column(ForeignKey("sessions.id"), unique=True, nullable=False)
    content_json: Mapped[dict] = mapped_column(JSONB, nullable=False)
    pdf_file_path: Mapped[str | None] = mapped_column(String(1024))
    generated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    last_edited_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    status: Mapped[ReportStatus] = mapped_column(
        Enum(ReportStatus, name="report_status"), default=ReportStatus.draft, nullable=False
    )

    session: Mapped["Session"] = relationship(back_populates="report")
