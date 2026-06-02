from __future__ import annotations

import math
from dataclasses import dataclass


@dataclass(frozen=True)
class Scale:
    pixels_per_mm: float

    def __post_init__(self) -> None:
        if self.pixels_per_mm <= 0:
            raise ValueError("pixels_per_mm must be positive")

    def px_to_mm(self, pixels: float) -> float:
        return pixels / self.pixels_per_mm

    def mm_to_px(self, mm: float) -> float:
        return mm * self.pixels_per_mm


@dataclass(frozen=True)
class FingerMeasurement:
    finger_name: str
    length_mm: float
    width_px: float
    width_mm: float
    ring_position_x: float
    ring_position_y: float
    finger_angle_rad: float
    base_width_mm: float = 0.0
    pip_width_mm: float = 0.0
    # 深度センサ(LiDAR/TrueDepth)で実測した指の厚み(mm)。標準ティアでは None。
    depth_mm: float | None = None

    @property
    def finger_angle_deg(self) -> float:
        return math.degrees(self.finger_angle_rad)


@dataclass(frozen=True)
class CircumferenceEstimate:
    """推定した指の周囲長(mm)。号数化(JP表)は Go が唯一の真実の源(ADR-0001)。"""

    circumference_mm: float
