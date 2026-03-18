#!/usr/bin/env python3
"""
Scirate Discord Bot - ユニットテスト
外部API不要、pytest で実行可能
"""

import json
import time
import tempfile
from pathlib import Path
from datetime import datetime, timedelta
from unittest.mock import patch

import pytest

from scirate_discord_bot import (
    convert_latex_to_unicode,
    is_weekday,
    RateLimiter,
    SummaryCache,
    PostedPapersTracker,
)


# ===== convert_latex_to_unicode =====

class TestConvertLatexToUnicode:
    """LaTeX→Unicode変換のテスト"""

    def test_greek_letters(self):
        assert "α" in convert_latex_to_unicode(r"$\alpha$")
        assert "β" in convert_latex_to_unicode(r"$\beta$")
        assert "ψ" in convert_latex_to_unicode(r"$\psi$")
        assert "Ω" in convert_latex_to_unicode(r"$\Omega$")

    def test_superscript(self):
        result = convert_latex_to_unicode(r"$x^2$")
        assert "²" in result

    def test_subscript(self):
        result = convert_latex_to_unicode(r"$x_0$")
        assert "₀" in result

    def test_superscript_braces(self):
        result = convert_latex_to_unicode(r"$x^{10}$")
        assert "¹⁰" in result

    def test_subscript_braces(self):
        result = convert_latex_to_unicode(r"$x_{12}$")
        assert "₁₂" in result

    def test_frac(self):
        result = convert_latex_to_unicode(r"$\frac{a}{b}$")
        assert "a/b" in result

    def test_sqrt(self):
        result = convert_latex_to_unicode(r"$\sqrt{x}$")
        assert "√x" in result

    def test_mathcal(self):
        result = convert_latex_to_unicode(r"$\mathcal{O}$")
        assert "𝒪" in result

    def test_mathcal_multiple(self):
        result = convert_latex_to_unicode(r"$\mathcal{H}$")
        assert "ℋ" in result

    def test_mathbb(self):
        result = convert_latex_to_unicode(r"$\mathbb{R}$")
        assert "ℝ" in result

    def test_mathbb_complex(self):
        result = convert_latex_to_unicode(r"$\mathbb{C}$")
        assert "ℂ" in result

    def test_widetilde(self):
        result = convert_latex_to_unicode(r"$\widetilde{O}$")
        assert "O\u0303" in result  # O + combining tilde

    def test_tilde(self):
        result = convert_latex_to_unicode(r"$\tilde{x}$")
        assert "x\u0303" in result

    def test_hat(self):
        result = convert_latex_to_unicode(r"$\hat{H}$")
        assert "H\u0302" in result

    def test_bar(self):
        result = convert_latex_to_unicode(r"$\bar{x}$")
        assert "x\u0304" in result

    def test_overline(self):
        result = convert_latex_to_unicode(r"$\overline{x}$")
        assert "x\u0304" in result

    def test_vec(self):
        result = convert_latex_to_unicode(r"$\vec{v}$")
        assert "v\u20D7" in result

    def test_dot(self):
        result = convert_latex_to_unicode(r"$\dot{x}$")
        assert "x\u0307" in result

    def test_mathbf_stripped(self):
        result = convert_latex_to_unicode(r"$\mathbf{A}$")
        assert "A" in result

    def test_math_symbols(self):
        assert "∞" in convert_latex_to_unicode(r"$\infty$")
        assert "→" in convert_latex_to_unicode(r"$\rightarrow$")
        assert "⟨" in convert_latex_to_unicode(r"$\langle$")
        assert "⟩" in convert_latex_to_unicode(r"$\rangle$")

    def test_text_command(self):
        result = convert_latex_to_unicode(r"$\text{hello}$")
        assert "hello" in result

    def test_mathrm_command(self):
        result = convert_latex_to_unicode(r"$\mathrm{kg}$")
        assert "kg" in result

    def test_no_latex(self):
        text = "This is plain text without LaTeX"
        assert convert_latex_to_unicode(text) == text

    def test_inline_paren_format(self):
        result = convert_latex_to_unicode(r"energy \(\alpha\) value")
        assert "α" in result

    def test_display_bracket_format(self):
        result = convert_latex_to_unicode(r"equation \[\beta\] here")
        assert "β" in result

    def test_combined_mathcal_widetilde(self):
        r"""実際のケース: \widetilde{\mathcal{O}}"""
        result = convert_latex_to_unicode(r"$\widetilde{\mathcal{O}}$")
        assert "𝒪" in result


# ===== is_weekday =====

