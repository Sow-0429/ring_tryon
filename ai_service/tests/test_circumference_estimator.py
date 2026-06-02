import pytest

from app.domain.model.measurement import FingerMeasurement
from app.domain.service.circumference_estimator import (
    TIER_PREMIUM,
    TIER_STANDARD,
    DepthBasedCircumferenceEstimator,
    DepthDataRequiredError,
    EllipseFitCircumferenceEstimator,
    estimator_for_tier,
)


def _measurement(width_mm=16.0, depth_mm=None, finger="ring"):
    return FingerMeasurement(
        finger_name=finger, length_mm=70.0, width_px=160.0, width_mm=width_mm,
        ring_position_x=0, ring_position_y=0, finger_angle_rad=0,
        base_width_mm=15.0, pip_width_mm=16.0, depth_mm=depth_mm,
    )


class TestDepthBasedCircumferenceEstimator:
    def test_uses_measured_depth(self):
        estimator = DepthBasedCircumferenceEstimator()
        # 厚み=幅(円形)なら周囲長≒π*幅
        result = estimator.estimate(_measurement(width_mm=16.0, depth_mm=16.0))
        assert result.circumference_mm == pytest.approx(3.14159 * 16.0, abs=0.1)

    def test_requires_depth(self):
        estimator = DepthBasedCircumferenceEstimator()
        with pytest.raises(DepthDataRequiredError):
            estimator.estimate(_measurement(depth_mm=None))


class TestEstimatorForTier:
    def test_standard(self):
        assert isinstance(
            estimator_for_tier(TIER_STANDARD), EllipseFitCircumferenceEstimator,
        )

    def test_premium(self):
        assert isinstance(
            estimator_for_tier(TIER_PREMIUM), DepthBasedCircumferenceEstimator,
        )

    def test_unknown_defaults_to_standard(self):
        assert isinstance(
            estimator_for_tier("bogus"), EllipseFitCircumferenceEstimator,
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
        estimator = EllipseFitCircumferenceEstimator()
        result = estimator.estimate(m)
        assert result.circumference_mm > 0

    def test_different_fingers_different_ratios(self):
        estimator = EllipseFitCircumferenceEstimator()
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
        estimator = EllipseFitCircumferenceEstimator()
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
