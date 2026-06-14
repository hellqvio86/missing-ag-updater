import os
from pathlib import Path
from typing import Any, Dict

# Use standard library tomllib (Python 3.11+)
import tomllib

from .const import HOME, OS_NAME


def get_default_config_path() -> Path:
    """Get the standard configuration file path based on OS."""
    home_path = Path(HOME)
    if OS_NAME == "linux":
        xdg_config = os.environ.get("XDG_CONFIG_HOME")
        if xdg_config:
            base_dir = Path(xdg_config)
        else:
            base_dir = home_path / ".config"
        return base_dir / "missing-ag-updater" / "config.toml"

    elif OS_NAME == "darwin":
        return home_path / "Library" / "Application Support" / "missing-ag-updater" / "config.toml"

    elif OS_NAME == "windows":
        appdata = os.environ.get("APPDATA")
        if appdata:
            base_dir = Path(appdata)
        else:
            base_dir = home_path / "AppData" / "Roaming"
        return base_dir / "missing-ag-updater" / "config.toml"

    else:
        return home_path / ".missing-ag-updater.toml"


def load_toml_config(path: str | Path, *, explicit: bool = False) -> Dict[str, Any]:
    """Load settings from a TOML configuration file.

    If explicit is True, raise FileNotFoundError if the file does not exist.
    Otherwise, return an empty dictionary if the file is missing.
    """
    config_file = Path(path)
    if not config_file.exists():
        if explicit:
            raise FileNotFoundError(f"Configuration file not found: {config_file}")
        return {}

    try:
        with config_file.open("rb") as f:
            return tomllib.load(f)
    except Exception as e:
        if explicit:
            raise ValueError(f"Failed to parse TOML configuration file: {e}")
        from .utils import print_warning

        print_warning(f"Could not load configuration file {config_file}: {e}")
        return {}
