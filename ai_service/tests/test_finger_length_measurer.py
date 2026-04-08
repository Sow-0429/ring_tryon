import pytest

from app.domain.model.measurement import Scale
from app.domain.service.finger_length_measurer import FingerLengthMeasurer
from tests.conftest import make_hand_landmarks


class TestFingerLengthMeasurer:
    def test_measure_returns_positive(self):
        landmarks = make_hand_landmarks()
        scale = Scale(pixels_per_mm=5.0)
        measurer = FingerLengthMeasurer()
        length = measurer.measure(landmarks, scale, "middle", 500, 500)
        assert length > 0

    def test_middle_longer_than_pinky(self):
        landmarks = make_hand_landmarks()
        scale = Scale(pixels_per_mm=5.0)
        measurer = FingerLengthMeasurer()
        middle = measurer.measure(landmarks, scale, "middle", 500, 500)
        pinky = measurer.measure(landmarks, scale, "pinky", 500, 500)
        assert middle > pinky

    def test_all_fingers_measurable(self):
        landmarks = make_hand_landmarks()
        scale = Scale(pixels_per_mm=5.0)
        measurer = FingerLengthMeasurer()
        for name in ["index", "middle", "ring", "pinky"]:
            length = measurer.measure(landmarks, scale, name, 500, 500)
            assert length > 0
