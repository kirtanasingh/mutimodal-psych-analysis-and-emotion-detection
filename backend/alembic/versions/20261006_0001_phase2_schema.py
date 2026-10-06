"""phase 2 schema

Revision ID: 20261006_0001
Revises:
Create Date: 2026-10-06
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql


revision: str = "20261006_0001"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    user_role = postgresql.ENUM("psychologist", "admin", name="user_role", create_type=False)
    session_status = postgresql.ENUM(
        "uploaded", "processing", "analysis_complete", "reviewed", name="session_status", create_type=False
    )
    modality = postgresql.ENUM("text", "audio", "face", name="modality", create_type=False)
    moment_type = postgresql.ENUM(
        "high_intensity",
        "sudden_transition",
        "divergence",
        "sustained_emotion",
        "rapid_transitions",
        name="moment_type",
        create_type=False,
    )
    ai_observation_status = postgresql.ENUM(
        "accepted", "modified", "dismissed", name="ai_observation_status", create_type=False
    )
    report_status = postgresql.ENUM("draft", "finalized", name="report_status", create_type=False)

    user_role.create(op.get_bind(), checkfirst=True)
    session_status.create(op.get_bind(), checkfirst=True)
    modality.create(op.get_bind(), checkfirst=True)
    moment_type.create(op.get_bind(), checkfirst=True)
    ai_observation_status.create(op.get_bind(), checkfirst=True)
    report_status.create(op.get_bind(), checkfirst=True)

    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("email", sa.String(length=255), nullable=False),
        sa.Column("password_hash", sa.String(length=255), nullable=False),
        sa.Column("role", user_role, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_users_email"), "users", ["email"], unique=True)

    op.create_table(
        "patients",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("psychologist_id", sa.Integer(), nullable=False),
        sa.Column("display_id", sa.String(length=100), nullable=False),
        sa.Column("basic_info_json", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["psychologist_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_patients_display_id"), "patients", ["display_id"], unique=False)
    op.create_index(op.f("ix_patients_psychologist_id"), "patients", ["psychologist_id"], unique=False)

    op.create_table(
        "sessions",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("patient_id", sa.Integer(), nullable=False),
        sa.Column("session_date", sa.Date(), nullable=False),
        sa.Column("session_type", sa.String(length=100), nullable=False),
        sa.Column("duration_seconds", sa.Integer(), nullable=True),
        sa.Column("status", session_status, nullable=False),
        sa.Column("consent_confirmed", sa.Boolean(), nullable=False),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["patient_id"], ["patients.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_sessions_patient_id"), "sessions", ["patient_id"], unique=False)

    op.create_table(
        "audio_features",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("session_id", sa.Integer(), nullable=False),
        sa.Column("window_start", sa.Float(), nullable=False),
        sa.Column("window_end", sa.Float(), nullable=False),
        sa.Column("pitch_mean", sa.Float(), nullable=True),
        sa.Column("pitch_std", sa.Float(), nullable=True),
        sa.Column("energy_mean", sa.Float(), nullable=True),
        sa.Column("speaking_rate", sa.Float(), nullable=True),
        sa.Column("pause_count", sa.Integer(), nullable=True),
        sa.Column("pause_duration_total", sa.Float(), nullable=True),
        sa.ForeignKeyConstraint(["session_id"], ["sessions.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_audio_features_session_id"), "audio_features", ["session_id"], unique=False)

    op.create_table(
        "clinician_notes",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("session_id", sa.Integer(), nullable=False),
        sa.Column("author_id", sa.Integer(), nullable=False),
        sa.Column("body", sa.Text(), nullable=False),
        sa.Column("ai_observation_status", ai_observation_status, nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["author_id"], ["users.id"]),
        sa.ForeignKeyConstraint(["session_id"], ["sessions.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_clinician_notes_author_id"), "clinician_notes", ["author_id"], unique=False)
    op.create_index(op.f("ix_clinician_notes_session_id"), "clinician_notes", ["session_id"], unique=False)

    op.create_table(
        "emotion_predictions",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("session_id", sa.Integer(), nullable=False),
        sa.Column("window_start", sa.Float(), nullable=False),
        sa.Column("window_end", sa.Float(), nullable=False),
        sa.Column("modality", modality, nullable=False),
        sa.Column("probabilities_json", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("dominant_emotion", sa.String(length=50), nullable=False),
        sa.Column("confidence", sa.Float(), nullable=False),
        sa.ForeignKeyConstraint(["session_id"], ["sessions.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_emotion_predictions_session_id"), "emotion_predictions", ["session_id"], unique=False)

    op.create_table(
        "facial_analysis",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("session_id", sa.Integer(), nullable=False),
        sa.Column("window_start", sa.Float(), nullable=False),
        sa.Column("window_end", sa.Float(), nullable=False),
        sa.Column("frames_sampled", sa.Integer(), nullable=False),
        sa.Column("face_detected_ratio", sa.Float(), nullable=True),
        sa.Column("probabilities_json", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.ForeignKeyConstraint(["session_id"], ["sessions.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_facial_analysis_session_id"), "facial_analysis", ["session_id"], unique=False)

    op.create_table(
        "fusion_results",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("session_id", sa.Integer(), nullable=False),
        sa.Column("window_start", sa.Float(), nullable=False),
        sa.Column("window_end", sa.Float(), nullable=False),
        sa.Column("probabilities_json", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("dominant_emotion", sa.String(length=50), nullable=False),
        sa.Column("confidence", sa.Float(), nullable=False),
        sa.Column("modalities_used_json", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("weights_used_json", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.ForeignKeyConstraint(["session_id"], ["sessions.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_fusion_results_session_id"), "fusion_results", ["session_id"], unique=False)

    op.create_table(
        "important_moments",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("session_id", sa.Integer(), nullable=False),
        sa.Column("timestamp", sa.Float(), nullable=False),
        sa.Column("moment_type", moment_type, nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("related_window_ids_json", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.ForeignKeyConstraint(["session_id"], ["sessions.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_important_moments_session_id"), "important_moments", ["session_id"], unique=False)

    op.create_table(
        "reports",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("session_id", sa.Integer(), nullable=False),
        sa.Column("content_json", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("pdf_file_path", sa.String(length=1024), nullable=True),
        sa.Column("generated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("last_edited_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("status", report_status, nullable=False),
        sa.ForeignKeyConstraint(["session_id"], ["sessions.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("session_id"),
    )

    op.create_table(
        "signal_divergences",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("session_id", sa.Integer(), nullable=False),
        sa.Column("window_start", sa.Float(), nullable=False),
        sa.Column("window_end", sa.Float(), nullable=False),
        sa.Column("modalities_involved_json", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("divergence_score", sa.Float(), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.ForeignKeyConstraint(["session_id"], ["sessions.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_signal_divergences_session_id"), "signal_divergences", ["session_id"], unique=False)

    op.create_table(
        "transcripts",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("session_id", sa.Integer(), nullable=False),
        sa.Column("language", sa.String(length=50), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["session_id"], ["sessions.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("session_id"),
    )

    op.create_table(
        "uploaded_videos",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("session_id", sa.Integer(), nullable=False),
        sa.Column("file_path", sa.String(length=1024), nullable=False),
        sa.Column("original_filename", sa.String(length=255), nullable=False),
        sa.Column("duration_seconds", sa.Integer(), nullable=True),
        sa.Column("uploaded_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["session_id"], ["sessions.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("session_id"),
    )

    op.create_table(
        "transcript_segments",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("transcript_id", sa.Integer(), nullable=False),
        sa.Column("start_time", sa.Float(), nullable=False),
        sa.Column("end_time", sa.Float(), nullable=False),
        sa.Column("speaker_label", sa.String(length=100), nullable=True),
        sa.Column("text", sa.Text(), nullable=False),
        sa.ForeignKeyConstraint(["transcript_id"], ["transcripts.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_transcript_segments_transcript_id"), "transcript_segments", ["transcript_id"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_transcript_segments_transcript_id"), table_name="transcript_segments")
    op.drop_table("transcript_segments")
    op.drop_table("uploaded_videos")
    op.drop_table("transcripts")
    op.drop_index(op.f("ix_signal_divergences_session_id"), table_name="signal_divergences")
    op.drop_table("signal_divergences")
    op.drop_table("reports")
    op.drop_index(op.f("ix_important_moments_session_id"), table_name="important_moments")
    op.drop_table("important_moments")
    op.drop_index(op.f("ix_fusion_results_session_id"), table_name="fusion_results")
    op.drop_table("fusion_results")
    op.drop_index(op.f("ix_facial_analysis_session_id"), table_name="facial_analysis")
    op.drop_table("facial_analysis")
    op.drop_index(op.f("ix_emotion_predictions_session_id"), table_name="emotion_predictions")
    op.drop_table("emotion_predictions")
    op.drop_index(op.f("ix_clinician_notes_session_id"), table_name="clinician_notes")
    op.drop_index(op.f("ix_clinician_notes_author_id"), table_name="clinician_notes")
    op.drop_table("clinician_notes")
    op.drop_index(op.f("ix_audio_features_session_id"), table_name="audio_features")
    op.drop_table("audio_features")
    op.drop_index(op.f("ix_sessions_patient_id"), table_name="sessions")
    op.drop_table("sessions")
    op.drop_index(op.f("ix_patients_psychologist_id"), table_name="patients")
    op.drop_index(op.f("ix_patients_display_id"), table_name="patients")
    op.drop_table("patients")
    op.drop_index(op.f("ix_users_email"), table_name="users")
    op.drop_table("users")

    sa.Enum(name="report_status").drop(op.get_bind(), checkfirst=True)
    sa.Enum(name="ai_observation_status").drop(op.get_bind(), checkfirst=True)
    sa.Enum(name="moment_type").drop(op.get_bind(), checkfirst=True)
    sa.Enum(name="modality").drop(op.get_bind(), checkfirst=True)
    sa.Enum(name="session_status").drop(op.get_bind(), checkfirst=True)
    sa.Enum(name="user_role").drop(op.get_bind(), checkfirst=True)
