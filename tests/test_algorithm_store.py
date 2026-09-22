import pytest

store_module = pytest.importorskip("api.services.algorithm_store")


def test_register_list_and_delete_round_trip(tmp_path):
    store = store_module.AlgorithmStore(str(tmp_path), str(tmp_path / "state.db"))

    created = store.register(
        "RSI Strategy",
        "rsi.py",
        ["numpy"],
        b"print('strategy')\n",
    )

    assert created["id"] == "rsi"
    assert (tmp_path / "algorithms" / "rsi.py").read_bytes() == b"print('strategy')\n"
    assert store.list_algorithms()[0]["dependencies"] == ["numpy"]
    assert str(store.get_script_path("rsi")).endswith("algorithms/rsi.py")

    assert store.delete("rsi") is True
    assert store.list_algorithms() == []
    assert not (tmp_path / "algorithms" / "rsi.py").exists()


def test_rejects_path_traversal_and_does_not_write_outside_store(tmp_path):
    store = store_module.AlgorithmStore(str(tmp_path), str(tmp_path / "state.db"))

    with pytest.raises((ValueError, OSError)):
        store.register(
            "Escape",
            "../outside.py",
            [],
            b"should not be written",
        )

    assert not (tmp_path.parent / "outside.py").exists()


def test_missing_algorithm_operations_are_safe(tmp_path):
    store = store_module.AlgorithmStore(str(tmp_path), str(tmp_path / "state.db"))

    assert store.delete("missing") is False
    assert store.get_script_path("missing") is None


def test_algorithm_run_lifecycle_is_persisted(tmp_path):
    store = store_module.AlgorithmStore(str(tmp_path), str(tmp_path / "state.db"))
    store.register("RSI Strategy", "rsi.py", [], b"print('strategy')\n")

    run = store.start_run("rsi")
    active = store.find_active_run("rsi")
    assert active is not None
    assert active["run_id"] == run["run_id"]

    assert store.finish_run(run["run_id"], status="Stopped") is True
    stopped = store.list_algorithms()[0]["history"][0]
    assert stopped["status"] == "Stopped"
