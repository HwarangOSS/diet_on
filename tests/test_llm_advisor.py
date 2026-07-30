"""
Unit tests for the LLM advisor's fail-closed response validation.

No network calls — these test validate_batch_response() directly against
docs/LLM_SCHEMA.md's fail-closed rules.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from diskcleaner.core.llm_advisor import validate_batch_response


def _request():
    return {
        "batch_id": "b1",
        "files": [
            {"file_id": "b1:f_0", "name": "a.tmp", "size": 10, "mtime": 100.0},
            {"file_id": "b1:f_1", "name": "b.tmp", "size": 20, "mtime": 100.0},
        ],
    }


def test_valid_response_passes_through():
    response = {
        "batch_id": "b1",
        "results": [
            {
                "file_id": "b1:f_0",
                "recommend_delete": True,
                "reason": "temp file",
                "confidence": 0.9,
            },
            {
                "file_id": "b1:f_1",
                "recommend_delete": False,
                "reason": "unknown",
                "confidence": 0.3,
            },
        ],
    }
    result = validate_batch_response(_request(), response)
    assert result["b1:f_0"]["valid"] is True
    assert result["b1:f_0"]["recommend_delete"] is True
    assert result["b1:f_1"]["recommend_delete"] is False


def test_non_dict_response_invalidates_whole_batch():
    result = validate_batch_response(_request(), None)
    assert all(r["valid"] is False for r in result.values())
    assert all(r["recommend_delete"] is False for r in result.values())


def test_batch_id_mismatch_invalidates_whole_batch():
    response = {"batch_id": "wrong", "results": []}
    result = validate_batch_response(_request(), response)
    assert all("batch_id 불일치" in r["reason"] for r in result.values())


def test_missing_file_id_falls_back_to_needs_review():
    response = {
        "batch_id": "b1",
        "results": [
            {"file_id": "b1:f_0", "recommend_delete": True, "reason": "temp file"},
        ],
    }
    result = validate_batch_response(_request(), response)
    assert result["b1:f_0"]["valid"] is True
    assert result["b1:f_1"]["valid"] is False
    assert result["b1:f_1"]["recommend_delete"] is False
    assert "응답 누락" in result["b1:f_1"]["reason"]


def test_duplicate_file_id_flagged():
    response = {
        "batch_id": "b1",
        "results": [
            {"file_id": "b1:f_0", "recommend_delete": True, "reason": "x"},
            {"file_id": "b1:f_0", "recommend_delete": False, "reason": "y"},
        ],
    }
    result = validate_batch_response(_request(), response)
    assert result["b1:f_0"]["recommend_delete"] is False
    assert "중복 응답" in result["b1:f_0"]["reason"]


def test_bad_recommend_delete_type_rejected():
    response = {
        "batch_id": "b1",
        "results": [
            {"file_id": "b1:f_0", "recommend_delete": "yes", "reason": "x"},
        ],
    }
    result = validate_batch_response(_request(), response)
    assert result["b1:f_0"]["valid"] is False
    assert result["b1:f_0"]["recommend_delete"] is False
    assert "recommend_delete 형식" in result["b1:f_0"]["reason"]


def test_bool_confidence_rejected():
    response = {
        "batch_id": "b1",
        "results": [
            {"file_id": "b1:f_0", "recommend_delete": True, "reason": "x", "confidence": True},
        ],
    }
    result = validate_batch_response(_request(), response)
    assert result["b1:f_0"]["valid"] is False
    assert "confidence 값" in result["b1:f_0"]["reason"]


def test_out_of_range_confidence_rejected():
    for bad_confidence in (-0.1, 1.1):
        response = {
            "batch_id": "b1",
            "results": [
                {
                    "file_id": "b1:f_0",
                    "recommend_delete": True,
                    "reason": "x",
                    "confidence": bad_confidence,
                },
            ],
        }
        result = validate_batch_response(_request(), response)
        assert result["b1:f_0"]["valid"] is False
        assert "confidence 값" in result["b1:f_0"]["reason"]


def test_unknown_file_id_in_response_is_ignored():
    response = {
        "batch_id": "b1",
        "results": [
            {"file_id": "b1:f_0", "recommend_delete": True, "reason": "x"},
            {"file_id": "b1:f_99", "recommend_delete": True, "reason": "ghost"},
        ],
    }
    result = validate_batch_response(_request(), response)
    assert set(result.keys()) == {"b1:f_0", "b1:f_1"}
    assert result["b1:f_1"]["recommend_delete"] is False
