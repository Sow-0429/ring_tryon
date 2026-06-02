"""較正ループの学習エントリ: Go から教師データを取得し回帰モデルを学習・保存する。

使い方:
    GO_API_URL=http://localhost:8080 CALIBRATION_MODEL_PATH=/data/model.json \
        python -m app.training.train

蓄積データが少なすぎる(回帰に必要な最小サンプル未満)場合は学習せず False を返す。
"""
from __future__ import annotations

import os

from app.domain.service.circumference_regression import CircumferenceRegressionModel
from app.infrastructure.calibration_data_client import CalibrationDataClient


def train_and_save(go_api_url: str, model_path: str) -> bool:
    """Go の教師データで回帰モデルを学習し model_path に保存する。

    学習できる十分なデータが無ければ保存せず False。成功したら True。
    """
    client = CalibrationDataClient(go_api_url)
    dataset = client.fetch_dataset()

    if not CircumferenceRegressionModel.can_fit(dataset):
        return False

    model = CircumferenceRegressionModel.fit(dataset)
    model.save(model_path)
    return True


def main() -> None:
    go_api_url = os.environ.get("GO_API_URL", "http://localhost:8080")
    model_path = os.environ.get("CALIBRATION_MODEL_PATH", "/data/calibration_model.json")

    if train_and_save(go_api_url, model_path):
        print(f"trained and saved model to {model_path}")
    else:
        print("insufficient calibration data; model not updated")


if __name__ == "__main__":
    main()
