import pytest

from app.domain.model.landmark import Point
from app.domain.service.scale_calibrator import ScaleCalibrator
from tests.conftest import make_hand_landmarks


class TestScaleCalibrator:
    def test_calibrate_basic(self):
        landmarks = make_hand_landmarks()
        calibrator = ScaleCalibrator()
        # 画像サイズ500x500で中指の長さ80mmと指定
        scale = calibrator.calibrate(landmarks, 80.0, 500, 500)
        assert scale.pixels_per_mm > 0

    def test_calibrate_uses_3d(self):
        """z座標があると3D距離が2Dより大きくなり、pixels_per_mmが大きくなる。"""
        calibrator = ScaleCalibrator()
        lm_flat = make_hand_landmarks()

        # z座標を追加したランドマーク
        points_with_z = list(lm_flat.points)
        points_with_z[9] = Point(0.48, 0.52, 0.0)   # MIDDLE_MCP
        points_with_z[10] = Point(0.48, 0.38, -0.05)  # MIDDLE_PIP
        points_with_z[11] = Point(0.48, 0.28, -0.08)  # MIDDLE_DIP
        points_with_z[12] = Point(0.48, 0.20, -0.10)  # MIDDLE_TIP
        lm_3d = make_hand_landmarks(points=points_with_z)

        scale_flat = calibrator.calibrate(lm_flat, 80.0, 500, 500)
        scale_3d = calibrator.calibrate(lm_3d, 80.0, 500, 500)

        assert scale_3d.pixels_per_mm > scale_flat.pixels_per_mm

    def test_calibrate_overlapping_landmarks(self):
        points = [Point(0.5, 0.5, 0.0)] * 21
        lm = make_hand_landmarks(points=points)
        calibrator = ScaleCalibrator()
        with pytest.raises(ValueError, match="overlap"):
            calibrator.calibrate(lm, 80.0, 500, 500)
