import json
import subprocess
from pathlib import Path


def extract_audio(video_path: str | Path, output_wav_path: str | Path) -> None:
    source = Path(video_path)
    destination = Path(output_wav_path)
    if not source.is_file():
        raise FileNotFoundError(f"Video file does not exist: {source}")
    destination.parent.mkdir(parents=True, exist_ok=True)
    result = subprocess.run(
        [
            "ffmpeg",
            "-i",
            str(source),
            "-ar",
            "16000",
            "-ac",
            "1",
            "-y",
            str(destination),
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        raise RuntimeError(f"FFmpeg audio extraction failed: {result.stderr[-2000:]}")


def probe_duration(video_path: str | Path) -> float:
    source = Path(video_path)
    if not source.is_file():
        raise FileNotFoundError(f"Video file does not exist: {source}")
    result = subprocess.run(
        [
            "ffprobe",
            "-v",
            "error",
            "-show_entries",
            "format=duration",
            "-of",
            "json",
            str(source),
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        raise RuntimeError(f"FFprobe duration probe failed: {result.stderr[-2000:]}")
    try:
        duration = float(json.loads(result.stdout)["format"]["duration"])
    except (KeyError, TypeError, ValueError, json.JSONDecodeError) as exc:
        raise RuntimeError("FFprobe returned no valid video duration") from exc
    if duration < 0:
        raise RuntimeError("FFprobe returned a negative video duration")
    return duration


def sample_frames(
    video_path: str | Path,
    output_dir: str | Path,
    interval_seconds: float = 2.5,
) -> list[dict[str, float | str]]:
    import cv2

    if interval_seconds <= 0:
        raise ValueError("Frame interval must be greater than zero")
    source = Path(video_path)
    if not source.is_file():
        raise FileNotFoundError(f"Video file does not exist: {source}")

    destination = Path(output_dir)
    destination.mkdir(parents=True, exist_ok=True)
    capture = cv2.VideoCapture(str(source))
    if not capture.isOpened():
        raise RuntimeError(f"OpenCV could not open video: {source}")

    fps = capture.get(cv2.CAP_PROP_FPS)
    frame_count = int(capture.get(cv2.CAP_PROP_FRAME_COUNT))
    if fps <= 0 or frame_count <= 0:
        capture.release()
        raise RuntimeError("Video has no readable frame rate or frames")

    sampled: list[dict[str, float | str]] = []
    next_timestamp = 0.0
    frame_index = 0
    try:
        while frame_index < frame_count:
            success, frame = capture.read()
            if not success:
                break
            timestamp = frame_index / fps
            if timestamp + (1 / fps) >= next_timestamp:
                output_path = destination / f"frame_{timestamp:.1f}s.jpg"
                if not cv2.imwrite(str(output_path), frame):
                    raise RuntimeError(f"OpenCV could not write frame: {output_path}")
                sampled.append({"timestamp_seconds": timestamp, "file_path": str(output_path)})
                next_timestamp += interval_seconds
            frame_index += 1
    finally:
        capture.release()

    if not sampled:
        raise RuntimeError("No video frames could be sampled")
    return sampled
