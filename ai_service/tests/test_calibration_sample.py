"""較正ループの学習行 CalibrationSample とデータセット CalibrationDataset のテスト。

特徴量[付け根幅, 関節幅, 指長, 指種別] → 実周囲長(ラベル) を 1 行とし、
予測器に対する平均絶対誤差(mm)と許容mm内割合(=±1号@80%の土台)を検証する。
ADR-0001 に従い 号数 は扱わず、ラベルは周囲長(mm)で表す。
TDD red phase: app.domain.model.calibration_sample は未実装の想定。
"""
from __future__ import annotations

import pytest

from app.domain.model.calibration_sample import CalibrationDataset, CalibrationSample


def _sample(
    finger_name: str = "ring",
    base: float = 16.0,
    pip: float = 17.0,
    length: float = 70.0,
    actual: float = 52.0,
) -> CalibrationSample:
    return CalibrationSample(
        finger_name=finger_name,
        base_width_mm=base,
        pip_width_mm=pip,
        length_mm=length,
        actual_circumference_mm=actual,
    )


class TestCalibrationSample:
    def test_features_order(self):
        """特徴量は [付け根幅, 関節幅, 指長, 指種別] の順。"""
        s = _sample(base=16.0, pip=17.0, length=70.0, finger_name="ring")
        assert s.features == (16.0, 17.0, 70.0, "ring")

    def test_label_is_circumference(self):
        s = _sample(actual=52.0)
        assert s.label == 52.0


class TestCalibrationDataset:
    def test_len(self):
        ds = CalibrationDataset(samples=(_sample(), _sample()))
        assert len(ds) == 2

    def test_mean_absolute_error(self):
        """予測が常に actual+2mm なら MAE は 2.0。"""
        ds = CalibrationDataset(
            samples=(_sample(actual=50.0), _sample(actual=54.0)),
        )
        mae = ds.mean_absolute_error(lambda s: s.actual_circumference_mm + 2.0)
        assert mae == pytest.approx(2.0)

    def test_within_tolerance_ratio(self):
        """誤差0,1.5,3.0mmの3件、許容2.0mmなら2/3が合格。"""
        samples = (
            _sample(actual=50.0),
            _sample(actual=50.0),
            _sample(actual=50.0),
        )
        ds = CalibrationDataset(samples=samples)
        offsets = iter([0.0, 1.5, 3.0])
        predict = lambda s: s.actual_circumference_mm + next(offsets)  # noqa: E731
        ratio = ds.within_tolerance_ratio(predict, tolerance_mm=2.0)
        assert ratio == pytest.approx(2 / 3)

    def test_within_tolerance_empty_dataset(self):
        ds = CalibrationDataset(samples=())
        assert ds.within_tolerance_ratio(lambda s: 0.0, tolerance_mm=1.0) == 0.0
