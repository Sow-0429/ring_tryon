from app.domain.model.measurement import FingerMeasurement, RingSize


class CircumferenceEstimator:
    def estimate(self, measurement: FingerMeasurement) -> RingSize:
        return RingSize.from_finger_width(measurement.width_mm)
