from pathlib import Path
from typing import Any

import cv2
import librosa
import numpy as np
import torch
from PIL import Image
from torchvision import models, transforms
from transformers import BertConfig, BertModel, BertTokenizer

from app.config import settings

EMOTION_LABELS = ("anger", "disgust", "fear", "joy", "neutral", "sadness", "surprise")
_MODELS: dict[str, Any] | None = None
_FACE_DETECTOR = cv2.CascadeClassifier(
    str(Path(cv2.data.haarcascades) / "haarcascade_frontalface_default.xml")
)


class TextEmotionModel(torch.nn.Module):
    def __init__(self) -> None:
        super().__init__()
        self.bert = BertModel(BertConfig())
        self.dropout = torch.nn.Dropout(0.3)
        self.classifier = torch.nn.Linear(768, 7)

    def forward(self, input_ids: torch.Tensor, attention_mask: torch.Tensor) -> torch.Tensor:
        output = self.bert(input_ids=input_ids, attention_mask=attention_mask)
        return self.classifier(self.dropout(output.pooler_output))


class AudioEmotionModel(torch.nn.Module):
    def __init__(self) -> None:
        super().__init__()
        self.conv1 = torch.nn.Conv1d(40, 64, kernel_size=5)
        self.bn1 = torch.nn.BatchNorm1d(64)
        self.conv2 = torch.nn.Conv1d(64, 128, kernel_size=5)
        self.bn2 = torch.nn.BatchNorm1d(128)
        self.pool = torch.nn.MaxPool1d(2)
        self.bilstm = torch.nn.LSTM(128, 128, num_layers=2, bidirectional=True, batch_first=True)
        self.classifier = torch.nn.Linear(256, 7)

    def forward(self, features: torch.Tensor) -> torch.Tensor:
        x = self.pool(torch.relu(self.bn1(self.conv1(features))))
        x = self.pool(torch.relu(self.bn2(self.conv2(x))))
        x = x.transpose(1, 2)
        _, (_, cell_state) = self.bilstm(x)
        return self.classifier(torch.cat((cell_state[-2], cell_state[-1]), dim=1))


class FaceEmotionModel(torch.nn.Module):
    def __init__(self) -> None:
        super().__init__()
        backbone = models.resnet18(weights=None)
        self.backbone = torch.nn.Sequential(*list(backbone.children())[:-1])
        self.dropout = torch.nn.Dropout(0.3)
        self.classifier = torch.nn.Linear(512, 7)

    def forward(self, image: torch.Tensor) -> torch.Tensor:
        features = self.backbone(image).flatten(1)
        return self.classifier(self.dropout(features))


def _models_dir() -> Path:
    configured = Path(settings.models_dir)
    return configured if configured.is_absolute() else Path(__file__).resolve().parents[3] / configured


def _load_state_dict(path: Path) -> dict[str, torch.Tensor]:
    state = torch.load(path, map_location="cpu", weights_only=True)
    if not isinstance(state, dict):
        raise RuntimeError(f"Expected a state_dict in {path}, got {type(state).__name__}")
    return state


def _load_models() -> dict[str, Any]:
    root = _models_dir()
    text = TextEmotionModel()
    text.load_state_dict(_load_state_dict(root / "bert_text_model.pt"))
    audio = AudioEmotionModel()
    audio.load_state_dict(_load_state_dict(root / "cnn_bilstm_audio_model.pt"))
    face = FaceEmotionModel()
    face.load_state_dict(_load_state_dict(root / "face_cnn_model.pt"))

    import joblib

    label_encoder = joblib.load(root / "label_encoder.pkl")
    classes = tuple(str(label) for label in label_encoder.classes_)
    if classes != EMOTION_LABELS:
        raise RuntimeError(f"Label encoder classes {classes!r} do not match {EMOTION_LABELS!r}")

    tokenizer = BertTokenizer.from_pretrained("bert-base-uncased")
    image_transform = transforms.Compose(
        [
            transforms.Resize((224, 224)),
            transforms.ToTensor(),
            transforms.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225]),
        ]
    )
    for model in (text, audio, face):
        model.eval()
    return {
        "text": text,
        "audio": audio,
        "face": face,
        "tokenizer": tokenizer,
        "image_transform": image_transform,
    }


def _get_models() -> dict[str, Any]:
    global _MODELS
    if _MODELS is None:
        _MODELS = _load_models()
    return _MODELS


def _probabilities(logits: torch.Tensor) -> np.ndarray:
    return torch.softmax(logits, dim=-1).squeeze(0).numpy()


def predict_text(text: str) -> np.ndarray:
    loaded = _get_models()
    encoded = loaded["tokenizer"](
        text or "",
        return_tensors="pt",
        truncation=True,
        padding="max_length",
        max_length=64,
    )
    with torch.inference_mode():
        return _probabilities(loaded["text"](encoded["input_ids"], encoded["attention_mask"]))


def _load_audio(audio_source: str | Path | np.ndarray | tuple[str | Path, float, float]) -> np.ndarray:
    start = end = None
    if isinstance(audio_source, tuple):
        audio_source, start, end = audio_source
    if isinstance(audio_source, np.ndarray):
        audio = audio_source.astype(np.float32, copy=False)
    else:
        audio, _ = librosa.load(str(audio_source), sr=16000, mono=True)
        if start is not None:
            audio = audio[max(0, int(start * 16000)) : max(0, int(end * 16000))]
    mfcc = librosa.feature.mfcc(y=audio, sr=16000, n_mfcc=40)
    if mfcc.shape[1] < 200:
        mfcc = np.pad(mfcc, ((0, 0), (0, 200 - mfcc.shape[1])))
    else:
        mfcc = mfcc[:, :200]
    return mfcc.astype(np.float32)


def predict_audio(
    audio_slice_path_or_array: str | Path | np.ndarray | tuple[str | Path, float, float],
) -> np.ndarray:
    loaded = _get_models()
    features = torch.from_numpy(_load_audio(audio_slice_path_or_array)).unsqueeze(0)
    with torch.inference_mode():
        return _probabilities(loaded["audio"](features))


def predict_face(frame_path: str | Path) -> np.ndarray | None:
    frame = cv2.imread(str(frame_path))
    if frame is None:
        raise FileNotFoundError(f"Frame file does not exist or is unreadable: {frame_path}")
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    faces = _FACE_DETECTOR.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=5, minSize=(30, 30))
    if len(faces) == 0:
        return None
    x, y, width, height = max(faces, key=lambda box: box[2] * box[3])
    crop = cv2.cvtColor(frame[y : y + height, x : x + width], cv2.COLOR_BGR2RGB)
    loaded = _get_models()
    image = loaded["image_transform"](Image.fromarray(crop)).unsqueeze(0)
    with torch.inference_mode():
        return _probabilities(loaded["face"](image))
