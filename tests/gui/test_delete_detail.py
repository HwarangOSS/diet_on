# 테스트코드
from diskcleaner.gui.pages.delete_detail import DeletePage
from diskcleaner.gui.result_mapping import REVIEW_CATEGORY_LABEL, SAFE_CATEGORY_LABEL


def test_review_category_files_default_unselected(qtbot):
    """검토 필요 파일은 사용자가 직접 체크하기 전까지 삭제 대상이면 안 됨 -
    기본 체크된 채로 뜨면 '전체 삭제' 한 번으로 AI 미검토 파일까지 지워짐."""
    page = DeletePage()
    qtbot.addWidget(page)

    page.set_files(
        [
            {
                "path": "/tmp/a.tmp",
                "name": "a.tmp",
                "size_bytes": 100,
                "category": SAFE_CATEGORY_LABEL,
            },
            {
                "path": "/tmp/ambiguous.docx",
                "name": "ambiguous.docx",
                "size_bytes": 5000,
                "category": REVIEW_CATEGORY_LABEL,
            },
        ]
    )

    selected_by_path = {f["path"]: item.is_selected() for f, item in zip(page._files, page._items)}
    assert selected_by_path["/tmp/a.tmp"] is True
    assert selected_by_path["/tmp/ambiguous.docx"] is False
