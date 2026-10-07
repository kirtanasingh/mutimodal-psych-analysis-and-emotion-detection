from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.clinical import FusionResult, SignalDivergence
from app.services.fusion_service import EMOTION_LABELS


def _time(seconds: float) -> str:
    return f"{int(seconds // 60)}:{int(seconds % 60):02d}"


def generate_session_summary(db: Session, session_id: int) -> str:
    rows = list(db.scalars(
        select(FusionResult)
        .where(FusionResult.session_id == session_id)
        .order_by(FusionResult.window_start)
    ))
    divergence_count = len(list(db.scalars(
        select(SignalDivergence).where(SignalDivergence.session_id == session_id)
    )))
    if not rows:
        return "No fused model signals are available for this session."
    averages = {
        emotion: sum(float(row.probabilities_json.get(emotion, 0)) for row in rows) / len(rows)
        for emotion in EMOTION_LABELS
    }
    dominant = max(averages, key=averages.get)
    best_start = best_end = 0.0
    current_start = current_end = None
    for row in rows:
        if row.dominant_emotion == dominant:
            if current_start is None:
                current_start = row.window_start
            current_end = row.window_end
        elif current_start is not None:
            if current_end - current_start > best_end - best_start:
                best_start, best_end = current_start, current_end
            current_start = current_end = None
    if current_start is not None and current_end - current_start > best_end - best_start:
        best_start, best_end = current_start, current_end
    start, end = best_start, best_end
    first = f"{dominant.capitalize()}-associated signal was most prominent between {_time(start)} and {_time(end)}."
    second = (
        f"{divergence_count} segment(s) showed cross-modal signal divergence and may warrant review."
        if divergence_count
        else "No cross-modal signal divergence was detected in this session."
    )
    return f"{first} {second}"
