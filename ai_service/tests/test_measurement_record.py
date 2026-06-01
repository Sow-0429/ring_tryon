"""較正ループ用の永続化スナップショット MeasurementRecord のテスト。

回帰特徴量(付け根幅/関節幅/指長)を保持し、正解周囲長から学習行を生成できることを検証する。
ADR-0001 に従い 号数 は保持しない(周囲長まで)。
"""
from __future__ import annotations

from datetime import datetime

from app.domain.model.calibration_sample import CalibrationSample
from app.domain.model.measurement_record import (
    FingerMeasurementSnapshot,
    MeasurementRecord,
)


def _snapshot(finger_name: str = "ring") -> FingerMeasurementSnapshot:
    return FingerMeasurementSnapshot(
        finger_name=finger_name,
        length_mm=70.0,
        base_width_mm=16.0,
        pip_width_mm=17.0,
        width_mm=17.0,
        circumference_mm=52.0,
    )


def _record(actual: int | None = None) -> MeasurementRecord:
    return MeasurementRecord(
        id="rec-1",
        created_at=datetime(2026, 5, 30, 12, 0, 0),
        calibration_method="card_id1",
        pixels_per_mm=10.0,
        handedness="Right",
        hand_confidence=0.95,
        finger_measurements={"ring": _snapshot("ring"), "index": _snapshot("index")},
        actual_ring_size_jp=actual,
    )


class TestFingerMeasurementSnapshot:
    def test_holds_regression_features(self):
        snap = _snapshot()
        assert snap.base_width_mm == 16.0
        assert snap.pip_width_mm == 17.0
        assert snap.length_mm == 70.0


class TestMeasurementRecord:
    def test_calibration_sample_for_target_finger(self):
        """正解周囲長を与えると対象指の学習行を生成する。"""
        record = _record(actual=11)

        sample = record.calibration_sample("ring", actual_circumference_mm=51.5)

        assert isinstance(sample, CalibrationSample)
        assert sample.finger_name == "ring"
        assert sample.features == (16.0, 17.0, 70.0, "ring")
        assert sample.actual_circumference_mm == 51.5

    def test_calibration_sample_missing_finger(self):
        record = _record(actual=11)
        assert record.calibration_sample("pinky", actual_circumference_mm=50.0) is None

    def test_actual_ring_size_optional(self):
        record = _record()
        assert record.actual_ring_size_jp is None
