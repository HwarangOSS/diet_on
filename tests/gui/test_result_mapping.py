# 테스트코드
from diskcleaner.core.deletion_pipeline import DeletionPlan
from diskcleaner.gui.result_mapping import report_to_delete_files, report_to_results
from tests.gui.factories import make_duplicate_group, make_file, make_report


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


def test_delete_target_count_uses_plan_when_given():
    safe = [make_file("/tmp/a.tmp", 100)]
    confirm = [make_file("/tmp/movie.mp4", 5000)]
    report = make_report(safe=safe, confirm=confirm)
    # LLM은 movie.mp4를 삭제 대상에서 제외(excluded)했다고 가정
    plan = DeletionPlan(auto_delete=safe, review_queue=[], excluded=confirm)

    result = report_to_results(report, plan)

    assert result["delete_target"] == {"count": 1, "size_bytes": 100}


def test_delete_target_count_excludes_review_queue():
    """ "삭제가 필요한 파일을 발견했어요" 카드는 auto_delete만 세야 함 -
    review_queue(AI가 판단 못해 사용자 확인이 필요한 것)까지 합치면 과대표시된다."""
    auto_delete = [make_file("/tmp/a.tmp", 100)]
    review_queue = [make_file("/tmp/ambiguous.docx", 5000)]
    report = make_report(safe=auto_delete, confirm=review_queue)
    plan = DeletionPlan(auto_delete=auto_delete, review_queue=review_queue, excluded=[])

    result = report_to_results(report, plan)

    assert result["delete_target"] == {"count": 1, "size_bytes": 100}


def test_delete_files_includes_llm_reason_from_plan():
    safe = [make_file("/tmp/a.tmp", 100)]
    plan = DeletionPlan(
        auto_delete=safe,
        review_queue=[],
        excluded=[],
        llm_results={"/tmp/a.tmp": {"reason": "오래된 임시 파일", "valid": True}},
    )
    report = make_report(safe=safe)

    files = report_to_delete_files(report, plan)

    assert files[0]["reason"] == "오래된 임시 파일"
