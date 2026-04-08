from __future__ import annotations

from dataclasses import dataclass
from typing import Union


@dataclass(frozen=True)
class FingerCalibrationInput:
    middle_finger_length_mm: float


@dataclass(frozen=True)
class CoinCalibrationInput:
    """100円玉を基準物として使用するキャリブレーション入力。"""
    pass


CalibrationInput = Union[FingerCalibrationInput, CoinCalibrationInput]
