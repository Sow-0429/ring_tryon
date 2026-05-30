"""手シルエットの二値マスクを返す HandSegmenter のテスト。

背景/照明に依存せず、ランドマークが指す手領域を前景として抽出することを検証する。
TDD red phase: app.infrastructure.hand_segmenter はまだ存在しない想定。
"""
from __future__ import annotations

import numpy as np

from app.infrastructure.hand_segmenter import HandSegmenter
from tests.conftest import make_hand_landmarks


def _draw_hand(img: np.ndarray, color: tuple[int, int, int]) -> None:
    """make_hand_landmarks の配置に合うよう手領域(手のひら+指帯)を塗る。"""
    h, w = img.shape[:2]
    # 手のひら
    img[int(0.50 * h):int(0.92 * h), int(0.34 * w):int(0.68 * w)] = color
    # 4本の指帯
    for cx in (0.40, 0.48, 0.56, 0.63):
        x0 = int((cx - 0.025) * w)
        x1 = int((cx + 0.025) * w)
        img[int(0.18 * h):int(0.58 * h), x0:x1] = color


def _make_hand_on_dark_bg(w: int = 500, h: int = 500) -> np.ndarray:
    img = np.full((h, w, 3), 30, dtype=np.uint8)
    _draw_hand(img, (200, 160, 130))
    return img


def _make_hand_on_bright_bg(w: int = 500, h: int = 500) -> np.ndarray:
    img = np.full((h, w, 3), 245, dtype=np.uint8)
    _draw_hand(img, (70, 60, 55))
    return img


class TestHandSegmenter:
    def test_returns_bool_mask_of_image_shape(self):
        image = _make_hand_on_dark_bg()
        landmarks = make_hand_landmarks()

        mask = HandSegmenter().segment(image, landmarks)

        assert mask.shape == (500, 500)
        assert mask.dtype == bool

    def test_hand_region_is_foreground(self):
        """指の中心はマスク内、背景の隅はマスク外。"""
        image = _make_hand_on_dark_bg()
        landmarks = make_hand_landmarks()

        mask = HandSegmenter().segment(image, landmarks)

        # 中指中心 (0.48w, 0.4h) あたり
        assert mask[int(0.40 * 500), int(0.48 * 500)]
        # 背景の隅
        assert not mask[5, 5]
        assert not mask[5, 495]

    def test_background_independent_on_bright_bg(self):
        """明るい背景に暗い手でも前景を正しく抽出する(極性非依存)。"""
        image = _make_hand_on_bright_bg()
        landmarks = make_hand_landmarks()

        mask = HandSegmenter().segment(image, landmarks)

        assert mask[int(0.40 * 500), int(0.48 * 500)]
        assert not mask[5, 5]

    def test_single_connected_component(self):
        """背景の孤立ノイズは前景に含めない(ランドマークを含む成分のみ採用)。"""
        image = _make_hand_on_dark_bg()
        # 背景隅にノイズblob
        image[10:40, 10:40] = (200, 160, 130)
        landmarks = make_hand_landmarks()

        mask = HandSegmenter().segment(image, landmarks)

        assert not mask[25, 25]
        assert mask[int(0.40 * 500), int(0.48 * 500)]
