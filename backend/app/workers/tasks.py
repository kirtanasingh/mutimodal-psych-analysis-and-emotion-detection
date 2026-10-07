from pathlib import Path

import numpy as np

from app.config import settings
from app.db.session import SessionLocal
from sqlalchemy import select

from app.models.clinical import (
    EmotionPrediction,
    FusionResult,
    Modality,
    Session as ClinicalSession,
    SessionStatus,
    SignalDivergence,
)
from app.services.video_service import extract_audio, probe_duration, sample_frames
from app.workers.celery_app import celery_app


def _upload_root() -> Path:
    configured = Path(settings.upload_dir)
    return configured if configured.is_absolute() else Path(__file__).resolve().parents[3] / configured


def _set_steps(session: ClinicalSession, **updates: bool) -> None:
    session.processing_steps = {**(session.processing_steps or {}), **updates}


@celery_app.task(name="process_session_video")
def process_session_video(session_id: int) -> None:
    with SessionLocal() as db:
        session = db.get(ClinicalSession, session_id)
        try:
            if session is None or session.uploaded_video is None:
                raise RuntimeError("Session or uploaded video was not found")

            video_path = Path(session.uploaded_video.file_path)
            session.status = SessionStatus.extracting_audio
            session.processing_error = None
            db.commit()

            session_dir = _upload_root() / str(session.patient_id) / str(session.id)
            extract_audio(video_path, session_dir / "audio.wav")
            duration = probe_duration(video_path)
            session.duration_seconds = round(duration)
            session.uploaded_video.duration_seconds = round(duration)
            _set_steps(session, audio_extracted=True)
            db.commit()

            session.status = SessionStatus.extracting_frames
            db.commit()
            sample_frames(video_path, session_dir / "frames")
            _set_steps(session, frames_extracted=True)
            session.status = SessionStatus.transcribing
            db.commit()

            from app.services.transcription_service import save_transcript, transcribe_audio

            segments = transcribe_audio(session_dir / "audio.wav")
            save_transcript(
                db,
                session.id,
                getattr(segments, "language", None),
                segments,
            )
            _set_steps(session, transcript_generated=True)
            session.status = SessionStatus.analyzing_emotions
            db.commit()

            from app.ml.model_loader import predict_audio, predict_face, predict_text
            from app.services.windowing_service import build_analysis_windows

            for window in build_analysis_windows(session.id):
                predictions = [(Modality.text, predict_text(window["text"]))]
                predictions.append(
                    (
                        Modality.audio,
                        predict_audio(
                            (
                                window["audio_slice_path"],
                                window["audio_start"],
                                window["audio_end"],
                            )
                        ),
                    )
                )
                face_predictions = [
                    prediction
                    for frame_path in window["frame_paths"]
                    if (prediction := predict_face(frame_path)) is not None
                ]
                if face_predictions:
                    predictions.append((Modality.face, sum(face_predictions) / len(face_predictions)))
                for modality, probabilities in predictions:
                    probabilities = probabilities / probabilities.sum()
                    dominant_index = int(probabilities.argmax())
                    db.add(
                        EmotionPrediction(
                            session_id=session.id,
                            window_start=window["window_start"],
                            window_end=window["window_end"],
                            modality=modality,
                            probabilities_json={
                                label: float(probabilities[index])
                                for index, label in enumerate(
                                    ("anger", "disgust", "fear", "joy", "neutral", "sadness", "surprise")
                                )
                            },
                            dominant_emotion=(
                                "anger",
                                "disgust",
                                "fear",
                                "joy",
                                "neutral",
                                "sadness",
                                "surprise",
                            )[dominant_index],
                            confidence=float(probabilities[dominant_index]),
                        )
                    )
            _set_steps(session, emotion_analysis_complete=True)
            session.status = SessionStatus.fusion_pending
            db.commit()

            session.status = SessionStatus.fusing
            db.commit()

            from app.services.fusion_service import EMOTION_LABELS, FusionEngine

            prediction_rows = db.scalars(
                select(EmotionPrediction)
                .where(EmotionPrediction.session_id == session.id)
                .order_by(EmotionPrediction.window_start, EmotionPrediction.id)
            ).all()
            grouped: dict[tuple[float, float], dict[str, object]] = {}
            for row in prediction_rows:
                window = grouped.setdefault(
                    (row.window_start, row.window_end),
                    {
                        "window_start": row.window_start,
                        "window_end": row.window_end,
                        "predictions": {"text": None, "audio": None, "face": None},
                    },
                )
                window["predictions"][row.modality.value] = np.array(
                    [row.probabilities_json[label] for label in EMOTION_LABELS], dtype=float
                )

            engine = FusionEngine()
            fusion_rows = []
            for window in grouped.values():
                fused = engine.fuse_window(window["predictions"])
                if fused["probabilities"] is not None:
                    fusion_rows.append(
                        {
                            "window_start": window["window_start"],
                            "window_end": window["window_end"],
                            **fused,
                        }
                    )
            for row in engine.smooth_sequence(fusion_rows):
                db.add(
                    FusionResult(
                        session_id=session.id,
                        window_start=row["window_start"],
                        window_end=row["window_end"],
                        probabilities_json={
                            label: float(row["probabilities"][index])
                            for index, label in enumerate(
                                EMOTION_LABELS
                            )
                        },
                        dominant_emotion=row["dominant_emotion"],
                        confidence=row["confidence"],
                        modalities_used_json=row["modalities_used"],
                        weights_used_json=row["weights_used"],
                    )
                )
            _set_steps(session, fusion_complete=True)
            db.flush()
            try:
                with db.begin_nested():
                    from app.services.divergence_service import detect_divergences

                    prediction_vectors = {}
                    for row in prediction_rows:
                        prediction_vectors.setdefault((row.window_start, row.window_end), {})[
                            row.modality.value
                        ] = np.array(
                            [row.probabilities_json[label] for label in EMOTION_LABELS],
                            dtype=float,
                        )
                    db.query(SignalDivergence).filter(
                        SignalDivergence.session_id == session.id
                    ).delete(synchronize_session=False)
                    stored_fusions = db.scalars(
                        select(FusionResult)
                        .where(FusionResult.session_id == session.id)
                        .order_by(FusionResult.window_start)
                    ).all()
                    for divergence in detect_divergences(stored_fusions, prediction_vectors):
                        db.add(
                            SignalDivergence(
                                session_id=session.id,
                                window_start=divergence["window_start"],
                                window_end=divergence["window_end"],
                                modalities_involved_json=divergence["modalities_involved"],
                                divergence_score=divergence["divergence_score"],
                                description=divergence["description"],
                            )
                        )
                _set_steps(session, divergence_detection_complete=True)
            except Exception as divergence_error:
                _set_steps(session, divergence_detection_complete=False)
                print(f"Divergence detection failed for session {session.id}: {divergence_error}")
            session.status = SessionStatus.analysis_complete
            db.commit()
        except Exception as exc:
            if session is not None:
                db.rollback()
                session.status = SessionStatus.upload_failed
                session.processing_error = str(exc)
                db.commit()
            raise
