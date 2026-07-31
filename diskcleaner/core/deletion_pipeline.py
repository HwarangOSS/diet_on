"""
Deletion pipeline: safety + risk classification -> LLM advisory -> DeletionManager.

Combines SafetyChecker.verify_all() (lock/permission/protected checks) with
FileClassifier's risk level (safe/confirm_needed/protected by file type) into
a single deletion plan. confirm_needed files are narrowed down further by
Claude's recommend_delete via llm_advisor, validated fail-closed.

No file is ever deleted here without the caller passing an explicit confirmed
path set to delete_plan() — user confirmation always happens upstream.
"""

from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable, Dict, List, Optional, Set

from diskcleaner.core import llm_advisor
from diskcleaner.core.classifier import FileClassifier, RiskLevel
from diskcleaner.core.safety import FileStatus, SafetyChecker
from diskcleaner.core.scanner import FileInfo
from diskcleaner.optimization.delete import DeleteResult, DeletionManager


@dataclass
class DeletionPlan:
    """Categorized deletion candidates produced by build_deletion_plan()."""

    auto_delete: List[FileInfo] = field(default_factory=list)
    review_queue: List[FileInfo] = field(default_factory=list)
    excluded: List[FileInfo] = field(default_factory=list)
    llm_results: Dict[str, Dict[str, object]] = field(default_factory=dict)


def build_deletion_plan(
    files: List[FileInfo],
    safety: Optional[SafetyChecker] = None,
    classifier: Optional[FileClassifier] = None,
    get_recommendations: Callable[[List[FileInfo]], Dict[str, Dict[str, object]]] = (
        llm_advisor.get_recommendations
    ),
) -> DeletionPlan:
    """
    Classify files into auto_delete / review_queue / excluded.

    - excluded: SafetyChecker says locked/no_permission/protected/error, or
      FileClassifier's type-based risk says protected.
    - auto_delete: SafetyChecker SAFE and FileClassifier risk "safe", plus any
      confirm_needed file the LLM validly recommends deleting.
    - review_queue: SafetyChecker SAFE and FileClassifier risk "confirm_needed"
      that the LLM did not validly recommend for deletion (kept for the user
      to decide manually — never auto-deleted).
    """
    safety = safety or SafetyChecker()
    classifier = classifier or FileClassifier()

    plain_files = [f for f in files if not f.is_dir]
    risk_by_path = {
        f.path: risk
        for risk, group in classifier.classify(plain_files)["by_risk"].items()
        for f in group
    }

    safe_files: List[FileInfo] = []
    confirm_files: List[FileInfo] = []
    excluded: List[FileInfo] = []

    for file, status in safety.verify_all(plain_files):
        risk = risk_by_path.get(file.path)
        if status is not FileStatus.SAFE or risk == RiskLevel.PROTECTED.value:
            excluded.append(file)
        elif risk == RiskLevel.CONFIRM_NEEDED.value:
            confirm_files.append(file)
        else:
            safe_files.append(file)

    try:
        llm_results = get_recommendations(confirm_files)
    except Exception as exc:
        # LLM call itself failed (missing API key, anthropic not installed,
        # network error, ...) - fail closed like validate_batch_response does
        # rather than losing the already-computed safe/excluded buckets.
        llm_results = {
            f.path: llm_advisor.fallback(f"LLM 호출 실패 - 확인 필요 ({exc})") for f in confirm_files
        }

    auto_delete = list(safe_files)
    review_queue = []
    for file in confirm_files:
        result = llm_results.get(file.path)
        if result and result["valid"] and result["recommend_delete"]:
            auto_delete.append(file)
        else:
            review_queue.append(file)

    return DeletionPlan(
        auto_delete=auto_delete,
        review_queue=review_queue,
        excluded=excluded,
        llm_results=llm_results,
    )


def delete_plan(
    plan: DeletionPlan,
    deletion_manager: DeletionManager,
    confirmed_paths: Set[str],
) -> DeleteResult:
    """
    Hand the user-confirmed subset of a DeletionPlan to DeletionManager.delete().

    async_mode is deliberately not exposed here: DeletionManager's async path
    (AsyncDeleter) doesn't actually report which files succeeded or failed, so
    wiring it through would silently return a DeleteResult that always claims
    zero deletions while files disappear in the background.

    Args:
        plan: Plan produced by build_deletion_plan().
        deletion_manager: DeletionManager to execute the actual deletion.
        confirmed_paths: Paths the user explicitly confirmed for deletion,
            restricted to plan.auto_delete + plan.review_queue.

    Returns:
        DeleteResult from DeletionManager.delete().
    """
    candidates = [
        Path(f.path) for f in plan.auto_delete + plan.review_queue if f.path in confirmed_paths
    ]
    return deletion_manager.delete(candidates)
