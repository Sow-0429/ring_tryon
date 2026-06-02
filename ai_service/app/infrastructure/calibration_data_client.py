from __future__ import annotations

import json
import urllib.request

from app.domain.model.calibration_sample import CalibrationDataset, CalibrationSample


class CalibrationDataClient:
    """Go の較正データ(教師データ)を取得して CalibrationDataset を組み立てる。

    Go が号数→周囲長変換まで済ませた学習行(GET /api/calibration/dataset)を受け取る。
    Python は号数表を持たない(ADR-0001/0007)。
    """

    def __init__(self, base_url: str, timeout_sec: float = 30.0) -> None:
        self._base_url = base_url.rstrip("/")
        self._timeout = timeout_sec

    def fetch_dataset(self) -> CalibrationDataset:
        url = f"{self._base_url}/api/calibration/dataset"
        with urllib.request.urlopen(url, timeout=self._timeout) as resp:  # noqa: S310
            payload = json.loads(resp.read().decode("utf-8"))
        return self.parse(payload)

    @staticmethod
    def parse(payload: list[dict]) -> CalibrationDataset:
        samples = tuple(
            CalibrationSample(
                finger_name=row["finger_name"],
                base_width_mm=float(row["base_width_mm"]),
                pip_width_mm=float(row["pip_width_mm"]),
                length_mm=float(row["length_mm"]),
                actual_circumference_mm=float(row["actual_circumference_mm"]),
            )
            for row in payload
        )
        return CalibrationDataset(samples=samples)
