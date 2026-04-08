"""将来のDB蓄積用データモデル。定義のみ、永続化は未実装。"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class FingerMeasurementSnapshot:
    finger_name: str
    length_mm: float
    width_mm: float
    circumference_mm: float
    estimated_ring_size_jp: int


@dataclass(frozen=True)
class MeasurementRecord:
    id: str
    created_at: datetime
    calibration_method: str
    pixels_per_mm: float
    handedness: str
    hand_confidence: float
    finger_measurements: dict[str, FingerMeasurementSnapshot]
    actual_ring_size_jp: int | None = None
    user_age: int | None = None
    user_gender: str | None = None
