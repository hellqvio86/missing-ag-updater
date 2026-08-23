"""GNOME Nautilus file manager integration for Antigravity IDE."""

import json
import os
from typing import Optional

from .const import SYSTEM_NAUTILUS_DIR, USER_NAUTILUS_DIR
from .utils import print_success, print_warning, refresh_linux_desktop_caches


def install_ide_nautilus(
    ide_dir: str,
    launcher_path: Optional[str],
    *,
    scope: str = "user",
) -> None:
    """Install Nautilus context-menu integration script for user or system."""
    target_dir = SYSTEM_NAUTILUS_DIR if scope == "system" else USER_NAUTILUS_DIR
    nautilus_file = os.path.join(target_dir, "open-in-antigravity-ide.py")
    exec_path = launcher_path or os.path.join(ide_dir, "bin", "antigravity-ide")
    exec_path_escaped = json.dumps(exec_path)
    nautilus_content = f"""import subprocess
from urllib.parse import unquote, urlparse
import gi
try:
    gi.require_version('Nautilus', '4.0')
except ValueError:
    pass
from gi.repository import Nautilus, GObject

try:
    nautilus_version = gi.get_required_version('Nautilus')
except ValueError:
    nautilus_version = None

if nautilus_version:
    try:
        major = int(nautilus_version.split('.')[0])
        if major < 4:
            raise ImportError("Nautilus 4.0 or greater is required")
    except (ValueError, IndexError):
        pass

class OpenInAntigravityIDE(GObject.GObject, Nautilus.MenuProvider):
    def _path(self, file_info):
        uri = file_info.get_uri()
        parsed = urlparse(uri)
        if parsed.scheme != 'file':
            return None
        return unquote(parsed.path)

    def _activate(self, menu_item, path):
        subprocess.Popen([{exec_path_escaped}, path])

    def get_file_items(self, files):
        if not files or len(files) != 1:
            return []
        path = self._path(files[0])
        if not path:
            return []
        item = Nautilus.MenuItem(
            name='OpenInAntigravityIDE::open',
            label='Open in Antigravity IDE',
            tip='Open this folder or file in Antigravity IDE'
        )
        item.connect('activate', self._activate, path)
        return [item]

    def get_background_items(self, folder):
        path = self._path(folder)
        if not path:
            return []
        item = Nautilus.MenuItem(
            name='OpenInAntigravityIDE::open_background',
            label='Open Folder in Antigravity IDE',
            tip='Open the current folder in Antigravity IDE'
        )
        item.connect('activate', self._activate, path)
        return [item]
"""
    try:
        os.makedirs(target_dir, exist_ok=True)
        with open(nautilus_file, "w", encoding="utf-8") as nf:
            nf.write(nautilus_content)
        print_success(f"Installed Nautilus context-menu: {nautilus_file}")
    except (OSError, Exception) as ne:
        print_warning(f"Could not install Nautilus context-menu: {ne}")

    refresh_linux_desktop_caches()
