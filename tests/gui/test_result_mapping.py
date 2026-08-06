# 테스트코드
from diskcleaner.gui.result_mapping import report_to_results

from .factories import make_duplicate_group, make_file, make_report


def test_empty_report_maps_to_zeroed_results():
    report = make_report()

    result = report_to_results(report)

    assert result == {
        "delete_target": {"count": 0, "size_bytes": 0},
        "duplicate": {"count": 0, "size_bytes": 0},
    }


def test_delete_target_combines_safe_and_confirm_needed():
    safe = [make_file("/tmp/a.tmp", 100), make_file("/tmp/b.log", 200)]
    confirm = [make_file("/tmp/movie.mp4", 5000)]
    report = make_report(safe=safe, confirm=confirm)

    result = report_to_results(report)

    assert result["delete_target"] == {"count": 3, "size_bytes": 5300}
    assert result["duplicate"] == {"count": 0, "size_bytes": 0}


def test_duplicate_count_is_all_files_but_size_excludes_one_kept_copy():
    dup_files = [
        make_file("/tmp/x1.jpg", 1000),
        make_file("/tmp/x2.jpg", 1000),
        make_file("/tmp/x3.jpg", 1000),
    ]
    group = make_duplicate_group(dup_files, size=1000)
    report = make_report(duplicates=[group])

    result = report_to_results(report)

    assert result["duplicate"]["count"] == 3
    assert result["duplicate"]["size_bytes"] == 2000
