from services.worker.app.campaign_gate import evaluate_diego_gta6_stream


def test_diego_live_gta6_stream_is_eligible():
    result = evaluate_diego_gta6_stream(
        {
            "user_login": "diegoloveless",
            "type": "live",
            "game_name": "Grand Theft Auto VI",
        }
    )
    assert result.eligible is True
    assert result.reasons == ()


def test_wrong_creator_is_rejected():
    result = evaluate_diego_gta6_stream(
        {
            "user_login": "someoneelse",
            "type": "live",
            "game_name": "Grand Theft Auto VI",
        }
    )
    assert result.eligible is False
    assert any("DiegoLoveless" in reason for reason in result.reasons)


def test_wrong_game_is_rejected():
    result = evaluate_diego_gta6_stream(
        {
            "user_login": "diegoloveless",
            "type": "live",
            "game_name": "Just Chatting",
        }
    )
    assert result.eligible is False
    assert any("Grand Theft Auto VI" in reason for reason in result.reasons)


def test_offline_or_missing_stream_is_rejected():
    assert evaluate_diego_gta6_stream(None).eligible is False
