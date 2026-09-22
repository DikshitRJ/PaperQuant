import pytest

schemas = pytest.importorskip("api.schemas")


def test_position_schema_matches_frontend_contract():
    position = schemas.Position(
        ticker="AAPL",
        initials="AA",
        qty=10,
        avg_price=185.5,
        current_price=187.2,
        invested="$1,855.00",
        current="$1,872.00",
        pnl="+$17.00",
        pnl_percent="+0.92%",
        strategy_id="rsi",
    )

    assert position.ticker == "AAPL"
    assert position.qty == 10
    dumped = (
        position.model_dump() if hasattr(position, "model_dump") else position.dict()
    )
    assert dumped["pnl_percent"] == "+0.92%"


def test_session_start_request_applies_watchlist_defaults():
    request = schemas.SessionStartRequest(
        watchlist=[{"ticker": "MSFT"}],
    )

    assert request.watchlist[0].ticker == "MSFT"
    assert request.watchlist[0].capital == 1000.0
    assert request.strategy_id is None


def test_settings_schema_contains_safe_defaults():
    settings = schemas.Settings()

    assert settings.currency == "USD"
    assert settings.theme == "dark"
    assert settings.auto_clear_logs is True
    assert settings.terminal_font_size == 14
