from __future__ import annotations

from dataclasses import dataclass
from dataclasses import replace as dataclass_replace
from typing import Callable

import numpy as np

from app.domain.model.calibration import (
    CalibrationInput,
    CardCalibrationInput,
    CoinCalibrationInput,
    FingerCalibrationInput,
)
from app.domain.model.landmark import HandLandmarks
from app.domain.model.measurement import FingerMeasurement, Scale
from app.domain.model.measurement_session import (
    AggregatedMeasurement,
    FingerSummary,
    FrameMeasurement,
    MeasurementSession,
)
from app.domain.service.card_calibrator import CardCalibrator
from app.domain.service.circumference_estimator import (
    TIER_STANDARD,
    CircumferenceEstimator,
    DepthBasedCircumferenceEstimator,
)
from app.domain.service.frame_aggregator import FrameAggregator, NoValidFramesError
from app.domain.service.quality_gate import QualityGate
from app.domain.service.coin_calibrator import CoinCalibrator
from app.domain.service.finger_length_measurer import FingerLengthMeasurer
from app.domain.service.finger_measurer import FingerMeasurer
from app.domain.service.scale_calibrator import ScaleCalibrator
from app.infrastructure.card_detector import CardDetector
from app.infrastructure.coin_detector import CoinDetector
from app.infrastructure.hand_detector import MediaPipeHandDetector
from app.infrastructure.hand_segmenter import HandSegmenter

FINGER_NAMES = ["index", "middle", "ring", "pinky"]


@dataclass
class FingerResult:
    measurement: FingerMeasurement
    circumference_mm: float


@dataclass
class FrameMeta:
    calibration_method: str
    pixels_per_mm: float
    handedness: str
    hand_confidence: float


@dataclass
class AnalyzeScanResult:
    session: MeasurementSession
    total_frames: int
    accepted_frames: int


@dataclass
class AnalyzeHandResult:
    landmarks: HandLandmarks
    scale: Scale
    calibration_method: str
    fingers: dict[str, FingerResult]

    def to_session(self) -> MeasurementSession:
        """較正ループ/永続化用の集約に変換する(永続化は Go 側)。"""
        return MeasurementSession(
            calibration_method=self.calibration_method,
            pixels_per_mm=self.scale.pixels_per_mm,
            handedness=self.landmarks.handedness,
            hand_confidence=self.landmarks.confidence,
            fingers={
                name: FingerSummary(
                    measurement=fr.measurement,
                    circumference_mm=fr.ring_size.circumference_mm,
                )
                for name, fr in self.fingers.items()
            },
        )


