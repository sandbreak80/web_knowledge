"""Basic test for config loading."""

from webarc.config.loader import load_config
from webarc.config.schema import WebArcConfig


def test_config_loads_with_defaults():
    """Test that config loads with default values."""
    config = load_config()
    assert isinstance(config, WebArcConfig)
    assert config.crawler.max_depth == 3
    assert config.safety.mode == "advisory"
    assert config.output.format == "obsidian"


def test_config_sections_exist():
    """Test that all config sections exist."""
    config = load_config()
    assert hasattr(config, 'crawler')
    assert hasattr(config, 'safety')
    assert hasattr(config, 'render')
    assert hasattr(config, 'extraction')
    assert hasattr(config, 'output')
    assert hasattr(config, 'logging')
    assert hasattr(config, 'adapters')
