from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from app.domain.model.confidence import ConfidenceScore
from app.domain.model.measurement import FingerMeasurement
from app.domain.model.measurement_record import (
    FingerMeasurementSnapshot,
    MeasurementRecord,
)


@dataclass(frozen=True)
class FingerSummary:
    """1 指分の計測と、そこから推定した周囲長(mm)。"""

    measurement: FingerMeasurement
    circumference_mm: float


@dataclass(frozen=True)
class FrameMeasurement:
    """指スキャン動画の 1 フレーム分の計測結果。

    accepted は品質ゲート(Phase2)の合否。不合格フレームは集約から除外する。
    """

    fingers: dict[str, FingerSummary]
    accepted: bool = True


@dataclass(frozen=True)
class AggregatedMeasurement:
    """複数フレームを中央値集約した結果と、その信頼度。"""

    fingers: dict[str, FingerSummary]
    confidence: ConfidenceScore
    frame_count: int


@dataclass(frozen=True)
class MeasurementSession:
    """1 回の計測を束ねる集約根。

    指別の計測+周囲長と撮影メタ情報を保持する。永続化スナップショット
    (MeasurementRecord)や較正学習行は、この集約から導出する。
    マルチフレーム集約(Phase4)では複数フレームの集約結果を入力にこの集約を作る。
    """

    calibration_method: str
    pixels_per_mm: float
    handedness: str
    hand_confidence: float
    fingers: dict[str, FingerSummary]
    confidence: ConfidenceScore | None = None
    frame_count: int = 1

    @classmethod
    def from_aggregation(
        cls,
        calibration_method: str,
        pixels_per_mm: float,
        handedness: str,
        hand_confidence: float,
        aggregated: "AggregatedMeasurement",
    ) -> "MeasurementSession":
        return cls(
            calibration_method=calibration_method,
            pixels_per_mm=pixels_per_mm,
            handedness=handedness,
            hand_confidence=hand_confidence,
            fingers=aggregated.fingers,
            confidence=aggregated.confidence,
            frame_count=aggregated.frame_count,
        )

    def to_record(
        self,
        record_id: str,
        created_at: datetime,
        actual_ring_size_jp: int | None = None,
        user_age: int | None = None,
        user_gender: str | None = None,
    ) -> MeasurementRecord:
        snapshots = {
            name: FingerMeasurementSnapshot(
                finger_name=name,
                length_mm=summary.measurement.length_mm,
                base_width_mm=summary.measurement.base_width_mm,
                pip_width_mm=summary.measurement.pip_width_mm,
                width_mm=summary.measurement.width_mm,
                circumference_mm=summary.circumference_mm,
            )
            for name, summary in self.fingers.items()
        }
        return MeasurementRecord(
            id=record_id,
            created_at=created_at,
            calibration_method=self.calibration_method,
            pixels_per_mm=self.pixels_per_mm,
            handedness=self.handedness,
            hand_confidence=self.hand_confidence,
            finger_measurements=snapshots,
            frame_count=self.frame_count,
            confidence=self.confidence.value if self.confidence else None,
            actual_ring_size_jp=actual_ring_size_jp,
            user_age=user_age,
            user_gender=user_gender,
        )
