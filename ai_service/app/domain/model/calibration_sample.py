from __future__ import annotations

from dataclasses import dataclass
from typing import Callable


@dataclass(frozen=True)
class CalibrationSample:
    """較正ループの学習行(値オブジェクト)。

    特徴量 [付け根幅, 関節幅, 指長, 指種別] と、正解ラベルである実周囲長(mm)。
    ラベルはユーザーの実号数から導いた周囲長で、号数化(JP表)は Go 側が担うため
    Python は周囲長(mm)のみを扱う(ADR-0001)。
    """

    finger_name: str
    base_width_mm: float
    pip_width_mm: float
    length_mm: float
    actual_circumference_mm: float

    @property
    def features(self) -> tuple[float, float, float, str]:
        return (self.base_width_mm, self.pip_width_mm, self.length_mm, self.finger_name)

    @property
    def label(self) -> float:
        return self.actual_circumference_mm


Predictor = Callable[[CalibrationSample], float]


@dataclass(frozen=True)
class CalibrationDataset:
    """蓄積した学習行の集合。回帰モデルの学習・受け入れ評価の両方に使う。

    予測器(周囲長を返す関数)に対する平均絶対誤差(mm)と、許容誤差バンド内に
    収まる割合を計算する。後者は受け入れ基準 ±1号@80% の土台(1号相当の
    許容mmを与えて割合を見る)。
    """

    samples: tuple[CalibrationSample, ...]

    def __len__(self) -> int:
        return len(self.samples)

    def mean_absolute_error(self, predict: Predictor) -> float:
        if not self.samples:
            return 0.0
        total = sum(
            abs(predict(s) - s.actual_circumference_mm) for s in self.samples
        )
        return total / len(self.samples)

    def within_tolerance_ratio(self, predict: Predictor, tolerance_mm: float) -> float:
        if not self.samples:
            return 0.0
        hits = sum(
            1
            for s in self.samples
            if abs(predict(s) - s.actual_circumference_mm) <= tolerance_mm
        )
        return hits / len(self.samples)
