from collections.abc import Mapping

import numpy as np

EMOTION_LABELS = ("anger", "disgust", "fear", "joy", "neutral", "sadness", "surprise")
DEFAULT_WEIGHTS = {"text": 0.5, "audio": 0.3, "face": 0.2}


class FusionEngine:
    def __init__(self, weights: Mapping[str, float] | None = None) -> None:
        configured = dict(weights or DEFAULT_WEIGHTS)
        if any(weight < 0 for weight in configured.values()) or not any(configured.values()):
            raise ValueError("Fusion weights must be non-negative and include a positive weight")
        self.weights = {modality: float(configured.get(modality, 0.0)) for modality in DEFAULT_WEIGHTS}

    def fuse_window(self, predictions: dict[str, np.ndarray | None]) -> dict:
        available = {
            modality: np.asarray(vector, dtype=np.float64)
            for modality, vector in predictions.items()
            if vector is not None
        }
        if not available:
            return {
                "probabilities": None,
                "dominant_emotion": None,
                "confidence": None,
                "modalities_used": [],
                "weights_used": {},
            }
        for modality, vector in available.items():
            if vector.shape != (len(EMOTION_LABELS),):
                raise ValueError(f"{modality} probability vector must have shape (7,), got {vector.shape}")
            if not np.isfinite(vector).all() or (vector < 0).any() or vector.sum() <= 0:
                raise ValueError(f"{modality} probability vector must be finite and non-negative")
            available[modality] = vector / vector.sum()

        weights = {modality: self.weights.get(modality, 0.0) for modality in available}
        weight_total = sum(weights.values())
        if weight_total <= 0:
            raise ValueError("Available modalities have no positive fusion weight")
        weights = {modality: weight / weight_total for modality, weight in weights.items()}
        probabilities = sum(weights[modality] * vector for modality, vector in available.items())
        probabilities = probabilities / probabilities.sum()
        dominant_index = int(probabilities.argmax())
        return {
            "probabilities": probabilities,
            "dominant_emotion": EMOTION_LABELS[dominant_index],
            "confidence": float(probabilities[dominant_index]),
            "modalities_used": list(available),
            "weights_used": weights,
        }

    def smooth_sequence(self, fusion_rows: list[dict], window_size: int = 3) -> list[dict]:
        if window_size <= 0 or window_size % 2 == 0:
            raise ValueError("window_size must be a positive odd number")
        if not fusion_rows:
            return []
        radius = window_size // 2
        result = []
        for index, row in enumerate(fusion_rows):
            start = max(0, index - radius)
            end = min(len(fusion_rows), index + radius + 1)
            probabilities = np.mean(
                [np.asarray(item["probabilities"], dtype=np.float64) for item in fusion_rows[start:end]],
                axis=0,
            )
            probabilities = probabilities / probabilities.sum()
            dominant_index = int(probabilities.argmax())
            result.append(
                {
                    **row,
                    "probabilities": probabilities,
                    "dominant_emotion": EMOTION_LABELS[dominant_index],
                    "confidence": float(probabilities[dominant_index]),
                }
            )
        return result