class AnalyzeHandUsecase:
    def __init__(
        self,
        detector: MediaPipeHandDetector,
        calibrator: ScaleCalibrator,
        coin_detector: CoinDetector,
        coin_calibrator: CoinCalibrator,
        card_detector: CardDetector,
        card_calibrator: CardCalibrator,
        quality_gate: QualityGate,
        segmenter: HandSegmenter,
        measurer: FingerMeasurer,
        length_measurer: FingerLengthMeasurer,
        estimator_selector: Callable[[str], CircumferenceEstimator],
        aggregator: FrameAggregator,
    ) -> None:
        self._detector = detector
        self._calibrator = calibrator
        self._coin_detector = coin_detector
        self._coin_calibrator = coin_calibrator
        self._card_detector = card_detector
        self._card_calibrator = card_calibrator
        self._quality_gate = quality_gate
        self._segmenter = segmenter
        self._measurer = measurer
        self._length_measurer = length_measurer
        self._select_estimator = estimator_selector
        self._aggregator = aggregator

    def execute(
        self,
        image: np.ndarray,
        calibration_input: CalibrationInput,
        tier: str = TIER_STANDARD,
        depth_mm: float | None = None,
    ) -> AnalyzeHandResult:
        landmarks = self._detector.detect(image)
        if landmarks is None:
            raise HandNotDetectedError("No hand detected in image")

        assessment = self._quality_gate.evaluate(image, landmarks)
        if not assessment.is_acceptable:
            raise LowQualityImageError(assessment.failure_messages)

        h, w = image.shape[:2]
        scale, method = self._resolve_scale(image, landmarks, calibration_input, w, h)

        # 深度実測が与えられた場合は固定比を排した深度ベース推定を使う。
        if depth_mm is not None and depth_mm > 0:
            estimator: CircumferenceEstimator = DepthBasedCircumferenceEstimator()
        else:
            estimator = self._select_estimator(tier)
        summaries = self._measure_fingers(
            image, landmarks, scale, w, h, estimator, depth_mm,
        )
        fingers = {
            name: FingerResult(
                measurement=s.measurement,
                circumference_mm=s.circumference_mm,
            )
            for name, s in summaries.items()
        }

        return AnalyzeHandResult(
            landmarks=landmarks,
            scale=scale,
            calibration_method=method,
            fingers=fingers,
        )

    def execute_scan(
        self,
        images: list[np.ndarray],
        calibration_input: CalibrationInput,
    ) -> AnalyzeScanResult:
        """指スキャンの複数フレームを処理し、中央値集約した結果を返す。

        1 枚も合格フレームが無い場合は LowQualityImageError を送出する。
        """
        estimator = self._select_estimator(TIER_STANDARD)
        frames: list[FrameMeasurement] = []
        metas: list[FrameMeta] = []
        for image in images:
            frame, meta = self._analyze_frame(image, calibration_input, estimator)
            frames.append(frame)
            if frame.accepted and meta is not None:
                metas.append(meta)

        try:
            aggregated: AggregatedMeasurement = self._aggregator.aggregate(frames)
        except NoValidFramesError:
            raise LowQualityImageError(
                ["有効なフレームがありません。手を平らに置き、明るい場所で撮り直してください"]
            )

        meta = metas[0]
        session = MeasurementSession.from_aggregation(
            calibration_method=meta.calibration_method,
            pixels_per_mm=meta.pixels_per_mm,
            handedness=meta.handedness,
            hand_confidence=meta.hand_confidence,
            aggregated=aggregated,
        )
        return AnalyzeScanResult(
            session=session,
            total_frames=len(images),
            accepted_frames=aggregated.frame_count,
        )

    def _analyze_frame(
        self,
        image: np.ndarray,
        calibration_input: CalibrationInput,
        estimator: CircumferenceEstimator,
    ) -> tuple[FrameMeasurement, FrameMeta | None]:
        """1 フレームを解析する。検出/較正/品質で失敗したフレームは accepted=False。"""
        landmarks = self._detector.detect(image)
        if landmarks is None:
            return FrameMeasurement(fingers={}, accepted=False), None

        h, w = image.shape[:2]
        try:
            scale, method = self._resolve_scale(
                image, landmarks, calibration_input, w, h,
            )
        except (CoinNotDetectedError, CardNotDetectedError):
            return FrameMeasurement(fingers={}, accepted=False), None

        accepted = self._quality_gate.evaluate(image, landmarks).is_acceptable
        summaries = self._measure_fingers(image, landmarks, scale, w, h, estimator)
        meta = FrameMeta(
            calibration_method=method,
            pixels_per_mm=scale.pixels_per_mm,
            handedness=landmarks.handedness,
            hand_confidence=landmarks.confidence,
        )
        return FrameMeasurement(fingers=summaries, accepted=accepted), meta

    def _measure_fingers(
        self,
        image: np.ndarray,
        landmarks: HandLandmarks,
        scale: Scale,
        w: int,
        h: int,
        estimator: CircumferenceEstimator,
        depth_mm: float | None = None,
    ) -> dict[str, FingerSummary]:
        mask = self._segmenter.segment(image, landmarks)
        summaries: dict[str, FingerSummary] = {}
        for finger_name in FINGER_NAMES:
            length_mm = self._length_measurer.measure(
                landmarks, scale, finger_name, w, h,
            )
            measurement = self._measurer.measure(
                mask, landmarks, scale, finger_name, length_mm,
            )
            if depth_mm is not None and depth_mm > 0:
                measurement = dataclass_replace(measurement, depth_mm=depth_mm)
            estimate = estimator.estimate(measurement)
            summaries[finger_name] = FingerSummary(
                measurement=measurement,
                circumference_mm=estimate.circumference_mm,
            )
        return summaries

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

        if isinstance(calibration_input, CardCalibrationInput):
            detected_card = self._card_detector.detect(image)
            if detected_card is None:
                raise CardNotDetectedError(
                    "No ID-1 card detected in image. "
                    "Place a credit/IC card next to your hand."
                )
            scale = self._card_calibrator.calibrate(detected_card)
            return scale, "card_id1"

        raise ValueError(f"Unknown calibration input: {type(calibration_input)}")


class HandNotDetectedError(Exception):
    pass


class CoinNotDetectedError(Exception):
    pass


class CardNotDetectedError(Exception):
    pass


class LowQualityImageError(Exception):
    """撮影品質が不合格。messages はユーザー向けの実用的な指示の一覧。"""

    def __init__(self, messages: list[str]) -> None:
        self.messages = messages
        super().__init__("; ".join(messages) or "Image quality check failed")
