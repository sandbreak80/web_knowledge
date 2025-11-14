"""Unit tests for the StateManager."""

from pathlib import Path
from unittest.mock import MagicMock

import pytest

from webarc.crawler.state import StateManager


@pytest.fixture
def output_dir(tmp_path):
    return Path(tmp_path)


def test_save_and_load_state(output_dir):
    manager = StateManager(output_dir)
    state = {
        "seed_url": "https://example.com",
        "config_hash": "abc",
        "pages_crawled": 5,
        "queue": ["https://example.com/next"],
        "visited": ["https://example.com"],
    }
    manager.save_state(state)
    loaded = manager.load_state()
    assert loaded is not None
    assert loaded["seed_url"] == "https://example.com"
    assert loaded["pages_crawled"] == 5
    assert loaded["pages_queued"] == 1


def test_maybe_checkpoint_interval(output_dir):
    manager = StateManager(output_dir, checkpoint_interval=2)
    manager.save_state = MagicMock()
    state = {"seed_url": "https://example.com"}
    manager.maybe_checkpoint(state)
    manager.save_state.assert_not_called()
    manager.maybe_checkpoint(state)
    manager.save_state.assert_called_once_with(state)


def test_load_state_missing(output_dir):
    manager = StateManager(output_dir)
    assert manager.load_state() is None


def test_load_state_bad_json(output_dir, caplog):
    manager = StateManager(output_dir)
    resume = output_dir / "resume.jsonl"
    resume.write_text("not json")
    with caplog.at_level("ERROR"):
        loaded = manager.load_state()
    assert loaded is None
    assert "Failed to load state" in caplog.text

