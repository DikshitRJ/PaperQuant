import pytest

settings_module = pytest.importorskip("api.services.settings_store")
logs_module = pytest.importorskip("api.services.log_buffer")


def test_settings_are_persisted_and_unknown_keys_are_ignored(tmp_path):
    first = settings_module.SettingsStore(str(tmp_path))
    updated = first.update({"leverage": 5, "unknown": "ignored"})

    assert updated["leverage"] == 5
    assert "unknown" not in updated

    second = settings_module.SettingsStore(str(tmp_path))
    assert second.get_all()["leverage"] == 5
    assert second.get_all()["currency"] == "USD"


def test_log_buffer_formats_sources_and_detects_errors():
    buffer = logs_module.LogBuffer(max_size=2)
    buffer.add("trade_adapter", "filled AAPL")
    buffer.add("system", "adapter failed")

    entries = buffer.get_all()
    assert entries[0]["content"] == "[TRADE_ADAPTER] filled AAPL"
    assert entries[0]["color"] == "text-yellow-400"
    assert entries[1]["color"] == "text-red-400"
    assert set(entries[1]) == {"time", "content", "color"}


def test_log_buffer_is_bounded_and_clearable():
    buffer = logs_module.LogBuffer(max_size=1)
    buffer.add("system", "first")
    buffer.add("system", "second")

    assert len(buffer.get_all()) == 1
    assert buffer.get_all()[0]["content"].endswith("second")
    buffer.clear()
    assert buffer.get_all() == []
