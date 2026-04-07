from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from app.domain.model.landmark import HandLandmarks
from app.domain.model.measurement import FingerMeasurement, RingSize, Scale
from app.domain.service.circumference_estimator import CircumferenceEstimator
from app.domain.service.finger_measurer import FingerMeasurer
from app.domain.service.scale_calibrator import ScaleCalibrator
from app.infrastructure.hand_detector import MediaPipeHandDetector

FINGER_NAMES = ["index", "middle", "ring", "pinky"]


@dataclass
class FingerResult:
    measurement: FingerMeasurement
    ring_size: RingSize


@dataclass
class AnalyzeHandResult:
    landmarks: HandLandmarks
    scale: Scale
    fingers: dict[str, FingerResult]


class AnalyzeHandUsecase:
    def __init__(
        self,
        detector: MediaPipeHandDetector,
        calibrator: ScaleCalibrator,
        measurer: FingerMeasurer,
        estimator: CircumferenceEstimator,
    ) -> None:
        self._detector = detector
        self._calibrator = calibrator
        self._measurer = measurer
        self._estimator = estimator

    def execute(
        self,
        image: np.ndarray,
        middle_finger_length_mm: float,
    ) -> AnalyzeHandResult:
        landmarks = self._detector.detect(image)
        if landmarks is None:
            raise HandNotDetectedError("No hand detected in image")

        h, w = image.shape[:2]
        scale = self._calibrator.calibrate(landmarks, middle_finger_length_mm, w, h)

        fingers: dict[str, FingerResult] = {}
        for finger_name in FINGER_NAMES:
            measurement = self._measurer.measure(image, landmarks, scale, finger_name)
            ring_size = self._estimator.estimate(measurement)
            fingers[finger_name] = FingerResult(
                measurement=measurement,
                ring_size=ring_size,
            )

        return AnalyzeHandResult(
            landmarks=landmarks,
            scale=scale,
            fingers=fingers,
        )


class HandNotDetectedError(Exception):
    pass
