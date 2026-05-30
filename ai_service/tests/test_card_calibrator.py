"""ID-1カードの検出結果からピクセル/mmスケールを算出するCardCalibratorのテスト。

TDD red phase: app.domain.service.card_calibrator はまだ存在しない想定。
"""
from __future__ import annotations

import pytest

from app.domain.model.reference_object import (
    CARD_ID1_LONG_EDGE_MM,
    CARD_ID1_SHORT_EDGE_MM,
    DetectedCard,
)
from app.domain.service.card_calibrator import CardCalibrator


def _card(long_px: float, short_px: float, confidence: float = 0.9) -> DetectedCard:
    corners = (
        (0.0, 0.0),
        (long_px, 0.0),
        (long_px, short_px),
        (0.0, short_px),
    )
    return DetectedCard(corners=corners, confidence=confidence)


class TestCardCalibrator:
    def test_calibrate_basic(self):
        """長辺856px・短辺539.8px → 両軸とも約10px/mm。"""
        detected = _card(long_px=856.0, short_px=539.8)
        calibrator = CardCalibrator()

        scale = calibrator.calibrate(detected)

        assert scale.pixels_per_mm == pytest.approx(10.0, rel=1e-3)

    def test_calibrate_uses_both_axes(self):
        """長辺・短辺それぞれの推定値の平均を採用する。"""
        # 長辺由来: 856/85.60 = 10.0, 短辺由来: 269.9/53.98 = 5.0 → 平均7.5
        detected = _card(long_px=856.0, short_px=269.9)
        calibrator = CardCalibrator()

        scale = calibrator.calibrate(detected)

        long_ppm = 856.0 / CARD_ID1_LONG_EDGE_MM
        short_ppm = 269.9 / CARD_ID1_SHORT_EDGE_MM
        expected = (long_ppm + short_ppm) / 2
        assert scale.pixels_per_mm == pytest.approx(expected, rel=1e-6)
        assert scale.pixels_per_mm == pytest.approx(7.5, rel=1e-3)

    def test_calibrate_conversion(self):
        """算出スケールでpx→mm変換が正しい。"""
        detected = _card(long_px=856.0, short_px=539.8)
        calibrator = CardCalibrator()

        scale = calibrator.calibrate(detected)

        # 約10px/mm なので 50px ≒ 5mm
        assert scale.px_to_mm(50.0) == pytest.approx(5.0, rel=1e-3)

    def test_calibrate_smaller_card(self):
        """半分のサイズなら約5px/mm。"""
        detected = _card(long_px=428.0, short_px=269.9)
        calibrator = CardCalibrator()

        scale = calibrator.calibrate(detected)

        assert scale.pixels_per_mm == pytest.approx(5.0, rel=1e-3)
