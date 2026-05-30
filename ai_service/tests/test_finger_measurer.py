import numpy as np
import pytest

from app.domain.model.measurement import Scale
from app.domain.service.finger_measurer import FingerMeasurer
from tests.conftest import make_hand_landmarks


def _uniform_band_mask(width_px: int = 40) -> np.ndarray:
    """中指(垂直)を覆う一様な幅の指帯マスク。

    make_hand_landmarks の中指は MCP(0.48,0.52)→PIP(0.48,0.38)で垂直に伸びる。
    付け根〜PIP領域を覆う x 中心240・指定幅の縦帯を立てる。
    """
    mask = np.zeros((500, 500), dtype=bool)
    cx = int(0.48 * 500)
    half = width_px // 2
    mask[170:290, cx - half:cx + half] = True
    return mask


def _wider_pip_mask() -> np.ndarray:
    """PIP側がより太いマスク(付け根30px / PIP50px)。"""
    mask = np.zeros((500, 500), dtype=bool)
    cx = int(0.48 * 500)
    # 付け根領域 (y は MCP=260 寄り) 幅30
    mask[230:275, cx - 15:cx + 15] = True
    # PIP領域 (y=190 付近) 幅50
    mask[170:230, cx - 25:cx + 25] = True
    return mask


class TestFingerMeasurer:
    def test_measure_returns_measurement(self):
        mask = _uniform_band_mask(width_px=40)
        landmarks = make_hand_landmarks()
        scale = Scale(pixels_per_mm=5.0)

        result = FingerMeasurer().measure(mask, landmarks, scale, "middle", 80.0)

        assert result.finger_name == "middle"
        assert result.length_mm == 80.0
        assert result.width_mm > 0

    def test_width_matches_mask_band(self):
        """一様40pxの帯なら幅≒40px=8mm(scale=5px/mm)。"""
        mask = _uniform_band_mask(width_px=40)
        landmarks = make_hand_landmarks()
        scale = Scale(pixels_per_mm=5.0)

        result = FingerMeasurer().measure(mask, landmarks, scale, "middle", 80.0)

        assert result.width_px == pytest.approx(40, abs=6)
        assert result.width_mm == pytest.approx(8.0, abs=1.2)

    def test_adopts_max_of_base_and_pip(self):
        """付け根30px・PIP50pxなら、最大円周となるPIP側(50px≒10mm)を採用。"""
        mask = _wider_pip_mask()
        landmarks = make_hand_landmarks()
        scale = Scale(pixels_per_mm=5.0)

        result = FingerMeasurer().measure(mask, landmarks, scale, "middle", 80.0)

        assert result.pip_width_mm == pytest.approx(10.0, abs=1.5)
        assert result.base_width_mm == pytest.approx(6.0, abs=1.5)
        # 採用幅は両者の最大
        assert result.width_mm == pytest.approx(result.pip_width_mm, abs=1e-6)
        assert result.width_mm >= result.base_width_mm

    def test_robust_median_filters_outliers(self):
        measurer = FingerMeasurer()
        values = [10.0, 11.0, 10.5, 50.0, 10.2]  # 50.0は外れ値
        result = measurer._robust_median(values)
        assert 9.0 < result < 12.0

    def test_robust_median_small_list(self):
        measurer = FingerMeasurer()
        assert measurer._robust_median([5.0, 10.0]) == 7.5
