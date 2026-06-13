import os
from typing import Optional

from .const import USER_NAUTILUS_DIR
from .utils import print_success, print_warning, refresh_linux_desktop_caches


def install_ide_nautilus(ide_dir: str, launcher_path: Optional[str]) -> None:
    """Install Nautilus context-menu integration script for user."""
    os.makedirs(USER_NAUTILUS_DIR, exist_ok=True)
    nautilus_file = os.path.join(USER_NAUTILUS_DIR, "open-in-antigravity-ide.py")
    exec_path = launcher_path or os.path.join(ide_dir, "bin", "antigravity-ide")
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
        subprocess.Popen(['{exec_path}', path])

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
        with open(nautilus_file, "w", encoding="utf-8") as nf:
            nf.write(nautilus_content)
        print_success(f"Installed Nautilus context-menu: {nautilus_file}")
    except Exception as ne:
        print_warning(f"Could not install Nautilus context-menu: {ne}")

    refresh_linux_desktop_caches()
