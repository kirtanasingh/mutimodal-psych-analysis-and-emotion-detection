from pydantic import BaseModel, ConfigDict


class TranscriptSegmentOut(BaseModel):
    id: int
    start_time: float
    end_time: float
    speaker_label: str | None
    text: str

    model_config = ConfigDict(from_attributes=True)


class TranscriptOut(BaseModel):
    id: int
    language: str | None
    segments: list[TranscriptSegmentOut]

    model_config = ConfigDict(from_attributes=True)
