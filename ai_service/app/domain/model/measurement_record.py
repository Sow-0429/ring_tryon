"""較正ループ用の永続化データモデル。定義のみ、永続化は Go 側の別作業。"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from app.domain.model.calibration_sample import CalibrationSample


@dataclass(frozen=True)
class FingerMeasurementSnapshot:
    """1 指分の計測スナップショット。回帰特徴量(付け根幅/関節幅/指長)を含む。

    号数は持たない(ADR-0001: Python は周囲長まで、号数化は Go)。
    """

    finger_name: str
    length_mm: float
    base_width_mm: float
    pip_width_mm: float
    width_mm: float
    circumference_mm: float


@dataclass(frozen=True)
class MeasurementRecord:
    id: str
    created_at: datetime
    calibration_method: str
    pixels_per_mm: float
    handedness: str
    hand_confidence: float
    finger_measurements: dict[str, FingerMeasurementSnapshot]
    # マルチフレーム集約の有効フレーム数と総合信頼度(単発計測なら1/None)。
    frame_count: int = 1
    confidence: float | None = None
    # ユーザーの実号数(較正ラベルの素)。号数→周囲長変換は Go が担う。
    actual_ring_size_jp: int | None = None
    user_age: int | None = None
    user_gender: str | None = None

    def calibration_sample(
        self, finger_name: str, actual_circumference_mm: float,
    ) -> CalibrationSample | None:
        """対象指の学習行を生成する。正解周囲長は外部(Go)から与える。"""
        snapshot = self.finger_measurements.get(finger_name)
        if snapshot is None:
            return None
        return CalibrationSample(
            finger_name=finger_name,
            base_width_mm=snapshot.base_width_mm,
            pip_width_mm=snapshot.pip_width_mm,
            length_mm=snapshot.length_mm,
            actual_circumference_mm=actual_circumference_mm,
        )