class TestIsWeekday:
    """平日チェックのテスト"""

    @patch("scirate_discord_bot.datetime")
    def test_monday_is_weekday(self, mock_dt):
        mock_dt.now.return_value = datetime(2026, 3, 16)  # Monday
        mock_dt.side_effect = lambda *a, **kw: datetime(*a, **kw)
        assert is_weekday() is True

    @patch("scirate_discord_bot.datetime")
    def test_friday_is_weekday(self, mock_dt):
        mock_dt.now.return_value = datetime(2026, 3, 20)  # Friday
        mock_dt.side_effect = lambda *a, **kw: datetime(*a, **kw)
        assert is_weekday() is True

    @patch("scirate_discord_bot.datetime")
    def test_saturday_is_not_weekday(self, mock_dt):
        mock_dt.now.return_value = datetime(2026, 3, 21)  # Saturday
        mock_dt.side_effect = lambda *a, **kw: datetime(*a, **kw)
        assert is_weekday() is False

    @patch("scirate_discord_bot.datetime")
    def test_sunday_is_not_weekday(self, mock_dt):
        mock_dt.now.return_value = datetime(2026, 3, 22)  # Sunday
        mock_dt.side_effect = lambda *a, **kw: datetime(*a, **kw)
        assert is_weekday() is False


# ===== RateLimiter =====

class TestRateLimiter:
    """レート制限のテスト"""

    def test_initial_state(self):
        rl = RateLimiter(rpm_limit=10)
        assert rl.rpm_limit == 10
        assert rl.request_count == 0

    def test_interval_calculation(self):
        rl = RateLimiter(rpm_limit=10)
        assert rl.interval == 6.0  # 60 / 10

    def test_request_count_increments(self):
        rl = RateLimiter(rpm_limit=100)
        rl.wait_if_needed()
        assert rl.request_count == 1
        rl.wait_if_needed()
        assert rl.request_count == 2

    def test_update_rpm(self):
        rl = RateLimiter(rpm_limit=10)
        rl.update_rpm(20)
        assert rl.rpm_limit == 20
        assert rl.interval == 3.0  # 60 / 20


# ===== SummaryCache =====

class TestSummaryCache:
    """キャッシュのテスト"""

    def test_set_and_get(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            cache = SummaryCache(cache_dir=Path(tmpdir))
            cache.set("2603.12345", "some abstract", "これは要約です")
            result = cache.get("2603.12345", "some abstract")
            assert result == "これは要約です"

    def test_cache_miss(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            cache = SummaryCache(cache_dir=Path(tmpdir))
            result = cache.get("9999.99999", "nonexistent")
            assert result is None

    def test_cache_persistence(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            cache1 = SummaryCache(cache_dir=Path(tmpdir))
            cache1.set("2603.12345", "abstract", "要約テスト")

            # 新しいインスタンスで読み込み
            cache2 = SummaryCache(cache_dir=Path(tmpdir))
            result = cache2.get("2603.12345", "abstract")
            assert result == "要約テスト"

    def test_cache_stats(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            cache = SummaryCache(cache_dir=Path(tmpdir))
            cache.set("2603.00001", "a1", "s1")
            cache.set("2603.00002", "a2", "s2")
            stats = cache.get_stats()
            assert stats["total_entries"] == 2


# ===== PostedPapersTracker =====

class TestPostedPapersTracker:
    """投稿済みトラッカーのテスト"""

    def _make_tracker(self, tmpdir):
        tracker = PostedPapersTracker()
        tracker.posted_file = Path(tmpdir) / "posted_papers.json"
        tracker.posted = {"papers": {}, "last_date": None}
        return tracker

    def test_not_posted(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            tracker = self._make_tracker(tmpdir)
            assert tracker.is_posted("2603.12345") is False

    def test_mark_and_check(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            tracker = self._make_tracker(tmpdir)
            tracker.mark_as_posted("2603.12345")
            assert tracker.is_posted("2603.12345") is True

    def test_old_post_not_counted(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            tracker = self._make_tracker(tmpdir)
            # 31日前に投稿
            old_date = (datetime.now() - timedelta(days=31)).isoformat()
            tracker.posted["papers"]["2603.12345"] = old_date
            assert tracker.is_posted("2603.12345") is False

    def test_filter_new_papers(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            tracker = self._make_tracker(tmpdir)
            tracker.mark_as_posted("2603.00001")

            papers = [
                {"arxiv_id": "2603.00001", "title": "Old"},
                {"arxiv_id": "2603.00002", "title": "New"},
            ]
            result = tracker.filter_new_papers(papers)
            assert len(result) == 1
            assert result[0]["arxiv_id"] == "2603.00002"

    def test_cleanup_old_entries(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            tracker = self._make_tracker(tmpdir)
            old_date = (datetime.now() - timedelta(days=61)).isoformat()
            tracker.posted["papers"]["2603.00001"] = old_date
            tracker.mark_as_posted("2603.00002")

            tracker.cleanup_old_entries(days=60)
            assert "2603.00001" not in tracker.posted["papers"]
            assert "2603.00002" in tracker.posted["papers"]
