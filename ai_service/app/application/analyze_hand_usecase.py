from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from app.domain.model.calibration import (
    CalibrationInput,
    CoinCalibrationInput,
    FingerCalibrationInput,
)
from app.domain.model.landmark import HandLandmarks
from app.domain.model.measurement import FingerMeasurement, RingSize, Scale
from app.domain.service.circumference_estimator import CircumferenceEstimator
from app.domain.service.coin_calibrator import CoinCalibrator
from app.domain.service.finger_length_measurer import FingerLengthMeasurer
from app.domain.service.finger_measurer import FingerMeasurer
from app.domain.service.scale_calibrator import ScaleCalibrator
from app.infrastructure.coin_detector import CoinDetector
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
    calibration_method: str
    fingers: dict[str, FingerResult]


class AnalyzeHandUsecase:
    def __init__(
        self,
        detector: MediaPipeHandDetector,
        calibrator: ScaleCalibrator,
        coin_detector: CoinDetector,
        coin_calibrator: CoinCalibrator,
        measurer: FingerMeasurer,
        length_measurer: FingerLengthMeasurer,
        estimator: CircumferenceEstimator,
    ) -> None:
        self._detector = detector
        self._calibrator = calibrator
        self._coin_detector = coin_detector
        self._coin_calibrator = coin_calibrator
        self._measurer = measurer
        self._length_measurer = length_measurer
        self._estimator = estimator

    def execute(
        self,
        image: np.ndarray,
        calibration_input: CalibrationInput,
    ) -> AnalyzeHandResult:
        landmarks = self._detector.detect(image)
        if landmarks is None:
            raise HandNotDetectedError("No hand detected in image")

        h, w = image.shape[:2]
        scale, method = self._resolve_scale(image, landmarks, calibration_input, w, h)

        fingers: dict[str, FingerResult] = {}
        for finger_name in FINGER_NAMES:
            length_mm = self._length_measurer.measure(
                landmarks, scale, finger_name, w, h,
            )
            measurement = self._measurer.measure(
                image, landmarks, scale, finger_name, length_mm,
            )
            ring_size = self._estimator.estimate(measurement)
            fingers[finger_name] = FingerResult(
                measurement=measurement,
                ring_size=ring_size,
            )

        return AnalyzeHandResult(
            landmarks=landmarks,
            scale=scale,
            calibration_method=method,
            fingers=fingers,
        )

    def _resolve_scale(
        self,
        image: np.ndarray,
        landmarks: HandLandmarks,
        calibration_input: CalibrationInput,
        w: int,
        h: int,
    ) -> tuple[Scale, str]:
        if isinstance(calibration_input, FingerCalibrationInput):
            scale = self._calibrator.calibrate(
                landmarks, calibration_input.middle_finger_length_mm, w, h,
            )
            return scale, "finger_length"

        if isinstance(calibration_input, CoinCalibrationInput):
            detected = self._coin_detector.detect(image)
            if detected is None:
                raise CoinNotDetectedError(
                    "No coin detected in image. "
                    "Place a 100-yen coin next to your hand."
                )
            scale = self._coin_calibrator.calibrate(detected)
            return scale, "coin_100_yen"

        raise ValueError(f"Unknown calibration input: {type(calibration_input)}")


class HandNotDetectedError(Exception):
    pass


class CoinNotDetectedError(Exception):
    pass
