"""
missing-ag-updater (Cross-Platform)
----------------------------------
An unofficial, community-maintained Python utility to check, download, and
install updates for the Antigravity IDE, Antigravity Hub, and Antigravity CLI.
Supports Linux, macOS, and Windows.

Disclaimer: This tool is not affiliated with, sponsored by, or supported by Google.
"""

from .cli import main
from .config import ResolvedConfig, resolve_config
from .const import __version__
from .discovery import (
    InstallationInfo,
    clean_duplicate_desktop_entries,
    detect_cli_self_update,
    diagnose_all,
    find_all_cli_installations,
    find_all_hub_installations,
    find_all_ide_installations,
)
from .exceptions import ReleaseEndpointError
from .uninstall import uninstall_cli, uninstall_hub, uninstall_ide
from .updater import update_cli, update_hub, update_ide
from .utils import set_debug_enabled

__all__ = [
    "__version__",
    "main",
    "resolve_config",
    "ResolvedConfig",
    "diagnose_all",
    "clean_duplicate_desktop_entries",
    "detect_cli_self_update",
    "find_all_ide_installations",
    "find_all_hub_installations",
    "find_all_cli_installations",
    "InstallationInfo",
    "ReleaseEndpointError",
    "set_debug_enabled",
    "update_ide",
    "update_hub",
    "update_cli",
    "uninstall_ide",
    "uninstall_hub",
    "uninstall_cli",
]
