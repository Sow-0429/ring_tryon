from __future__ import annotations

import statistics

import cv2
import numpy as np

from app.domain.model.landmark import HandLandmarks
from app.domain.model.quality import QualityAssessment, QualityCheck

FINGER_NAMES = ("index", "middle", "ring", "pinky")

# 手の平坦さ: 全ランドマークの z(深さ)標準偏差の上限(正規化単位)。
FLATNESS_MAX_Z_STD = 0.08
# 指の直線性: PIP/DIP の MCP→TIP 軸からの逸脱を指長で正規化した上限。
STRAIGHTNESS_MAX_DEVIATION = 0.18
# ブレ: グレースケール Laplacian の分散の下限(小さいほどボケ)。
SHARPNESS_MIN_VARIANCE = 100.0
# 露出: グレースケール平均輝度の許容帯。
EXPOSURE_MIN_MEAN = 40.0
EXPOSURE_MAX_MEAN = 220.0


class QualityGate:
    """撮影品質を検査し、不合格は実用的な指示メッセージ付きで返す。

    号数は微小な計測差で変わるため、平坦さ・直線性・鮮鋭さ・露出が満たされない
    入力は計測前に弾く。検査結果は将来のフレーム選別(マルチフレーム集約)にも流用する。
    """

    def evaluate(
        self, image: np.ndarray, landmarks: HandLandmarks,
    ) -> QualityAssessment:
        return QualityAssessment(
            checks=(
                self._flatness(landmarks),
                self._straightness(landmarks),
                self._sharpness(image),
                self._exposure(image),
            )
        )

    def _flatness(self, landmarks: HandLandmarks) -> QualityCheck:
        z_std = statistics.pstdev([p.z for p in landmarks.points])
        passed = z_std <= FLATNESS_MAX_Z_STD
        return QualityCheck(
            name="flatness",
            passed=passed,
            value=z_std,
            threshold=FLATNESS_MAX_Z_STD,
            message="" if passed else "手のひらを平らに置いて、真上から撮影してください",
        )

    def _straightness(self, landmarks: HandLandmarks) -> QualityCheck:
        max_dev = 0.0
        for name in FINGER_NAMES:
            mcp = landmarks.finger_mcp(name)
            pip = landmarks.finger_pip(name)
            dip = landmarks.finger_dip(name)
            tip = landmarks.finger_tip(name)
            dev = self._axis_deviation(mcp, pip, dip, tip)
            max_dev = max(max_dev, dev)

        passed = max_dev <= STRAIGHTNESS_MAX_DEVIATION
        return QualityCheck(
            name="straightness",
            passed=passed,
            value=max_dev,
            threshold=STRAIGHTNESS_MAX_DEVIATION,
            message="" if passed else "指をまっすぐ伸ばして撮影してください",
        )

    @staticmethod
    def _axis_deviation(mcp, pip, dip, tip) -> float:
        """MCP→TIP 軸からの PIP/DIP の逸脱量を指長(MCP→TIP距離)で正規化。"""
        ax, ay = mcp.x, mcp.y
        bx, by = tip.x, tip.y
        length = ((bx - ax) ** 2 + (by - ay) ** 2) ** 0.5
        if length == 0:
            # MCP と TIP が重なる = 完全に折り曲げ。最大逸脱として扱う。
            return float("inf")

        def perp_dist(p) -> float:
            # 点 p から線分 (mcp→tip) を通る直線への垂直距離。
            cross = abs((bx - ax) * (ay - p.y) - (ax - p.x) * (by - ay))
            return cross / length

        return max(perp_dist(pip), perp_dist(dip)) / length

    def _sharpness(self, image: np.ndarray) -> QualityCheck:
        gray = cv2.cvtColor(image, cv2.COLOR_RGB2GRAY)
        variance = float(cv2.Laplacian(gray, cv2.CV_64F).var())
        passed = variance >= SHARPNESS_MIN_VARIANCE
        return QualityCheck(
            name="sharpness",
            passed=passed,
            value=variance,
            threshold=SHARPNESS_MIN_VARIANCE,
            message="" if passed else "画像がぶれています。手を固定して撮り直してください",
        )

    def _exposure(self, image: np.ndarray) -> QualityCheck:
        gray = cv2.cvtColor(image, cv2.COLOR_RGB2GRAY)
        mean = float(np.mean(gray))
        passed = EXPOSURE_MIN_MEAN <= mean <= EXPOSURE_MAX_MEAN
        if passed:
            message = ""
        elif mean < EXPOSURE_MIN_MEAN:
            message = "暗すぎます。明るい場所で撮影してください"
        else:
            message = "明るすぎます。光の反射を避けて撮影してください"
        return QualityCheck(
            name="exposure",
            passed=passed,
            value=mean,
            threshold=EXPOSURE_MIN_MEAN,
            message=message,
        )
