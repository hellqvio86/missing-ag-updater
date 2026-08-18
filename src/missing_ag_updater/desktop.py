"""Linux desktop entry and icon installation for Antigravity IDE and Hub."""

import os
import shutil
from typing import Optional

from .const import (
    SYSTEM_APPLICATIONS_DIR,
    SYSTEM_ICONS_DIR,
    USER_APPLICATIONS_DIR,
    USER_ICONS_DIR,
)
from .utils import (
    extract_asar_icon,
    print_info,
    print_success,
    print_warning,
    refresh_linux_desktop_caches,
)


def install_ide_desktop(
    ide_dir: str,
    launcher_path: Optional[str],
    *,
    scope: str = "user",
) -> None:
    """Create Linux desktop entry and install icon for Antigravity IDE (user or system scope)."""
    app_dir = SYSTEM_APPLICATIONS_DIR if scope == "system" else USER_APPLICATIONS_DIR
    icons_dir = SYSTEM_ICONS_DIR if scope == "system" else USER_ICONS_DIR

    os.makedirs(app_dir, exist_ok=True)
    desktop_file = os.path.join(app_dir, "antigravity-ide.desktop")
    exec_path = launcher_path or os.path.join(ide_dir, "bin", "antigravity-ide")

    desktop_content = f"""[Desktop Entry]
Name=Antigravity IDE
Comment=Google Antigravity IDE
Exec={exec_path} %F
Icon=antigravity
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
    except OSError as de:
        print_warning(f"Could not install desktop entry {desktop_file}: {de}")

    # Copy icon: prefer official Antigravity branding icon if available, falling back to code.png
    dest_icon = os.path.join(icons_dir, "antigravity.png")
    dest_ide_icon = os.path.join(icons_dir, "antigravity-ide.png")
    installed_official_icon = False
    candidate_icons = [
        os.path.join(icons_dir, "antigravity.png"),
        os.path.join(USER_ICONS_DIR, "antigravity.png"),
        os.path.join(SYSTEM_ICONS_DIR, "antigravity.png"),
    ]
    for cand in candidate_icons:
        if os.path.exists(cand):
            try:
                os.makedirs(icons_dir, exist_ok=True)
                if cand != dest_icon:
                    shutil.copy2(cand, dest_icon)
                if cand != dest_ide_icon:
                    shutil.copy2(cand, dest_ide_icon)
                installed_official_icon = True
                print_success(f"Installed {'system' if scope == 'system' else 'local'} IDE icon.")
                break
            except (OSError, shutil.Error):
                pass

    if not installed_official_icon:
        icon_source = os.path.join(ide_dir, "resources", "app", "resources", "linux", "code.png")
        if not os.path.exists(icon_source):
            # Check nested directory
            icon_source = os.path.join(
                ide_dir,
                "Antigravity-IDE",
                "resources",
                "app",
                "resources",
                "linux",
                "code.png",
            )

        if os.path.exists(icon_source):
            os.makedirs(icons_dir, exist_ok=True)
            try:
                shutil.copy2(icon_source, dest_icon)
                shutil.copy2(icon_source, dest_ide_icon)
                print_success(f"Installed {'system' if scope == 'system' else 'local'} IDE icon.")
            except (OSError, shutil.Error) as ie:
                print_warning(f"Could not install IDE icon: {ie}")

    # If installing to system, check and remove duplicate user desktop entry if present
    if scope == "system":
        user_dt = os.path.join(USER_APPLICATIONS_DIR, "antigravity-ide.desktop")
        if os.path.exists(user_dt):
            try:
                os.remove(user_dt)
                print_info(f"Removed shadowed user desktop entry to prevent duplicate icons: {user_dt}")
            except OSError:
                pass
    elif scope == "user":
        sys_dt = os.path.join(SYSTEM_APPLICATIONS_DIR, "antigravity-ide.desktop")
        if os.path.exists(sys_dt):
            print_info(f"Notice: System desktop entry also exists at {sys_dt}. User entry will take precedence.")

    refresh_linux_desktop_caches()


def install_hub_desktop(
    hub_dir: str,
    launcher_path: Optional[str],
    *,
    scope: str = "user",
) -> None:
    """Create Linux desktop entry and extract icon for Antigravity Hub (user or system scope)."""
    app_dir = SYSTEM_APPLICATIONS_DIR if scope == "system" else USER_APPLICATIONS_DIR
    icons_dir = SYSTEM_ICONS_DIR if scope == "system" else USER_ICONS_DIR

    os.makedirs(app_dir, exist_ok=True)
    desktop_file = os.path.join(app_dir, "antigravity.desktop")
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
    except OSError as de:
        print_warning(f"Could not install desktop entry {desktop_file}: {de}")

    # Extract icon from app.asar
    asar_path = os.path.join(hub_dir, "resources", "app.asar")
    if not os.path.exists(asar_path):
        asar_path = os.path.join(hub_dir, "Antigravity-x64", "resources", "app.asar")

    if os.path.exists(asar_path):
        dest_icon = os.path.join(icons_dir, "antigravity.png")
        if extract_asar_icon(asar_path, dest_icon):
            print_success(f"Extracted and installed {'system' if scope == 'system' else 'local'} Hub icon.")
            # Also ensure IDE icon has official branding if IDE desktop is present
            ide_dest_icon = os.path.join(icons_dir, "antigravity-ide.png")
            try:
                shutil.copy2(dest_icon, ide_dest_icon)
            except (OSError, shutil.Error):
                pass
        else:
            print_warning("Could not extract Hub icon.")

    if scope == "system":
        user_dt = os.path.join(USER_APPLICATIONS_DIR, "antigravity.desktop")
        if os.path.exists(user_dt):
            try:
                os.remove(user_dt)
                print_info(f"Removed shadowed user desktop entry to prevent duplicate icons: {user_dt}")
            except OSError:
                pass
    elif scope == "user":
        sys_dt = os.path.join(SYSTEM_APPLICATIONS_DIR, "antigravity.desktop")
        if os.path.exists(sys_dt):
            print_info(f"Notice: System desktop entry also exists at {sys_dt}. User entry will take precedence.")

    refresh_linux_desktop_caches()
