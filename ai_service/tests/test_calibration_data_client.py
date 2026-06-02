"""Go の学習データ取得クライアント CalibrationDataClient と回帰モデル永続化のテスト。"""
from __future__ import annotations

import pytest

from app.domain.model.calibration_sample import CalibrationDataset, CalibrationSample
from app.domain.service.circumference_regression import CircumferenceRegressionModel
from app.infrastructure.calibration_data_client import CalibrationDataClient


class TestCalibrationDataClientParse:
    def test_parse_builds_dataset(self):
        payload = [
            {"finger_name": "ring", "base_width_mm": 16.0, "pip_width_mm": 17.0,
             "length_mm": 70.0, "actual_circumference_mm": 52.5},
            {"finger_name": "index", "base_width_mm": 15.0, "pip_width_mm": 15.5,
             "length_mm": 68.0, "actual_circumference_mm": 50.5},
        ]
        ds = CalibrationDataClient.parse(payload)

        assert isinstance(ds, CalibrationDataset)
        assert len(ds) == 2
        assert ds.samples[0].finger_name == "ring"
        assert ds.samples[0].actual_circumference_mm == 52.5
        assert ds.samples[0].features == (16.0, 17.0, 70.0, "ring")

    def test_parse_empty(self):
        assert len(CalibrationDataClient.parse([])) == 0


class TestRegressionModelPersistence:
    def _dataset(self):
        samples = []
        for i in range(8):
            base = 14.0 + (i % 5) * 0.5
            pip = 15.0 + (i % 3) * 0.7
            length = 60.0 + (i % 7) * 1.5
            circ = 0.5 * base + 1.2 * pip + 0.1 * length + 3.0
            samples.append(CalibrationSample("ring", base, pip, length, circ))
        return CalibrationDataset(samples=tuple(samples))

    def test_to_from_dict_roundtrip(self):
        model = CircumferenceRegressionModel.fit(self._dataset())
        restored = CircumferenceRegressionModel.from_dict(model.to_dict())

        a = model.predict("ring", 16.0, 17.0, 70.0)
        b = restored.predict("ring", 16.0, 17.0, 70.0)
        assert a == pytest.approx(b, abs=1e-9)

    def test_save_load(self, tmp_path):
        model = CircumferenceRegressionModel.fit(self._dataset())
        path = str(tmp_path / "model.json")
        model.save(path)
        loaded = CircumferenceRegressionModel.load(path)

        assert loaded.predict("ring", 16.0, 17.0, 70.0) == pytest.approx(
            model.predict("ring", 16.0, 17.0, 70.0), abs=1e-9,
        )
