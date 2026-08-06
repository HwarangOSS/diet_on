from diskcleaner.core.smart_cleanup import CleanupReport

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


def report_to_delete_files(report: CleanupReport) -> list:
    """삭제 상세 페이지(FileListItem 리스트)가 바로 쓸 수 있는 형식으로 변환.

    반환: [{"path": str, "name": str, "size_bytes": int, "hashtags": [str]}, ...]
    """
    type_lookup = _build_type_lookup(report)
    safe_files = report.by_risk.get("safe", [])
    confirm_files = report.by_risk.get("confirm_needed", [])

    return [
        {
            "path": f.path,
            "name": f.name,
            "size_bytes": f.size,
            "hashtags": [type_lookup[f.path]] if f.path in type_lookup else [],
        }
        for f in safe_files + confirm_files
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
                    {"path": f.path, "name": f.name, "size_bytes": f.size}
                    for f in files_sorted
                ],
            }
        )
    return groups


def report_to_results(report: CleanupReport) -> dict:
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
