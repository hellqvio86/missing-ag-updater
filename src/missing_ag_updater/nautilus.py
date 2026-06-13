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
from gi.repository import Nautilus, GObject

class OpenInAntigravityIDE(GObject.GObject, Nautilus.MenuProvider):
    def _path(self, file_info):
        uri = file_info.get_uri()
        parsed = urlparse(uri)
        if parsed.scheme != 'file':
            return None
        return unquote(parsed.path)

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
        item.connect('activate', lambda _item: subprocess.Popen(['{exec_path}', path]))
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
        item.connect('activate', lambda _item: subprocess.Popen(['{exec_path}', path]))
        return [item]
"""
    try:
        with open(nautilus_file, "w", encoding="utf-8") as nf:
            nf.write(nautilus_content)
        print_success(f"Installed Nautilus context-menu: {nautilus_file}")
    except Exception as ne:
        print_warning(f"Could not install Nautilus context-menu: {ne}")

    refresh_linux_desktop_caches()
