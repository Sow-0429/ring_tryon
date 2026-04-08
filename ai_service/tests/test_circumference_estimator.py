import pytest

from app.domain.model.measurement import FingerMeasurement
from app.domain.service.circumference_estimator import (
    DEPTH_TO_WIDTH_RATIOS,
    CircumferenceEstimator,
)


class TestCircumferenceEstimator:
    def test_estimate_returns_positive(self):
        m = FingerMeasurement(
            finger_name="ring",
            length_mm=70.0,
            width_px=50.0,
            width_mm=16.0,
            ring_position_x=0, ring_position_y=0,
            finger_angle_rad=0,
        )
        estimator = CircumferenceEstimator()
        result = estimator.estimate(m)
        assert result.circumference_mm > 0

    def test_different_fingers_different_ratios(self):
        estimator = CircumferenceEstimator()
        results = {}
        for name in ["index", "middle", "ring", "pinky"]:
            m = FingerMeasurement(
                finger_name=name,
                length_mm=70.0,
                width_px=50.0,
                width_mm=16.0,
                ring_position_x=0, ring_position_y=0,
                finger_angle_rad=0,
            )
            results[name] = estimator.estimate(m).circumference_mm

        # 指ごとに異なるratioなので異なる周囲長になる
        assert len(set(round(v, 4) for v in results.values())) == len(results)

    def test_wider_finger_larger_circumference(self):
        estimator = CircumferenceEstimator()
        m_narrow = FingerMeasurement(
            finger_name="ring", length_mm=70.0,
            width_px=40.0, width_mm=12.0,
            ring_position_x=0, ring_position_y=0, finger_angle_rad=0,
        )
        m_wide = FingerMeasurement(
            finger_name="ring", length_mm=70.0,
            width_px=60.0, width_mm=18.0,
            ring_position_x=0, ring_position_y=0, finger_angle_rad=0,
        )
        assert estimator.estimate(m_wide).circumference_mm > estimator.estimate(m_narrow).circumference_mm
