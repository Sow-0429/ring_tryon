import pytest

from app.domain.model.reference_object import COIN_100_YEN_DIAMETER_MM, DetectedCoin
from app.domain.service.coin_calibrator import CoinCalibrator


class TestCoinCalibrator:
    def test_calibrate_basic(self):
        detected = DetectedCoin(
            center_x=250.0,
            center_y=250.0,
            diameter_px=113.0,
            confidence=0.9,
        )
        calibrator = CoinCalibrator()
        scale = calibrator.calibrate(detected)
        expected_ppm = 113.0 / COIN_100_YEN_DIAMETER_MM
        assert scale.pixels_per_mm == pytest.approx(expected_ppm, rel=1e-6)

    def test_calibrate_larger_coin(self):
        detected = DetectedCoin(
            center_x=100.0,
            center_y=100.0,
            diameter_px=226.0,
            confidence=0.95,
        )
        calibrator = CoinCalibrator()
        scale = calibrator.calibrate(detected)
        assert scale.pixels_per_mm == pytest.approx(10.0, rel=1e-3)

    def test_calibrate_converts_correctly(self):
        detected = DetectedCoin(
            center_x=0, center_y=0,
            diameter_px=45.2,
            confidence=0.8,
        )
        calibrator = CoinCalibrator()
        scale = calibrator.calibrate(detected)
        # 45.2px = 22.6mm なので 1mm = 2px
        assert scale.pixels_per_mm == pytest.approx(2.0, rel=1e-6)
        assert scale.px_to_mm(20.0) == pytest.approx(10.0, rel=1e-3)
