"""学習エントリ train_and_save のテスト(Goアクセスはスタブ化)。"""
from __future__ import annotations

from app.domain.model.calibration_sample import CalibrationDataset, CalibrationSample
from app.domain.service.circumference_regression import CircumferenceRegressionModel
from app.training import train


def _dataset(n: int) -> CalibrationDataset:
    samples = []
    for i in range(n):
        base = 14.0 + (i % 5) * 0.5
        pip = 15.0 + (i % 3) * 0.7
        length = 60.0 + (i % 7) * 1.5
        circ = 0.5 * base + 1.2 * pip + 0.1 * length + 3.0
        samples.append(CalibrationSample("ring", base, pip, length, circ))
    return CalibrationDataset(samples=tuple(samples))


class _StubClient:
    def __init__(self, dataset: CalibrationDataset) -> None:
        self._dataset = dataset

    def fetch_dataset(self) -> CalibrationDataset:
        return self._dataset


def test_train_and_save_success(tmp_path, monkeypatch):
    monkeypatch.setattr(
        train, "CalibrationDataClient", lambda url: _StubClient(_dataset(10)),
    )
    path = str(tmp_path / "model.json")

    ok = train.train_and_save("http://go", path)

    assert ok is True
    # 保存されたモデルが読み込めて予測できる。
    model = CircumferenceRegressionModel.load(path)
    assert model.predict("ring", 16.0, 17.0, 70.0) > 0


def test_train_and_save_insufficient_data(tmp_path, monkeypatch):
    monkeypatch.setattr(
        train, "CalibrationDataClient", lambda url: _StubClient(_dataset(2)),
    )
    path = str(tmp_path / "model.json")

    ok = train.train_and_save("http://go", path)

    assert ok is False
    assert not (tmp_path / "model.json").exists()
