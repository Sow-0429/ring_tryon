"""マルチフレーム中央値集約 FrameAggregator のテスト。

複数フレームの単発計測を指別に中央値集約し、不合格フレームを除外し、
ConfidenceScore 付きの集約結果を返すことを検証する。
TDD red phase: app.domain.service.frame_aggregator は未実装の想定。
"""
from __future__ import annotations

import pytest

from app.domain.model.confidence import ConfidenceScore
from app.domain.model.measurement import FingerMeasurement
from app.domain.model.measurement_session import FingerSummary, FrameMeasurement
from app.domain.service.frame_aggregator import FrameAggregator, NoValidFramesError


def _summary(circ: float, base: float = 16.0, pip: float = 17.0) -> FingerSummary:
    measurement = FingerMeasurement(
        finger_name="ring",
        length_mm=70.0,
        width_px=pip * 10,
        width_mm=pip,
        ring_position_x=100.0,
        ring_position_y=200.0,
        finger_angle_rad=0.0,
        base_width_mm=base,
        pip_width_mm=pip,
    )
    return FingerSummary(measurement=measurement, circumference_mm=circ)


def _frame(circ: float, accepted: bool = True, base: float = 16.0) -> FrameMeasurement:
    return FrameMeasurement(
        fingers={"ring": _summary(circ, base=base)}, accepted=accepted,
    )


class TestFrameAggregator:
    def test_median_circumference(self):
        frames = [_frame(50.0), _frame(52.0), _frame(54.0)]

        result = FrameAggregator().aggregate(frames)

        assert result.fingers["ring"].circumference_mm == pytest.approx(52.0)
        assert result.frame_count == 3

    def test_median_features(self):
        frames = [_frame(50.0, base=15.0), _frame(52.0, base=16.0), _frame(54.0, base=20.0)]

        result = FrameAggregator().aggregate(frames)

        assert result.fingers["ring"].measurement.base_width_mm == pytest.approx(16.0)

    def test_rejects_unaccepted_frames(self):
        """不合格フレームの外れ値は集約に含めない。"""
        frames = [
            _frame(50.0),
            _frame(52.0),
            _frame(999.0, accepted=False),  # 品質不合格・外れ値
        ]

        result = FrameAggregator().aggregate(frames)

        assert result.fingers["ring"].circumference_mm == pytest.approx(51.0)
        assert result.frame_count == 2

    def test_confidence_present_and_high_for_low_spread(self):
        frames = [_frame(51.9), _frame(52.0), _frame(52.1)]

        result = FrameAggregator().aggregate(frames)

        assert isinstance(result.confidence, ConfidenceScore)
        assert result.confidence.value > 0.5
        assert result.confidence.valid_frame_count == 3

    def test_high_spread_lowers_confidence(self):
        tight = FrameAggregator().aggregate([_frame(51.9), _frame(52.0), _frame(52.1)])
        wide = FrameAggregator().aggregate([_frame(48.0), _frame(52.0), _frame(56.0)])
        assert wide.confidence.value < tight.confidence.value

    def test_no_valid_frames_raises(self):
        frames = [_frame(50.0, accepted=False)]
        with pytest.raises(NoValidFramesError):
            FrameAggregator().aggregate(frames)
