import numpy as np
import pytest

from app.domain.model.measurement import Scale
from app.domain.service.finger_measurer import FingerMeasurer
from tests.conftest import make_hand_landmarks


def _make_test_image(width: int = 500, height: int = 500) -> np.ndarray:
    """指を模擬した簡易テスト画像を生成。中央に明るい縦帯。"""
    img = np.zeros((height, width, 3), dtype=np.uint8)
    # 背景を暗く
    img[:, :] = (30, 30, 30)
    # 中央に肌色の帯（指を模擬）
    center_x = width // 2
    finger_width = 40
    img[:, center_x - finger_width // 2:center_x + finger_width // 2] = (200, 160, 130)
    return img


class TestFingerMeasurer:
    def test_measure_returns_measurement(self):
        image = _make_test_image()
        landmarks = make_hand_landmarks()
        scale = Scale(pixels_per_mm=5.0)
        measurer = FingerMeasurer()
        result = measurer.measure(image, landmarks, scale, "middle", 80.0)
        assert result.finger_name == "middle"
        assert result.width_mm > 0
        assert result.length_mm == 80.0

    def test_robust_median_filters_outliers(self):
        measurer = FingerMeasurer()
        values = [10.0, 11.0, 10.5, 50.0, 10.2]  # 50.0は外れ値
        result = measurer._robust_median(values)
        assert 9.0 < result < 12.0

    def test_robust_median_small_list(self):
        measurer = FingerMeasurer()
        assert measurer._robust_median([5.0, 10.0]) == 7.5

    def test_dynamic_scan_length(self):
        """scan_lengthがMCP-PIP距離に応じて動的に変わることを確認。"""
        measurer = FingerMeasurer()
        # MEASUREMENT_RATIOSの数だけ測定が行われる
        assert len(measurer.MEASUREMENT_RATIOS) == 5
