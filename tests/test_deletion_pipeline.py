"""
Unit tests for the deletion pipeline (issue #12).

Uses real SafetyChecker/FileClassifier against temp files, and a fake
get_recommendations() so no network call is made.
"""

from pathlib import Path

from diskcleaner.core.deletion_pipeline import build_deletion_plan, delete_plan
from diskcleaner.core.safety import FileStatus
from diskcleaner.core.scanner import DirectoryScanner
from diskcleaner.optimization.delete import DeletionManager


def _scan(tmp_path: Path):
    return [f for f in DirectoryScanner(str(tmp_path), cache_enabled=False).scan() if not f.is_dir]


class _FixedStatusSafety:
    """Fake SafetyChecker reporting a fixed FileStatus for every file, so
    locked/no_permission exclusion can be tested without simulating real
    OS-level locks or permission changes."""

    def __init__(self, status: FileStatus):
        self.status = status

    def verify_all(self, files):
        return [(f, self.status) for f in files]


def test_safe_type_goes_to_auto_delete(tmp_path):
    (tmp_path / "a.cache").write_text("x" * 10)

    plan = build_deletion_plan(_scan(tmp_path), get_recommendations=lambda files: {})

    assert [f.name for f in plan.auto_delete] == ["a.cache"]
    assert plan.review_queue == []
    assert plan.excluded == []


def test_protected_extension_is_excluded(tmp_path):
    (tmp_path / "app.exe").write_text("x" * 10)

    plan = build_deletion_plan(_scan(tmp_path), get_recommendations=lambda files: {})

    assert [f.name for f in plan.excluded] == ["app.exe"]
    assert plan.auto_delete == []
    assert plan.review_queue == []


def test_classifier_protected_risk_excludes_even_when_safety_says_safe(tmp_path):
    (tmp_path / "app.exe").write_text("x" * 10)

    plan = build_deletion_plan(
        _scan(tmp_path),
        safety=_FixedStatusSafety(FileStatus.SAFE),
        get_recommendations=lambda files: {},
    )

    assert [f.name for f in plan.excluded] == ["app.exe"]
    assert plan.auto_delete == []
    assert plan.review_queue == []


def test_locked_file_is_excluded(tmp_path):
    (tmp_path / "a.cache").write_text("x" * 10)

    plan = build_deletion_plan(
        _scan(tmp_path),
        safety=_FixedStatusSafety(FileStatus.LOCKED),
        get_recommendations=lambda files: {},
    )

    assert plan.auto_delete == []
    assert plan.review_queue == []
    assert [f.name for f in plan.excluded] == ["a.cache"]


def test_no_permission_file_is_excluded(tmp_path):
    (tmp_path / "a.cache").write_text("x" * 10)

    plan = build_deletion_plan(
        _scan(tmp_path),
        safety=_FixedStatusSafety(FileStatus.NO_PERMISSION),
        get_recommendations=lambda files: {},
    )

    assert plan.auto_delete == []
    assert plan.review_queue == []
    assert [f.name for f in plan.excluded] == ["a.cache"]


def test_confirm_needed_recommend_delete_true_moves_to_auto_delete(tmp_path):
    (tmp_path / "photo.jpg").write_text("x" * 10)

    def fake_recommendations(files):
        return {
            f.path: {"recommend_delete": True, "reason": "old", "confidence": 0.9, "valid": True}
            for f in files
        }

    plan = build_deletion_plan(_scan(tmp_path), get_recommendations=fake_recommendations)

    assert [f.name for f in plan.auto_delete] == ["photo.jpg"]
    assert plan.review_queue == []


def test_confirm_needed_recommend_delete_false_stays_in_review_queue(tmp_path):
    (tmp_path / "photo.jpg").write_text("x" * 10)

    def fake_recommendations(files):
        return {
            f.path: {
                "recommend_delete": False,
                "reason": "unsure",
                "confidence": 0.4,
                "valid": True,
            }
            for f in files
        }

    plan = build_deletion_plan(_scan(tmp_path), get_recommendations=fake_recommendations)

    assert plan.auto_delete == []
    assert [f.name for f in plan.review_queue] == ["photo.jpg"]


def test_confirm_needed_invalid_llm_result_stays_in_review_queue(tmp_path):
    (tmp_path / "photo.jpg").write_text("x" * 10)

    plan = build_deletion_plan(_scan(tmp_path), get_recommendations=lambda files: {})

    assert plan.auto_delete == []
    assert [f.name for f in plan.review_queue] == ["photo.jpg"]


def test_llm_call_failure_falls_back_to_review_queue_without_crashing(tmp_path):
    (tmp_path / "a.cache").write_text("x" * 10)  # safe, unaffected by the LLM call
    (tmp_path / "photo.jpg").write_text("y" * 10)  # confirm_needed

    def broken_recommendations(files):
        raise RuntimeError("ANTHROPIC_API_KEY not set")

    plan = build_deletion_plan(_scan(tmp_path), get_recommendations=broken_recommendations)

    assert [f.name for f in plan.auto_delete] == ["a.cache"]
    assert [f.name for f in plan.review_queue] == ["photo.jpg"]

    photo_path = next(f.path for f in plan.review_queue)
    assert plan.llm_results[photo_path]["valid"] is False


def test_delete_plan_only_deletes_confirmed_paths(tmp_path):
    (tmp_path / "a.cache").write_text("x" * 10)
    (tmp_path / ".DS_Store").write_text("y" * 10)

    plan = build_deletion_plan(_scan(tmp_path), get_recommendations=lambda files: {})
    assert len(plan.auto_delete) == 2

    kept = next(f for f in plan.auto_delete if f.name == "a.cache")
    deleted = next(f for f in plan.auto_delete if f.name == ".DS_Store")

    result = delete_plan(plan, DeletionManager(), confirmed_paths={deleted.path})

    assert result.total_deleted == 1
    assert Path(kept.path).exists()
    assert not Path(deleted.path).exists()
