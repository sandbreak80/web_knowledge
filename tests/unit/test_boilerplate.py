"""Unit tests for boilerplate extractor."""

from unittest.mock import MagicMock

import pytest

from webarc.extractors.boilerplate import extract_main_content


def test_extract_main_content_success(monkeypatch):
    fake_doc = MagicMock()
    fake_doc.summary.return_value = "<p>content</p>"
    monkeypatch.setattr("webarc.extractors.boilerplate.Document", MagicMock(return_value=fake_doc))
    result = extract_main_content("<html></html>", "https://example.com")
    assert result == "<p>content</p>"
    fake_doc.summary.assert_called_once()


def test_extract_main_content_failure(monkeypatch, caplog):
    monkeypatch.setattr(
        "webarc.extractors.boilerplate.Document",
        MagicMock(side_effect=RuntimeError("boom")),
    )
    with caplog.at_level("WARNING"):
        result = extract_main_content("<html></html>", "https://example.com")
    assert result is None
    assert "Failed to extract content" in caplog.text

