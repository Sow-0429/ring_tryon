from __future__ import annotations

import statistics
from statistics import median

from app.domain.model.confidence import ConfidenceScore
from app.domain.model.measurement import FingerMeasurement
from app.domain.model.measurement_session import (
    AggregatedMeasurement,
    FingerSummary,
    FrameMeasurement,
)


class NoValidFramesError(Exception):
    """合格フレームが 1 枚も無く集約できない。"""


class FrameAggregator:
    """指スキャンの複数フレームを中央値集約し、単発ノイズを低減する。

    各指の周囲長・回帰特徴量(付け根幅/関節幅/指長/幅)をフレーム横断で中央値化し、
    フレーム間一致度(周囲長std)・有効フレーム数・品質割合から ConfidenceScore を出す。
    号数化はしない(ADR-0001)。
    """

    def aggregate(
        self,
        frames: list[FrameMeasurement],
        angle_coverage: float | None = None,
    ) -> AggregatedMeasurement:
        valid = [f for f in frames if f.accepted]
        if not valid:
            raise NoValidFramesError("No accepted frames to aggregate")

        finger_names: list[str] = []
        for name in valid[0].fingers:
            finger_names.append(name)

        aggregated_fingers: dict[str, FingerSummary] = {}
        per_finger_std: list[float] = []

        for name in finger_names:
            summaries = [f.fingers[name] for f in valid if name in f.fingers]
            if not summaries:
                continue

            circumferences = [s.circumference_mm for s in summaries]
            med_circ = median(circumferences)
            per_finger_std.append(
                statistics.pstdev(circumferences) if len(circumferences) > 1 else 0.0
            )

            rep = summaries[0].measurement
            agg_measurement = FingerMeasurement(
                finger_name=name,
                length_mm=median(s.measurement.length_mm for s in summaries),
                width_px=median(s.measurement.width_px for s in summaries),
                width_mm=median(s.measurement.width_mm for s in summaries),
                ring_position_x=rep.ring_position_x,
                ring_position_y=rep.ring_position_y,
                finger_angle_rad=rep.finger_angle_rad,
                base_width_mm=median(s.measurement.base_width_mm for s in summaries),
                pip_width_mm=median(s.measurement.pip_width_mm for s in summaries),
            )
            aggregated_fingers[name] = FingerSummary(
                measurement=agg_measurement, circumference_mm=med_circ,
            )

        representative_std = (
            sum(per_finger_std) / len(per_finger_std) if per_finger_std else 0.0
        )
        confidence = ConfidenceScore.compute(
            circumference_std_mm=representative_std,
            valid_frame_count=len(valid),
            quality_ratio=len(valid) / len(frames),
            angle_coverage=angle_coverage,
        )

        return AggregatedMeasurement(
            fingers=aggregated_fingers,
            confidence=confidence,
            frame_count=len(valid),
        )
