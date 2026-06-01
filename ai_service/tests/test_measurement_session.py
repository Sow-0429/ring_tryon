"""計測結果を束ねる集約 MeasurementSession のテスト。

指別の計測+周囲長とメタ情報を保持し、永続化スナップショット(MeasurementRecord)と
較正学習行を導出できることを検証する。
TDD red phase: app.domain.model.measurement_session は未実装の想定。
"""
from __future__ import annotations

from datetime import datetime

from app.domain.model.confidence import ConfidenceScore
from app.domain.model.measurement import FingerMeasurement
from app.domain.model.measurement_record import MeasurementRecord
from app.domain.model.measurement_session import (
    AggregatedMeasurement,
    FingerSummary,
    MeasurementSession,
)


def _measurement(finger_name: str = "ring") -> FingerMeasurement:
    return FingerMeasurement(
        finger_name=finger_name,
        length_mm=70.0,
        width_px=170.0,
        width_mm=17.0,
        ring_position_x=100.0,
        ring_position_y=200.0,
        finger_angle_rad=0.0,
        base_width_mm=16.0,
        pip_width_mm=17.0,
    )


def _session() -> MeasurementSession:
    return MeasurementSession(
        calibration_method="card_id1",
        pixels_per_mm=10.0,
        handedness="Right",
        hand_confidence=0.95,
        fingers={
            "ring": FingerSummary(measurement=_measurement("ring"), circumference_mm=52.0),
            "index": FingerSummary(measurement=_measurement("index"), circumference_mm=48.0),
        },
    )


class TestMeasurementSession:
    def test_to_record_carries_features(self):
        session = _session()

        record = session.to_record(
            record_id="rec-1",
            created_at=datetime(2026, 5, 30, 12, 0, 0),
            actual_ring_size_jp=11,
        )

        assert isinstance(record, MeasurementRecord)
        assert record.calibration_method == "card_id1"
        assert record.pixels_per_mm == 10.0
        assert record.actual_ring_size_jp == 11
        ring = record.finger_measurements["ring"]
        assert ring.base_width_mm == 16.0
        assert ring.pip_width_mm == 17.0
        assert ring.circumference_mm == 52.0

    def test_record_to_calibration_sample_end_to_end(self):
        """セッション → 記録 → 学習行 の一連がつながる。"""
        session = _session()
        record = session.to_record(
            record_id="rec-1",
            created_at=datetime(2026, 5, 30, 12, 0, 0),
            actual_ring_size_jp=11,
        )

        sample = record.calibration_sample("ring", actual_circumference_mm=51.5)

        assert sample is not None
        assert sample.features == (16.0, 17.0, 70.0, "ring")
        assert sample.label == 51.5

    def test_to_record_without_actual_label(self):
        session = _session()
        record = session.to_record(
            record_id="rec-2",
            created_at=datetime(2026, 5, 30, 12, 0, 0),
        )
        assert record.actual_ring_size_jp is None

    def test_from_aggregation_carries_confidence(self):
        """集約結果からセッションを構築すると信頼度とフレーム数が保持される。"""
        confidence = ConfidenceScore.compute(
            circumference_std_mm=0.2, valid_frame_count=5, quality_ratio=1.0,
        )
        aggregated = AggregatedMeasurement(
            fingers={"ring": FingerSummary(_measurement("ring"), circumference_mm=52.0)},
            confidence=confidence,
            frame_count=5,
        )

        session = MeasurementSession.from_aggregation(
            calibration_method="card_id1",
            pixels_per_mm=10.0,
            handedness="Right",
            hand_confidence=0.95,
            aggregated=aggregated,
        )

        assert session.confidence is confidence
        assert session.frame_count == 5
        record = session.to_record(
            record_id="rec-3", created_at=datetime(2026, 5, 30, 12, 0, 0),
        )
        assert record.finger_measurements["ring"].circumference_mm == 52.0
        # 集約のフレーム数・信頼度が記録(=migration列)に伝播する
        assert record.frame_count == 5
        assert record.confidence == confidence.value
