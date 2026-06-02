from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from app.domain.model.calibration_sample import CalibrationDataset
from app.domain.model.measurement import CircumferenceEstimate, FingerMeasurement

# 線形回帰の係数は [base, pip, length, intercept] の4自由度。
_MIN_SAMPLES = 4


@dataclass(frozen=True)
class CircumferenceRegressionModel:
    """指種別ごとの線形回帰係数。較正ループの正解データから学習する。

    予測式: circumference = w0*base + w1*pip + w2*length + w3。
    指別データが不足する指は全体(global)係数で予測する。
    """

    per_finger: dict[str, tuple[float, float, float, float]]
    global_coef: tuple[float, float, float, float]

    @staticmethod
    def can_fit(dataset: CalibrationDataset) -> bool:
        return len(dataset) >= _MIN_SAMPLES

    @classmethod
    def fit(cls, dataset: CalibrationDataset) -> "CircumferenceRegressionModel":
        if not cls.can_fit(dataset):
            raise ValueError(
                f"need at least {_MIN_SAMPLES} samples to fit, got {len(dataset)}"
            )

        global_coef = _solve(list(dataset.samples))

        per_finger: dict[str, tuple[float, float, float, float]] = {}
        by_finger: dict[str, list] = {}
        for s in dataset.samples:
            by_finger.setdefault(s.finger_name, []).append(s)
        for finger, samples in by_finger.items():
            if len(samples) >= _MIN_SAMPLES:
                per_finger[finger] = _solve(samples)

        return cls(per_finger=per_finger, global_coef=global_coef)

    def predict(
        self,
        finger_name: str,
        base_width_mm: float,
        pip_width_mm: float,
        length_mm: float,
    ) -> float:
        coef = self.per_finger.get(finger_name, self.global_coef)
        w0, w1, w2, w3 = coef
        return w0 * base_width_mm + w1 * pip_width_mm + w2 * length_mm + w3

    def to_dict(self) -> dict:
        return {
            "per_finger": {k: list(v) for k, v in self.per_finger.items()},
            "global_coef": list(self.global_coef),
        }

    @classmethod
    def from_dict(cls, data: dict) -> "CircumferenceRegressionModel":
        per_finger = {
            k: (float(v[0]), float(v[1]), float(v[2]), float(v[3]))
            for k, v in data.get("per_finger", {}).items()
        }
        g = data["global_coef"]
        return cls(
            per_finger=per_finger,
            global_coef=(float(g[0]), float(g[1]), float(g[2]), float(g[3])),
        )

    def save(self, path: str) -> None:
        import json
        from pathlib import Path

        Path(path).write_text(json.dumps(self.to_dict()))

    @classmethod
    def load(cls, path: str) -> "CircumferenceRegressionModel":
        import json
        from pathlib import Path

        return cls.from_dict(json.loads(Path(path).read_text()))


def _solve(samples: list) -> tuple[float, float, float, float]:
    """最小二乗で [base, pip, length, 1] → circumference の係数を解く。"""
    x = np.array(
        [[s.base_width_mm, s.pip_width_mm, s.length_mm, 1.0] for s in samples],
        dtype=np.float64,
    )
    y = np.array([s.actual_circumference_mm for s in samples], dtype=np.float64)
    coef, *_ = np.linalg.lstsq(x, y, rcond=None)
    return (float(coef[0]), float(coef[1]), float(coef[2]), float(coef[3]))


class RegressionCircumferenceEstimator:
    """学習済み回帰モデルで周囲長を推定する戦略(較正後の標準ティア)。"""

    def __init__(self, model: CircumferenceRegressionModel) -> None:
        self._model = model

    def estimate(self, measurement: FingerMeasurement) -> CircumferenceEstimate:
        circumference = self._model.predict(
            measurement.finger_name,
            measurement.base_width_mm,
            measurement.pip_width_mm,
            measurement.length_mm,
        )
        return CircumferenceEstimate(circumference_mm=circumference)
