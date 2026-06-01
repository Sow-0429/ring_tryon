from __future__ import annotations

from dataclasses import dataclass

# フレーム間一致度: 周囲長の標準偏差がこの値(mm)以上で一致度0とみなす。
AGREEMENT_STD_MAX_MM = 3.0
# フレーム被覆: この枚数で被覆1.0(飽和)とみなす有効フレーム数。
FRAME_COVERAGE_TARGET = 5


def _clamp01(x: float) -> float:
    return max(0.0, min(1.0, x))


@dataclass(frozen=True)
class ConfidenceScore:
    """マルチフレーム集約の総合信頼度(値オブジェクト)。

    フレーム間一致度(周囲長std)・有効フレーム数・品質割合・(任意)角度カバレッジを
    [0,1] に正規化し、利用可能な成分の平均で総合値を出す。製品UXでは号数レンジの
    広さや実物確認の促し方の判断に使う(ADR-0004)。
    """

    value: float
    agreement: float
    frame_coverage: float
    quality_ratio: float
    valid_frame_count: int
    angle_coverage: float | None = None

    @classmethod
    def compute(
        cls,
        circumference_std_mm: float,
        valid_frame_count: int,
        quality_ratio: float,
        angle_coverage: float | None = None,
    ) -> "ConfidenceScore":
        agreement = _clamp01(1.0 - circumference_std_mm / AGREEMENT_STD_MAX_MM)
        frame_coverage = _clamp01(valid_frame_count / FRAME_COVERAGE_TARGET)
        quality = _clamp01(quality_ratio)

        components = [agreement, frame_coverage, quality]
        if angle_coverage is not None:
            components.append(_clamp01(angle_coverage))

        value = sum(components) / len(components)
        return cls(
            value=value,
            agreement=agreement,
            frame_coverage=frame_coverage,
            quality_ratio=quality,
            valid_frame_count=valid_frame_count,
            angle_coverage=angle_coverage,
        )
