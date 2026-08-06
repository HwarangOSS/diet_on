# 테스트코드
from diskcleaner.core.duplicate_finder import DuplicateGroup
from diskcleaner.core.scanner import FileInfo
from diskcleaner.core.smart_cleanup import CleanupReport


def make_file(path: str, size: int, mtime: float = 0.0) -> FileInfo:
    name = path.rsplit("/", 1)[-1]
    return FileInfo(path=path, name=name, size=size, mtime=mtime, is_dir=False, is_link=False)


def make_duplicate_group(files, size: int) -> DuplicateGroup:
    return DuplicateGroup(files=files, size=size)


def make_report(safe=None, confirm=None, duplicates=None) -> CleanupReport:
    safe = safe or []
    confirm = confirm or []
    duplicates = duplicates or []

    return CleanupReport(
        by_type={},
        by_risk={"safe": safe, "confirm_needed": confirm, "protected": []},
        by_age={},
        duplicates=duplicates,
        total_files=len(safe) + len(confirm),
        total_size=sum(f.size for f in safe + confirm),
        reclaimable_space=0,
        scan_time=0.1,
        timestamp=0.0,
    )
