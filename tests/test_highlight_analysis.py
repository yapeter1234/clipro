import pytest

from services.worker.app.highlight_analysis import HighlightAnalysisError, parse_highlights


def test_parse_highlights_converts_timestamps():
    result = parse_highlights(
        '{"highlights":[{"start_seconds":10.25,"end_seconds":28.5,"title":"Big moment","score":9.2}]}',
        duration_ms=60000,
    )
    assert result[0]["start_ms"] == 10250
    assert result[0]["end_ms"] == 28500
    assert result[0]["score"] == 9.2


def test_parse_highlights_clamps_to_source_duration():
    result = parse_highlights(
        '{"highlights":[{"start_seconds":55,"end_seconds":80,"title":"Valid"}]}',
        duration_ms=60000,
    )
    assert result[0]["end_ms"] == 60000


def test_parse_highlights_removes_overlapping_lower_scored_suggestions():
    result = parse_highlights(
        '{"highlights":['
        '{"start_seconds":10,"end_seconds":30,"title":"A","score":8},'
        '{"start_seconds":15,"end_seconds":35,"title":"B","score":9},'
        '{"start_seconds":40,"end_seconds":55,"title":"C","score":7}]}',
        duration_ms=60000,
    )
    assert [item["title"] for item in result] == ["B", "C"]


def test_parse_highlights_rejects_non_json_response():
    with pytest.raises(HighlightAnalysisError):
        parse_highlights("No moments found.", duration_ms=60000)
