from __future__ import annotations

from dataclasses import dataclass

COIN_100_YEN_DIAMETER_MM = 22.6


@dataclass(frozen=True)
class DetectedCoin:
    center_x: float
    center_y: float
    diameter_px: float
    confidence: float
