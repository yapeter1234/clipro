"""Validation helpers for model-generated highlight candidates."""
from __future__ import annotations
import json
from typing import Any

class HighlightAnalysisError(ValueError):
    """The model did not return a usable highlight plan."""

def parse_highlights(response: str, *, duration_ms: int, limit: int = 12) -> list[dict[str, Any]]:
    text = response.strip()
    if text.lower().startswith("json"):
        text = text[4:].strip()
    start, end = text.find("{"), text.rfind("}")
    if start < 0 or end <= start:
        start, end = text.find("["), text.rfind("]")
    if start < 0 or end <= start:
        raise HighlightAnalysisError("The analysis model returned no JSON highlight list.")
    try:
        payload = json.loads(text[start:end + 1])
    except json.JSONDecodeError as exc:
        raise HighlightAnalysisError("The analysis model returned invalid JSON.") from exc
    raw_items = payload.get("highlights") if isinstance(payload, dict) else payload
    if not isinstance(raw_items, list):
        raise HighlightAnalysisError("The analysis model did not return a highlights array.")
    normalized = []
    for item in raw_items:
        if not isinstance(item, dict):
            continue
        try:
            start_ms = max(0, round(float(item.get("start_seconds", item.get("start", 0))) * 1000))
            end_ms = min(duration_ms, round(float(item.get("end_seconds", item.get("end", 0))) * 1000))
            score = float(item.get("score", 5))
        except (TypeError, ValueError):
            continue
        if end_ms <= start_ms or end_ms - start_ms < 5000 or start_ms >= duration_ms:
            continue
        end_ms = min(end_ms, start_ms + 90000)
        normalized.append({
            "start_ms": start_ms, "end_ms": end_ms, "duration_ms": end_ms - start_ms,
            "title": str(item.get("title") or "Untitled moment").strip()[:120] or "Untitled moment",
            "hook": str(item.get("hook") or "").strip()[:220],
            "rationale": str(item.get("rationale") or "").strip()[:500],
            "score": round(max(0.0, min(10.0, score)), 1),
        })
    normalized.sort(key=lambda item: item["score"], reverse=True)
    selected = []
    for candidate in normalized:
        if any(candidate["start_ms"] < chosen["end_ms"] and candidate["end_ms"] > chosen["start_ms"] for chosen in selected):
            continue
        selected.append(candidate)
        if len(selected) >= limit:
            break
    if not selected:
        raise HighlightAnalysisError("The model did not identify any valid highlight moments.")
    return sorted(selected, key=lambda item: item["start_ms"])
