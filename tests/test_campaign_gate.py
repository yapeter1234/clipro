from services.worker.app.campaign_gate import (
    evaluate_diego_gta_stream,
    evaluate_diego_gta6_stream,
    is_grand_theft_auto_category,
)


def test_diego_live_gta_stream_is_eligible():
    result = evaluate_diego_gta_stream(
        {
            "user_login": "diegoloveless",
            "type": "live",
            "game_name": "Grand Theft Auto VI",
        }
    )
    assert result.eligible is True
    assert result.reasons == ()


def test_diego_gta_v_category_is_allowed_by_franchise_brief():
    result = evaluate_diego_gta_stream(
        {
            "user_login": "diegoloveless",
            "type": "live",
            "game_name": "Grand Theft Auto V",
        }
    )
    assert result.eligible is True


def test_wrong_creator_is_rejected():
    result = evaluate_diego_gta_stream(
        {
            "user_login": "someoneelse",
            "type": "live",
            "game_name": "Grand Theft Auto VI",
        }
    )
    assert result.eligible is False
    assert any("DiegoLoveless" in reason for reason in result.reasons)


def test_wrong_game_is_rejected():
    result = evaluate_diego_gta_stream(
        {
            "user_login": "diegoloveless",
            "type": "live",
            "game_name": "Just Chatting",
        }
    )
    assert result.eligible is False
    assert any("Grand Theft Auto title" in reason for reason in result.reasons)


def test_offline_or_missing_stream_is_rejected():
    assert evaluate_diego_gta_stream(None).eligible is False


def test_gta_category_aliases_are_normalized():
    assert is_grand_theft_auto_category("GTA 6")
    assert is_grand_theft_auto_category("  grand theft auto online  ")
    assert is_grand_theft_auto_category("gta v")
    assert not is_grand_theft_auto_category("Grand Theft Auto RP Servers")


def test_backward_compatible_function_name_still_works():
    result = evaluate_diego_gta6_stream(
        {
            "user_login": "diegoloveless",
            "type": "live",
            "game_name": "Grand Theft Auto VI",
        }
    )
    assert result.eligible is True
