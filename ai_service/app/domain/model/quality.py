from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class QualityCheck:
    """個々の撮影品質検査の結果。

    name: 検査の識別子 (flatness / straightness / sharpness / exposure)。
    value/threshold: 計測値としきい値(検査ごとに意味が異なる)。
    message: 不合格時にユーザーへ提示する実用的な指示。合格時は空文字。
    """

    name: str
    passed: bool
    value: float
    threshold: float
    message: str = ""


@dataclass(frozen=True)
class QualityAssessment:
    """複数の品質検査をまとめた総合判定(値オブジェクト)。"""

    checks: tuple[QualityCheck, ...]

    @property
    def is_acceptable(self) -> bool:
        return all(c.passed for c in self.checks)

    @property
    def failure_messages(self) -> list[str]:
        return [c.message for c in self.checks if not c.passed and c.message]
