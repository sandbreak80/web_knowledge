"""Configuration loader for WebArc."""

import yaml
from pathlib import Path
from typing import Optional

from webarc.config.schema import WebArcConfig


def find_config_file() -> Optional[Path]:
    """Find webarc.yaml config file in standard locations."""
    # Check current directory
    current_dir = Path.cwd()
    config_paths = [
        current_dir / "webarc.yaml",
        current_dir / "config" / "webarc.yaml",
        Path.home() / ".webarc" / "webarc.yaml",
    ]
    
    for path in config_paths:
        if path.exists():
            return path
    
    return None


def load_config(config_path: Optional[str] = None) -> WebArcConfig:
    """
    Load configuration from YAML file or use defaults.
    
    Args:
        config_path: Optional path to config file. If None, searches standard locations.
    
    Returns:
        WebArcConfig instance with loaded or default values.
    """
    if config_path:
        path = Path(config_path)
    else:
        path = find_config_file()
    
    if path and path.exists():
        with open(path, 'r', encoding='utf-8') as f:
            config_dict = yaml.safe_load(f) or {}
    else:
        config_dict = {}
    
    # Create config with defaults, then override with loaded values
    # Use Pydantic's model_validate to properly construct nested models
    try:
        # Merge defaults with loaded values
        default_dict = WebArcConfig().model_dump()
        merged_dict = {**default_dict, **config_dict}
        # Recursively merge nested dicts
        for key, value in config_dict.items():
            if isinstance(value, dict) and key in default_dict:
                merged_dict[key] = {**default_dict[key], **value}
        config = WebArcConfig.model_validate(merged_dict)
    except Exception:
        # Fallback: create with defaults
        config = WebArcConfig()
        # Manually update if validation fails
        if config_dict:
            for section, values in config_dict.items():
                if hasattr(config, section) and isinstance(values, dict):
                    section_obj = getattr(config, section)
                    for key, value in values.items():
                        if hasattr(section_obj, key):
                            setattr(section_obj, key, value)
    
    return config
