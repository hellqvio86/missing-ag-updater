import os
import shutil
from typing import Optional

from .const import USER_APPLICATIONS_DIR, USER_ICONS_DIR
from .utils import extract_asar_icon, print_success, print_warning, refresh_linux_desktop_caches


def install_ide_desktop(ide_dir: str, launcher_path: Optional[str]) -> None:
    """Create local Linux desktop entry and install icon for Antigravity IDE."""
    os.makedirs(USER_APPLICATIONS_DIR, exist_ok=True)
    desktop_file = os.path.join(USER_APPLICATIONS_DIR, "antigravity-ide.desktop")
    exec_path = launcher_path or os.path.join(ide_dir, "bin", "antigravity-ide")

    desktop_content = f"""[Desktop Entry]
Name=Antigravity IDE
Comment=Google Antigravity IDE
Exec={exec_path} %F
Icon=antigravity-ide
Terminal=false
Type=Application
Categories=Development;IDE;
MimeType=inode/directory;text/plain;application/x-code-workspace;application/x-antigravity-workspace;x-scheme-handler/antigravity-ide;
StartupNotify=true
StartupWMClass=antigravity-ide
"""
    try:
        with open(desktop_file, "w", encoding="utf-8") as df:
            df.write(desktop_content)
        print_success(f"Installed desktop entry: {desktop_file}")
    except Exception as de:
        print_warning(f"Could not install desktop entry: {de}")

    # Copy icon
    icon_source = os.path.join(ide_dir, "resources", "app", "resources", "linux", "code.png")
    if os.path.exists(icon_source):
        os.makedirs(USER_ICONS_DIR, exist_ok=True)
        try:
            shutil.copy2(icon_source, os.path.join(USER_ICONS_DIR, "antigravity-ide.png"))
            print_success("Installed local IDE icon.")
        except Exception as ie:
            print_warning(f"Could not install local IDE icon: {ie}")

    refresh_linux_desktop_caches()


def install_hub_desktop(hub_dir: str, launcher_path: Optional[str]) -> None:
    """Create local Linux desktop entry and extract icon for Antigravity Hub."""
    os.makedirs(USER_APPLICATIONS_DIR, exist_ok=True)
    desktop_file = os.path.join(USER_APPLICATIONS_DIR, "antigravity.desktop")
    exec_path = launcher_path or os.path.join(hub_dir, "antigravity")

    desktop_content = f"""[Desktop Entry]
Name=Antigravity
Comment=Google Antigravity 2.0 agent platform
Exec={exec_path} %U
Icon=antigravity
Terminal=false
Type=Application
Categories=Development;IDE;
StartupNotify=true
StartupWMClass=Antigravity
"""
    try:
        with open(desktop_file, "w", encoding="utf-8") as df:
            df.write(desktop_content)
        print_success(f"Installed desktop entry: {desktop_file}")
    except Exception as de:
        print_warning(f"Could not install desktop entry: {de}")

    # Extract icon from app.asar
    asar_path = os.path.join(hub_dir, "resources", "app.asar")
    if os.path.exists(asar_path):
        dest_icon = os.path.join(USER_ICONS_DIR, "antigravity.png")
        if extract_asar_icon(asar_path, dest_icon):
            print_success("Extracted and installed local Hub icon.")
        else:
            print_warning("Could not extract local Hub icon.")

    refresh_linux_desktop_caches()
