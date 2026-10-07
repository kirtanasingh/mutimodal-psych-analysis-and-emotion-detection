from collections.abc import Iterable

import numpy as np

from app.services.fusion_service import EMOTION_LABELS

DIVERGENCE_THRESHOLD = 0.5
DESCRIPTION_TEMPLATE = "{} signals showed divergence during this segment. Review recommended."
MODALITY_LABELS = {"text": "Text", "audio": "audio", "face": "facial"}


def detect_divergences(
    fusion_rows: Iterable,
    emotion_predictions_by_window: dict[tuple[float, float], dict[str, np.ndarray | None]],
) -> list[dict]:
    detected = []
    for fusion_row in fusion_rows:
        key = (fusion_row.window_start, fusion_row.window_end)
        available = {
            modality: np.asarray(vector, dtype=float)
            for modality, vector in emotion_predictions_by_window.get(key, {}).items()
            if vector is not None
        }
        if len(available) < 2:
            continue
        distances = [
            (
                1.0 - float(np.dot(left, right) / (np.linalg.norm(left) * np.linalg.norm(right))),
                first,
                second,
            )
            for index, (first, left) in enumerate(available.items())
            for second, right in list(available.items())[index + 1 :]
            if np.linalg.norm(left) > 0 and np.linalg.norm(right) > 0
        ]
        if not distances:
            continue
        score, first, second = max(distances)
        if score <= DIVERGENCE_THRESHOLD:
            continue
        involved = [first, second]
        labels = [MODALITY_LABELS[modality] for modality in involved]
        if len(involved) == 3:
            description = "Text, audio, and facial signals showed divergence during this segment. Review recommended."
        else:
            description = DESCRIPTION_TEMPLATE.format(", ".join(labels[:-1]) + " and " + labels[-1])
        detected.append({
            "window_start": fusion_row.window_start,
            "window_end": fusion_row.window_end,
            "modalities_involved": involved,
            "divergence_score": score,
            "description": description,
        })
    return detected
