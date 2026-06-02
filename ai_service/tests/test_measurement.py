import pytest

from app.domain.model.measurement import (
    CircumferenceEstimate,
    FingerMeasurement,
    Scale,
)


class TestScale:
    def test_px_to_mm(self):
        scale = Scale(pixels_per_mm=10.0)
        assert scale.px_to_mm(50.0) == pytest.approx(5.0)

    def test_mm_to_px(self):
        scale = Scale(pixels_per_mm=10.0)
        assert scale.mm_to_px(5.0) == pytest.approx(50.0)

    def test_invalid_scale(self):
        with pytest.raises(ValueError):
            Scale(pixels_per_mm=0.0)
        with pytest.raises(ValueError):
            Scale(pixels_per_mm=-1.0)


class TestCircumferenceEstimate:
    def test_holds_circumference(self):
        # 号数化(JP/US/EU)は Go の責務(ADR-0001)。Python は周囲長のみ持つ。
        est = CircumferenceEstimate(circumference_mm=50.5)
        assert est.circumference_mm == 50.5


class TestFingerMeasurement:
    def test_angle_deg(self):
        import math
        m = FingerMeasurement(
            finger_name="ring",
            length_mm=70.0,
            width_px=50.0,
            width_mm=15.0,
            ring_position_x=100.0,
            ring_position_y=200.0,
            finger_angle_rad=math.pi / 4,
        )
        assert m.finger_angle_deg == pytest.approx(45.0)
