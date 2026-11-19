import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def read_json(relative_path: str):
    return json.loads((ROOT / relative_path).read_text(encoding="utf-8"))


def test_diego_campaign_is_twitch_only_and_manual_download():
    cfg = read_json("config/campaigns/diego-loveless-gta6.json")
    assert cfg["creator"]["channel_login"] == "diegoloveless"
    assert cfg["source_policy"]["allowed_platforms"] == ["twitch"]
    assert cfg["source_policy"]["allowed_source_types"] == [
        "live_stream",
        "past_broadcast",
    ]
    assert cfg["source_policy"]["acquisition_mode"] == (
        "viewer_native_clip_manual_download"
    )
    assert cfg["source_policy"]["editor_role_required"] is False
    assert cfg["source_policy"]["editor_api_enabled"] is False


def test_diego_campaign_contains_all_mandatory_cta_and_hashtags():
    cfg = read_json("config/campaigns/diego-loveless-gta6.json")
    assert cfg["output"]["cta_required"] is True
    assert cfg["output"]["required_cta_destination"] == (
        "https://twitch.tv/diegoloveless"
    )
    assert set(cfg["output"]["required_hashtags"]) == {
        "#GTA",
        "#DiegoLoveless",
    }


def test_diego_campaign_never_publishes_and_tracks_post_metrics():
    cfg = read_json("config/campaigns/diego-loveless-gta6.json")
    assert cfg["publishing_rules"]["clipro_publishing_enabled"] is False
    assert cfg["publishing_rules"]["manual_user_publishing_only"] is True
    assert cfg["publishing_rules"]["likes_must_be_visible"] is True
    assert cfg["publishing_rules"]["min_post_live_days"] == 30
    assert cfg["publishing_rules"]["min_engagement_rate"] == 0.008
    assert cfg["publishing_rules"]["min_tier1_audience_share"] == 0.4
    assert cfg["publishing_rules"]["tier1_countries"] == ["US", "GB", "CA", "AU"]


def test_temporary_gta_window_is_seven_days_from_november_18():
    cfg = read_json("config/campaigns/diego-loveless-gta6.json")
    window = cfg["campaign_window"]
    assert window["effective_from"] == "2026-11-18"
    assert window["duration_days"] == 7
    assert window["effective_until_exclusive"] == "2026-11-25"


def test_general_campaign_template_is_not_locked_to_diego():
    cfg = read_json("config/campaigns/template.json")
    assert cfg["creator"]["display_name"] == ""
    assert set(cfg["source_policy"]["allowed_platforms"]) == {
        "twitch",
        "kick",
        "youtube",
    }
    assert cfg["publishing_rules"]["automatic_publishing"] is False


def test_streamer_brainrot_style_keeps_quality_guardrails():
    cfg = read_json("config/styles/streamer-brainrot.json")
    assert cfg["style_id"] == "streamer-brainrot"
    assert cfg["audio"]["voiceover_original_only"] is True
    assert "do not humiliate creator" in cfg["guardrails"]
