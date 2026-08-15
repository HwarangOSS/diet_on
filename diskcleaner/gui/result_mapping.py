from __future__ import annotations

from diskcleaner.core.deletion_pipeline import DeletionPlan
from diskcleaner.core.duplicate_finder import DuplicateGroup
from diskcleaner.core.smart_cleanup import CleanupReport

SAFE_CATEGORY_LABEL = "즉시 삭제 가능"

REVIEW_CATEGORY_LABEL = "검토 필요"


def report_to_delete_files(report: CleanupReport, plan: DeletionPlan | None = None) -> list:
    if plan is None:
        return []

    llm_lookup = {
        path: result for path, result in plan.llm_results.items() if isinstance(result, dict)
    }

    def _to_file_dict(f, category: str) -> dict:
        return {
            "path": f.path,
            "name": f.name,
            "size_bytes": f.size,
            "reason": llm_lookup.get(f.path, {}).get("reason"),
            "category": category,
        }

    # review_queue(AI가 삭제를 권하지 않은 파일)는 상세 삭제 목록에 노출하지 않는다 -
    # 정말 삭제 대상인 auto_delete만 사용자에게 보여준다.
    return [_to_file_dict(f, SAFE_CATEGORY_LABEL) for f in plan.auto_delete]


def report_to_duplicate_groups(report: CleanupReport) -> list:
    groups = []
    for dup_group in report.duplicates:
        files_sorted = sorted(dup_group.files, key=lambda f: f.mtime)
        if not files_sorted:
            continue
        groups.append(
            {
                "name": files_sorted[0].name,
                "files": [
                    {"path": f.path, "name": f.name, "size_bytes": f.size} for f in files_sorted
                ],
            }
        )
    return groups


def remove_deleted_paths(
    report: CleanupReport, plan: DeletionPlan | None, deleted_paths: set[str]
) -> None:
    if not deleted_paths:
        return

    for bucket in (report.by_risk, report.by_type, report.by_age):
        for key, files in bucket.items():
            bucket[key] = [f for f in files if f.path not in deleted_paths]

    new_groups = []
    for group in report.duplicates:
        remaining = [f for f in group.files if f.path not in deleted_paths]
        if len(remaining) > 1:
            new_groups.append(
                DuplicateGroup(files=remaining, size=group.size, hash_value=group.hash_value)
            )
    report.duplicates = new_groups

    if plan is not None:
        plan.auto_delete = [f for f in plan.auto_delete if f.path not in deleted_paths]
        plan.review_queue = [f for f in plan.review_queue if f.path not in deleted_paths]


def report_to_results(report: CleanupReport, plan: DeletionPlan | None = None) -> dict:
    if plan is not None:
        delete_target_files = plan.auto_delete
    else:
        safe_files = report.by_risk.get("safe", [])
        confirm_files = report.by_risk.get("confirm_needed", [])
        delete_target_files = safe_files + confirm_files

    duplicate_count = sum(group.count for group in report.duplicates)

    return {
        "delete_target": {
            "count": len(delete_target_files),
            "size_bytes": sum(f.size for f in delete_target_files),
        },
        "duplicate": {
            "count": duplicate_count,
            "size_bytes": report.duplicate_reclaimable,
        },
    }
