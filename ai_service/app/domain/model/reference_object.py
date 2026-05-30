from __future__ import annotations

import math
from dataclasses import dataclass

COIN_100_YEN_DIAMETER_MM = 22.6

# ISO/IEC 7810 ID-1 (クレジット/ICカード) の寸法
CARD_ID1_LONG_EDGE_MM = 85.60
CARD_ID1_SHORT_EDGE_MM = 53.98
CARD_ID1_ASPECT_RATIO = CARD_ID1_LONG_EDGE_MM / CARD_ID1_SHORT_EDGE_MM


@dataclass(frozen=True)
class DetectedCoin:
    center_x: float
    center_y: float
    diameter_px: float
    confidence: float


@dataclass(frozen=True)
class DetectedCard:
    """検出されたID-1カードの計測結果(計算側の内部表現)。

    corners は時計回りに TL, TR, BR, BL の順のピクセル座標 (x, y)。
    """

    corners: tuple[tuple[float, float], ...]
    confidence: float

    def __post_init__(self) -> None:
        if len(self.corners) != 4:
            raise ValueError(f"Expected 4 corners, got {len(self.corners)}")

    @staticmethod
    def _dist(a: tuple[float, float], b: tuple[float, float]) -> float:
        return math.hypot(a[0] - b[0], a[1] - b[1])

    @property
    def _width_px(self) -> float:
        tl, tr, br, bl = self.corners
        return (self._dist(tl, tr) + self._dist(bl, br)) / 2

    @property
    def _height_px(self) -> float:
        tl, tr, br, bl = self.corners
        return (self._dist(tl, bl) + self._dist(tr, br)) / 2

    @property
    def long_edge_px(self) -> float:
        return max(self._width_px, self._height_px)

    @property
    def short_edge_px(self) -> float:
        return min(self._width_px, self._height_px)

    @property
    def aspect_ratio(self) -> float:
        short = self.short_edge_px
        if short == 0:
            raise ValueError("Card short edge is zero")
        return self.long_edge_px / short

    @property
    def center_x(self) -> float:
        return sum(c[0] for c in self.corners) / 4

    @property
    def center_y(self) -> float:
        return sum(c[1] for c in self.corners) / 4
