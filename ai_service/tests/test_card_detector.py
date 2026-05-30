"""ISO/IEC 7810 ID-1 カード(85.60×53.98mm)を基準物として検出するCardDetectorのテスト。

TDD red phase: app.infrastructure.card_detector / app.domain.model.reference_object
の DetectedCard はまだ存在しない想定。
"""
from __future__ import annotations

import cv2
import numpy as np
import pytest

from app.domain.model.reference_object import (
    CARD_ID1_ASPECT_RATIO,
    CARD_ID1_LONG_EDGE_MM,
    CARD_ID1_SHORT_EDGE_MM,
    DetectedCard,
)
from app.infrastructure.card_detector import CardDetector


def _make_image_with_card(
    image_w: int = 600,
    image_h: int = 500,
    top_left: tuple[int, int] = (140, 150),
    card_w: int = 317,
    card_h: int = 200,
    bg: int = 240,
    fg: tuple[int, int, int] = (60, 60, 60),
) -> np.ndarray:
    """明るい背景に暗いカード矩形を描画したテスト画像。

    card_w/card_h = 317/200 = 1.585 ≒ ID-1 のアスペクト比(85.60/53.98)。
    """
    img = np.ones((image_h, image_w, 3), dtype=np.uint8) * bg
    x, y = top_left
    cv2.rectangle(img, (x, y), (x + card_w, y + card_h), fg, -1)
    return img


def _make_image_with_square(
    image_w: int = 500,
    image_h: int = 500,
    top_left: tuple[int, int] = (120, 120),
    side: int = 250,
) -> np.ndarray:
    """カードではない正方形(アスペクト比1.0)を描画した画像。"""
    img = np.ones((image_h, image_w, 3), dtype=np.uint8) * 240
    x, y = top_left
    cv2.rectangle(img, (x, y), (x + side, y + side), (60, 60, 60), -1)
    return img


def _make_blank_image(image_w: int = 500, image_h: int = 500) -> np.ndarray:
    return np.ones((image_h, image_w, 3), dtype=np.uint8) * 200


class TestCardDetector:
    def test_detect_card_returns_result(self):
        """ID-1比の矩形を含む画像でカードを検出できる。"""
        image = _make_image_with_card()
        detector = CardDetector()

        result = detector.detect(image)

        assert result is not None
        assert isinstance(result, DetectedCard)

    def test_detect_card_edge_lengths(self):
        """検出した長辺/短辺のピクセル長が描画サイズと一致する。"""
        image = _make_image_with_card(card_w=317, card_h=200)
        detector = CardDetector()

        result = detector.detect(image)

        assert result is not None
        assert result.long_edge_px == pytest.approx(317, abs=15)
        assert result.short_edge_px == pytest.approx(200, abs=15)

    def test_detect_card_center(self):
        """検出した中心が矩形中心付近にある。"""
        image = _make_image_with_card(top_left=(140, 150), card_w=317, card_h=200)
        detector = CardDetector()

        result = detector.detect(image)

        assert result is not None
        assert result.center_x == pytest.approx(140 + 317 / 2, abs=15)
        assert result.center_y == pytest.approx(150 + 200 / 2, abs=15)

    def test_detect_card_aspect_ratio(self):
        """検出カードのアスペクト比がID-1規格に近い。"""
        image = _make_image_with_card()
        detector = CardDetector()

        result = detector.detect(image)

        assert result is not None
        assert result.aspect_ratio == pytest.approx(CARD_ID1_ASPECT_RATIO, abs=0.1)

    def test_reject_square_not_card(self):
        """アスペクト比が規格から外れる正方形はカードとして検出しない。"""
        image = _make_image_with_square()
        detector = CardDetector()

        result = detector.detect(image)

        assert result is None

    def test_detect_no_card(self):
        """矩形のない画像ではNoneを返す。"""
        image = _make_blank_image()
        detector = CardDetector()

        result = detector.detect(image)

        assert result is None

    def test_confidence_in_range(self):
        """信頼度は0.0〜1.0の範囲。"""
        image = _make_image_with_card()
        detector = CardDetector()

        result = detector.detect(image)

        assert result is not None
        assert 0.0 <= result.confidence <= 1.0


class TestDetectedCardGeometry:
    """DetectedCard値オブジェクトの幾何プロパティ。"""

    def _card(self, long_px: float, short_px: float) -> DetectedCard:
        # corners は時計回りに TL, TR, BR, BL の順
        corners = (
            (0.0, 0.0),
            (long_px, 0.0),
            (long_px, short_px),
            (0.0, short_px),
        )
        return DetectedCard(corners=corners, confidence=0.9)

    def test_long_and_short_edge(self):
        card = self._card(long_px=856.0, short_px=539.8)

        assert card.long_edge_px == pytest.approx(856.0, rel=1e-6)
        assert card.short_edge_px == pytest.approx(539.8, rel=1e-6)

    def test_center(self):
        card = self._card(long_px=856.0, short_px=539.8)

        assert card.center_x == pytest.approx(428.0, rel=1e-6)
        assert card.center_y == pytest.approx(269.9, rel=1e-6)

    def test_aspect_ratio(self):
        card = self._card(long_px=856.0, short_px=539.8)

        assert card.aspect_ratio == pytest.approx(CARD_ID1_ASPECT_RATIO, abs=0.01)

    def test_requires_four_corners(self):
        with pytest.raises(ValueError):
            DetectedCard(corners=((0.0, 0.0), (1.0, 0.0), (1.0, 1.0)), confidence=0.9)

    def test_id1_constants(self):
        assert CARD_ID1_LONG_EDGE_MM == pytest.approx(85.60)
        assert CARD_ID1_SHORT_EDGE_MM == pytest.approx(53.98)
        assert CARD_ID1_ASPECT_RATIO == pytest.approx(85.60 / 53.98, rel=1e-6)
