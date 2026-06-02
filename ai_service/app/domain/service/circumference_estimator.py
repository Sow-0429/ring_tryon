from __future__ import annotations

import math
from typing import Protocol

from app.domain.model.measurement import CircumferenceEstimate, FingerMeasurement

# 標準ティアの固定 深さ/幅比(指種別)。較正データが貯まれば回帰モデルへ置換する。
DEPTH_TO_WIDTH_RATIOS: dict[str, float] = {
    "index": 0.80,
    "middle": 0.82,
    "ring": 0.85,
    "pinky": 0.75,
}

DEFAULT_DEPTH_TO_WIDTH_RATIO = 0.80


def ellipse_circumference(width_mm: float, depth_mm: float) -> float:
    """幅(長軸)と厚み(短軸)から楕円周長(Ramanujan近似)を返す。"""
    a = width_mm / 2
    b = depth_mm / 2
    return math.pi * (3 * (a + b) - math.sqrt((3 * a + b) * (a + 3 * b)))


TIER_STANDARD = "standard"
TIER_PREMIUM = "premium"


class DepthDataRequiredError(Exception):
    """プレミアム(深度)ティアなのに深度データが無い。"""


class CircumferenceEstimator(Protocol):
    """周囲長推定の戦略インターフェース。"""

    def estimate(self, measurement: FingerMeasurement) -> CircumferenceEstimate: ...


def estimator_for_tier(tier: str) -> CircumferenceEstimator:
    """ティアに応じた推定戦略を返す。課金判定(誰がpremiumか)は Go アプリ層。

    standard: 全機種対応の固定比楕円近似。premium: 深度実測の楕円近似。
    """
    if tier == TIER_PREMIUM:
        return DepthBasedCircumferenceEstimator()
    return EllipseFitCircumferenceEstimator()


class EllipseFitCircumferenceEstimator:
    """標準ティア: 真上2D計測の幅に固定 深さ/幅比を掛けて楕円近似する。

    厚みを直接測れないための近似。系統バイアスは較正ループ(回帰)で吸収する。
    """

    def estimate(self, measurement: FingerMeasurement) -> CircumferenceEstimate:
        ratio = DEPTH_TO_WIDTH_RATIOS.get(
            measurement.finger_name, DEFAULT_DEPTH_TO_WIDTH_RATIO,
        )
        circumference = ellipse_circumference(
            measurement.width_mm, measurement.width_mm * ratio,
        )
        return CircumferenceEstimate(circumference_mm=circumference)


class DepthBasedCircumferenceEstimator:
    """プレミアムティア: 深度センサで実測した厚みを使い固定比を排した楕円近似。

    depth_mm が無い計測には適用できない(課金判定とティア選択は Go アプリ層)。
    """

    def estimate(self, measurement: FingerMeasurement) -> CircumferenceEstimate:
        if measurement.depth_mm is None or measurement.depth_mm <= 0:
            raise DepthDataRequiredError(
                "premium (depth) tier requires measured depth_mm"
            )
        circumference = ellipse_circumference(
            measurement.width_mm, measurement.depth_mm,
        )
        return CircumferenceEstimate(circumference_mm=circumference)
