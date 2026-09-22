import pytest


portfolio_module = pytest.importorskip("api.services.portfolio")


class FakeCache:
    def __init__(self, values):
        self.values = values

    def iterkeys(self):
        return iter(self.values)

    def get(self, key, default=None):
        return self.values.get(key, default)


def make_service(state, prices):
    service = portfolio_module.PortfolioService.__new__(
        portfolio_module.PortfolioService
    )
    service.state_cache = FakeCache(state)
    service.prices_cache = FakeCache(prices)
    return service


def test_enriches_long_position_with_live_price_and_pnl():
    service = make_service(
        {"rsi:AAPL": {"qty": 10, "avg_price": 100.0}},
        {"prices:AAPL": [{"price": 105.0, "ts": 1}]},
    )

    position = service.get_enriched_positions()[0]

    assert position == {
        "ticker": "AAPL",
        "initials": "AA",
        "qty": 10,
        "avg_price": 100.0,
        "current_price": 105.0,
        "invested": "$1,000.00",
        "current": "$1,050.00",
        "pnl": "+50.00",
        "pnl_percent": "+5.00%",
        "strategy_id": "rsi",
    }


def test_ignores_empty_and_non_position_cache_entries():
    service = make_service(
        {
            "rsi:AAPL": {"qty": 0, "avg_price": 100.0},
            "not-a-position": {"qty": 3, "avg_price": 1.0},
        },
        {},
    )

    assert service.get_enriched_positions() == []


def test_uses_average_price_when_no_live_tick_exists():
    service = make_service(
        {"rsi:MSFT": {"qty": 2, "avg_price": 50.0}},
        {},
    )

    position = service.get_enriched_positions()[0]

    assert position["current_price"] == 50.0
    assert position["pnl"] == "+0.00"
    assert position["pnl_percent"] == "+0.00%"
