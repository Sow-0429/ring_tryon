"""フレーム集約の信頼度 ConfidenceScore のテスト。

フレーム間一致度(周囲長の標準偏差)・有効フレーム数・品質割合・(任意)角度カバレッジ
から [0,1] の総合信頼度を算出することを検証する。
TDD red phase: app.domain.model.confidence は未実装の想定。
"""
from __future__ import annotations

import pytest

from app.domain.model.confidence import ConfidenceScore


class TestConfidenceScore:
    def test_high_agreement_many_frames_full_quality_is_high(self):
        score = ConfidenceScore.compute(
            circumference_std_mm=0.2,
            valid_frame_count=6,
            quality_ratio=1.0,
        )
        assert 0.0 <= score.value <= 1.0
        assert score.value > 0.85

    def test_high_variance_lowers_score(self):
        good = ConfidenceScore.compute(
            circumference_std_mm=0.2, valid_frame_count=6, quality_ratio=1.0,
        )
        noisy = ConfidenceScore.compute(
            circumference_std_mm=3.0, valid_frame_count=6, quality_ratio=1.0,
        )
        assert noisy.value < good.value

    def test_few_frames_lowers_score(self):
        many = ConfidenceScore.compute(
            circumference_std_mm=0.2, valid_frame_count=6, quality_ratio=1.0,
        )
        few = ConfidenceScore.compute(
            circumference_std_mm=0.2, valid_frame_count=1, quality_ratio=1.0,
        )
        assert few.value < many.value

    def test_low_quality_lowers_score(self):
        high_q = ConfidenceScore.compute(
            circumference_std_mm=0.2, valid_frame_count=6, quality_ratio=1.0,
        )
        low_q = ConfidenceScore.compute(
            circumference_std_mm=0.2, valid_frame_count=6, quality_ratio=0.3,
        )
        assert low_q.value < high_q.value

    def test_value_clamped(self):
        score = ConfidenceScore.compute(
            circumference_std_mm=100.0, valid_frame_count=0, quality_ratio=0.0,
        )
        assert 0.0 <= score.value <= 1.0

    def test_angle_coverage_optional_raises_when_low(self):
        """角度カバレッジを与えると、低カバレッジは信頼度を下げる。"""
        full = ConfidenceScore.compute(
            circumference_std_mm=0.2, valid_frame_count=6, quality_ratio=1.0,
            angle_coverage=1.0,
        )
        partial = ConfidenceScore.compute(
            circumference_std_mm=0.2, valid_frame_count=6, quality_ratio=1.0,
            angle_coverage=0.2,
        )
        assert partial.value < full.value

    def test_exposes_components(self):
        score = ConfidenceScore.compute(
            circumference_std_mm=0.2, valid_frame_count=6, quality_ratio=1.0,
        )
        assert 0.0 <= score.agreement <= 1.0
        assert 0.0 <= score.frame_coverage <= 1.0
        assert score.valid_frame_count == 6
