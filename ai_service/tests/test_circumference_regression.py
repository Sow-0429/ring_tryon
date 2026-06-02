"""較正ループの回帰モデル CircumferenceRegressionModel のテスト。

特徴量[付け根幅, 関節幅, 指長] → 実周囲長 を指種別ごとに線形回帰し、
固定比推定を学習モデルへ置換できることを検証する。
TDD red phase: app.domain.service.circumference_regression は未実装の想定。
"""
from __future__ import annotations

import pytest

from app.domain.model.calibration_sample import CalibrationDataset, CalibrationSample
from app.domain.model.measurement import FingerMeasurement
from app.domain.service.circumference_regression import (
    CircumferenceRegressionModel,
    RegressionCircumferenceEstimator,
)


def _make_dataset(coef, intercept, finger="ring", n=12):
    """circumference = coef·[base,pip,length] + intercept の合成データ。

    特徴量は互いに共線にならないよう独立に振る(回帰係数を一意に同定するため)。
    """
    samples = []
    for i in range(n):
        base = 14.0 + (i % 5) * 0.5
        pip = 15.0 + (i % 3) * 0.7
        length = 60.0 + (i % 7) * 1.5
        circ = coef[0] * base + coef[1] * pip + coef[2] * length + intercept
        samples.append(CalibrationSample(
            finger_name=finger,
            base_width_mm=base,
            pip_width_mm=pip,
            length_mm=length,
            actual_circumference_mm=circ,
        ))
    return CalibrationDataset(samples=tuple(samples))


class TestCircumferenceRegressionModel:
    def test_fit_recovers_linear_relationship(self):
        coef, intercept = (0.5, 1.2, 0.1), 3.0
        ds = _make_dataset(coef, intercept)

        model = CircumferenceRegressionModel.fit(ds)
        pred = model.predict("ring", base_width_mm=16.0, pip_width_mm=17.0, length_mm=70.0)
        expected = 0.5 * 16.0 + 1.2 * 17.0 + 0.1 * 70.0 + 3.0

        assert pred == pytest.approx(expected, abs=0.2)

    def test_per_finger_models(self):
        """指ごとに別の関係を学習する。"""
        ring = _make_dataset((0.5, 1.2, 0.1), 3.0, finger="ring")
        index = _make_dataset((0.3, 1.0, 0.2), 1.0, finger="index")
        ds = CalibrationDataset(samples=ring.samples + index.samples)

        model = CircumferenceRegressionModel.fit(ds)

        r = model.predict("ring", 16.0, 17.0, 70.0)
        i = model.predict("index", 16.0, 17.0, 70.0)
        assert r != pytest.approx(i, abs=0.5)

    def test_insufficient_data_falls_back_to_global(self):
        """指別データが足りなければ全体モデルで予測する。"""
        # ring は十分、pinky は0件 → pinky は global で予測(例外を出さない)。
        ds = _make_dataset((0.5, 1.2, 0.1), 3.0, finger="ring", n=12)
        model = CircumferenceRegressionModel.fit(ds)

        pred = model.predict("pinky", 16.0, 17.0, 70.0)
        assert pred > 0

    def test_can_fit_returns_false_for_empty(self):
        empty = CalibrationDataset(samples=())
        assert CircumferenceRegressionModel.can_fit(empty) is False


class TestRegressionCircumferenceEstimator:
    def test_estimate_uses_model(self):
        ds = _make_dataset((0.5, 1.2, 0.1), 3.0)
        model = CircumferenceRegressionModel.fit(ds)
        estimator = RegressionCircumferenceEstimator(model)

        m = FingerMeasurement(
            finger_name="ring", length_mm=70.0, width_px=170.0, width_mm=17.0,
            ring_position_x=0, ring_position_y=0, finger_angle_rad=0,
            base_width_mm=16.0, pip_width_mm=17.0,
        )
        result = estimator.estimate(m)
        expected = model.predict("ring", 16.0, 17.0, 70.0)
        assert result.circumference_mm == pytest.approx(expected, abs=1e-6)
