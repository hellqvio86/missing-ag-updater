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
from .discovery import clean_duplicate_desktop_entries, diagnose_all
from .uninstall import uninstall_cli, uninstall_hub, uninstall_ide
from .updater import update_cli, update_hub, update_ide

__all__ = [
    "__version__",
    "main",
    "resolve_config",
    "ResolvedConfig",
    "diagnose_all",
    "clean_duplicate_desktop_entries",
    "update_ide",
    "update_hub",
    "update_cli",
    "uninstall_ide",
    "uninstall_hub",
    "uninstall_cli",
]
