import math

from app.domain.model.measurement import FingerMeasurement, RingSize

DEPTH_TO_WIDTH_RATIOS: dict[str, float] = {
    "index": 0.80,
    "middle": 0.82,
    "ring": 0.85,
    "pinky": 0.75,
}

DEFAULT_DEPTH_TO_WIDTH_RATIO = 0.80


class CircumferenceEstimator:
    def estimate(self, measurement: FingerMeasurement) -> RingSize:
        ratio = DEPTH_TO_WIDTH_RATIOS.get(
            measurement.finger_name, DEFAULT_DEPTH_TO_WIDTH_RATIO,
        )
        width_mm = measurement.width_mm
        a = width_mm / 2
        b = (width_mm * ratio) / 2
        circumference = math.pi * (
            3 * (a + b) - math.sqrt((3 * a + b) * (a + 3 * b))
        )
        return RingSize(circumference_mm=circumference)
