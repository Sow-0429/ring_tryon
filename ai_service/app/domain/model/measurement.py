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

    @property
    def finger_angle_deg(self) -> float:
        return math.degrees(self.finger_angle_rad)


@dataclass(frozen=True)
class RingSize:
    circumference_mm: float

    @property
    def us_size(self) -> float:
        return round((self.circumference_mm - 36.5) / 2.55, 1)

    @property
    def eu_size(self) -> int:
        return round(self.circumference_mm)

    @property
    def jp_size(self) -> int:
        jp_table = [
            (41.0, 1), (42.0, 2), (43.0, 3), (44.0, 4), (45.0, 5),
            (46.0, 6), (47.5, 7), (48.5, 8), (49.5, 9), (50.5, 10),
            (51.5, 11), (52.5, 12), (53.5, 13), (54.5, 14), (55.5, 15),
            (56.5, 16), (57.5, 17), (58.5, 18), (60.0, 19), (61.0, 20),
            (62.0, 21), (63.0, 22), (64.0, 23), (65.0, 24), (66.0, 25),
        ]
        closest = min(jp_table, key=lambda t: abs(t[0] - self.circumference_mm))
        return closest[1]

    @property
    def jp_size_range(self) -> tuple[int, int]:
        jp = self.jp_size
        return (max(1, jp - 1), min(25, jp + 1))
