import json
from pathlib import Path

from jsonschema import Draft202012Validator, FormatChecker

ROOT = Path(__file__).resolve().parents[1]
SCHEMA_PATH = ROOT / "packages" / "timeline" / "schema.json"
EXAMPLE_PATH = (
    ROOT / "packages" / "timeline" / "examples" / "streamer_reaction.json"
)


def load_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def test_timeline_schema_is_valid_json_schema():
    schema = load_json(SCHEMA_PATH)
    Draft202012Validator.check_schema(schema)


def test_streamer_reaction_example_matches_schema():
    schema = load_json(SCHEMA_PATH)
    example = load_json(EXAMPLE_PATH)
    validator = Draft202012Validator(
        schema,
        format_checker=FormatChecker(),
    )
    errors = sorted(
        validator.iter_errors(example),
        key=lambda error: list(error.absolute_path),
    )
    assert not errors, "\n".join(
        f"{list(error.absolute_path)}: {error.message}" for error in errors
    )


def test_all_media_clips_reference_declared_assets():
    project = load_json(EXAMPLE_PATH)
    asset_ids = {asset["asset_id"] for asset in project["assets"]}

    for track in project["tracks"]:
        for item in track["items"]:
            if item["type"] == "media_clip":
                assert item["asset_id"] in asset_ids


def test_source_ranges_are_positive():
    project = load_json(EXAMPLE_PATH)

    for track in project["tracks"]:
        for item in track["items"]:
            if item["type"] == "media_clip":
                assert item["source_out_ms"] > item["source_in_ms"]
            elif item["type"] == "caption_cue":
                assert item["end_ms"] > item["start_ms"]
            elif item["type"] == "overlay":
                assert item["end_ms"] > item["start_ms"]
