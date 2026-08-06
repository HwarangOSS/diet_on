from diskcleaner.core.smart_cleanup import CleanupReport


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
