from __future__ import annotations

from diskcleaner.core.deletion_pipeline import DeletionPlan
from diskcleaner.core.smart_cleanup import CleanupReport

# LLM을 안 거치는 safe 파일(캐시/로그/임시)은 plan.llm_results에 없으니 이 카테고리로 묶는다.
# "안전"이라고 하면 "삭제 안 해도 되는 파일"로 오해하기 쉬워서, AI 확인 없이도 확실히
# 지워도 되는 파일이라는 의미로 이름을 바꿈.
SAFE_CATEGORY_LABEL = "즉시 삭제 가능"

# review_queue 파일(AI가 삭제를 승인하지 않아 사람이 직접 판단해야 하는 파일)은
# SAFE_CATEGORY_LABEL과 절대 섞이면 안 됨 - 기본 선택/일괄 삭제 대상에서 빠져야 함.
REVIEW_CATEGORY_LABEL = "검토 필요"

# FileClassifier의 타입 카테고리가 중국어로 돼있어서(diskcleaner/core/classifier.py
# type_categories) 그대로 해시태그에 노출하면 안 됨 - 우선 자주 나오는 것만
# 한국어로 옮겨두고, 매핑에 없는 카테고리는 "기타 파일"로 뭉뚱그림.
# TODO: classifier.py 자체를 한국어 카테고리로 바꾸는 게 근본적인 해결책.
_TYPE_TAG_KO = {
    "临时/构建产物": "사용이 오래된 파일",
    "日志文件": "로그 파일",
    "缓存文件": "캐시 파일",
    "备份文件": "백업 파일",
    "下载文件": "다운로드 파일",
    "媒体文件": "미디어 파일",
    "文档文件": "문서 파일",
    "压缩文件": "압축 파일",
    "其他文件": "기타 파일",
}


def _build_type_lookup(report: CleanupReport) -> dict:
    """파일 경로 -> 한국어 태그 한 번에 만들어두기 (report.by_type 재사용, 재분류 안 함)."""
    lookup = {}
    for type_name, files in report.by_type.items():
        tag = _TYPE_TAG_KO.get(type_name, "기타 파일")
        for f in files:
            lookup[f.path] = tag
    return lookup


def report_to_delete_files(report: CleanupReport, plan: DeletionPlan | None = None) -> list:
    """삭제 상세 페이지(FileListItem 리스트)가 바로 쓸 수 있는 형식으로 변환.

    plan이 주어지면 AI가 삭제 대상에서 제외한(excluded) 파일은 빠지고, LLM이 남긴
    삭제 사유/카테고리가 있으면 "reason"/"category"에 채워짐 (category는 상세 화면에서
    같은 카테고리끼리 묶어서 일괄 선택하는 데 씀). plan이 없으면(AI 판단 전) 기존처럼
    safe+confirm_needed를 그대로 보여줌.

    반환: [{"path", "name", "size_bytes", "hashtags": [str], "reason": str | None,
            "category": str}, ...]
    """
    type_lookup = _build_type_lookup(report)

    if plan is not None:
        llm_lookup = {
            path: result for path, result in plan.llm_results.items() if isinstance(result, dict)
        }
        # review_queue는 AI가 삭제를 승인하지 않은 파일이라 category를 llm 결과에
        # 맡기지 않고 항상 REVIEW_CATEGORY_LABEL로 고정 (SAFE_CATEGORY_LABEL과 섞여
        # 기본 선택/일괄 삭제되는 걸 막기 위함).
        categorized = [
            (f, llm_lookup.get(f.path, {}).get("category", SAFE_CATEGORY_LABEL))
            for f in plan.auto_delete
        ] + [(f, REVIEW_CATEGORY_LABEL) for f in plan.review_queue]
    else:
        llm_lookup = {}
        files = report.by_risk.get("safe", []) + report.by_risk.get("confirm_needed", [])
        categorized = [(f, SAFE_CATEGORY_LABEL) for f in files]

    return [
        {
            "path": f.path,
            "name": f.name,
            "size_bytes": f.size,
            "hashtags": [type_lookup[f.path]] if f.path in type_lookup else [],
            "reason": llm_lookup.get(f.path, {}).get("reason"),
            "category": category,
        }
        for f, category in categorized
    ]


def report_to_duplicate_groups(report: CleanupReport) -> list:
    """중복 상세 페이지(DuplicateGroupBox 리스트)가 바로 쓸 수 있는 형식으로 변환.

    각 그룹은 mtime이 가장 오래된 파일을 "원본으로 추정"해서 맨 앞에 둠
    (DuplicateGroupBox.set_group()이 files[0]을 원본 취급하고 기본 비선택 처리함).

    반환: [{"name": str, "files": [{"path", "name", "size_bytes"}, ...]}, ...]
    """
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


def report_to_results(report: CleanupReport, plan: DeletionPlan | None = None) -> dict:
    """ "삭제가 필요한 파일을 발견했어요" 카드 숫자.

    plan이 있으면 AI가 실제로 삭제를 추천한 auto_delete만 센다 (review_queue는
    AI가 판단을 못해 사용자 확인이 필요한 별개 상태라 여기 합산하면 "전부 삭제
    필요"로 과대표시됨). auto_delete에는 규칙 기반으로 확실히 안전한 safe 파일과
    AI가 검토해서 승인한 confirm_needed 파일이 같이 들어있는데, 상세화면에서
    "즉시 삭제 가능"/AI 카테고리로 나눠 보여주므로 요약 카드는 합산해도 된다.
    """
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
