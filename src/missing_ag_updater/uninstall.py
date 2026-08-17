import os
import shutil
from typing import Optional

from .const import (
    OS_NAME,
    SYSTEM_APPLICATIONS_DIR,
    SYSTEM_ICONS_DIR,
    SYSTEM_NAUTILUS_DIR,
    USER_APPLICATIONS_DIR,
    USER_ICONS_DIR,
    USER_NAUTILUS_DIR,
)
from .discovery import (
    detect_preferred_cli,
    detect_preferred_hub,
    detect_preferred_ide,
    refresh_linux_desktop_caches,
)
from .utils import (
    get_running_pids,
    is_path_writable,
    print_error,
    print_info,
    print_status,
    print_success,
    print_warning,
    resolve_existing_hub_dir,
    resolve_existing_ide_dir,
)


def uninstall_ide(
    ide_dir: Optional[str] = None,
    launcher_path: Optional[str] = None,
    scope: Optional[str] = None,
    dry_run: bool = False,
    force: bool = False,
) -> bool:
    """Uninstall the Antigravity IDE, associated desktop entries, icons, and launcher symlinks."""
    print_status("Checking Antigravity IDE installation for removal...")

    if not ide_dir or not launcher_path or not scope:
        detected_dir, detected_launcher, detected_scope = detect_preferred_ide(scope)
        ide_dir = ide_dir or detected_dir
        launcher_path = launcher_path or detected_launcher
        scope = scope or detected_scope

    resolved_ide_dir = resolve_existing_ide_dir(ide_dir)

    # Check active running processes
    running_pids = get_running_pids("antigravity-ide") or get_running_pids("Antigravity IDE")
    if running_pids and not force:
        print_warning(
            f"Antigravity IDE is currently running (PID: {', '.join(running_pids)}). "
            "Please close the IDE or run with --force to uninstall anyway."
        )
        return False

    targets_to_remove: list[str] = []

    # 1. Main Directory
    if resolved_ide_dir and os.path.exists(resolved_ide_dir):
        targets_to_remove.append(resolved_ide_dir)
        parent_dir = os.path.dirname(os.path.abspath(resolved_ide_dir))
        if os.path.basename(parent_dir) in ("antigravity-ide", "Antigravity-IDE") and parent_dir != resolved_ide_dir:
            targets_to_remove.append(parent_dir)

    # 2. Launcher Symlink
    if launcher_path and (os.path.islink(launcher_path) or os.path.exists(launcher_path)):
        targets_to_remove.append(launcher_path)

    # 3. Linux Desktop Entries, Icons, Nautilus Extensions
    if OS_NAME == "linux":
        if scope == "system":
            app_dirs = [SYSTEM_APPLICATIONS_DIR, USER_APPLICATIONS_DIR]
            icon_dirs = [SYSTEM_ICONS_DIR, USER_ICONS_DIR]
            nautilus_dirs = [SYSTEM_NAUTILUS_DIR, USER_NAUTILUS_DIR]
        else:
            app_dirs = [USER_APPLICATIONS_DIR]
            icon_dirs = [USER_ICONS_DIR]
            nautilus_dirs = [USER_NAUTILUS_DIR]

        for app_d in app_dirs:
            dt = os.path.join(app_d, "antigravity-ide.desktop")
            if os.path.exists(dt):
                targets_to_remove.append(dt)

        for icon_d in icon_dirs:
            icon = os.path.join(icon_d, "antigravity-ide.png")
            if os.path.exists(icon):
                targets_to_remove.append(icon)

        for naut_d in nautilus_dirs:
            ext = os.path.join(naut_d, "antigravity-nautilus.py")
            if os.path.exists(ext):
                targets_to_remove.append(ext)

    if not targets_to_remove:
        print_info("No Antigravity IDE installation files found to uninstall.")
        return True

    # Preflight write permissions
    for target in targets_to_remove:
        if not is_path_writable(target):
            print_error(
                f"Permission denied: Cannot remove '{target}'. "
                "To uninstall a system-wide installation, please run with sudo: sudo antigravity-updater --uninstall"
            )
            return False

    if dry_run:
        print_info("Dry Run: The following items would be removed:")
        for target in targets_to_remove:
            print_info(f"  - {target}")
        return True

    for target in targets_to_remove:
        try:
            if os.path.islink(target) or os.path.isfile(target):
                os.remove(target)
                print_status(f"Removed file: {target}")
            elif os.path.isdir(target):
                shutil.rmtree(target)
                print_status(f"Removed directory: {target}")
        except Exception as err:
            print_warning(f"Could not remove '{target}': {err}")

    if OS_NAME == "linux":
        refresh_linux_desktop_caches()

    print_success("Antigravity IDE successfully uninstalled!")
    return True


def uninstall_hub(
    hub_dir: Optional[str] = None,
    launcher_path: Optional[str] = None,
    scope: Optional[str] = None,
    dry_run: bool = False,
    force: bool = False,
) -> bool:
    """Uninstall the Antigravity Hub, associated desktop entries, icons, and launcher symlinks."""
    print_status("Checking Antigravity Hub installation for removal...")

    if not hub_dir or not launcher_path or not scope:
        detected_dir, detected_launcher, detected_scope = detect_preferred_hub(scope)
        hub_dir = hub_dir or detected_dir
        launcher_path = launcher_path or detected_launcher
        scope = scope or detected_scope

    resolved_hub_dir = resolve_existing_hub_dir(hub_dir)

    # Check active running processes
    running_pids = get_running_pids("antigravity")
    if running_pids and not force:
        print_warning(
            f"Antigravity Hub is currently running (PID: {', '.join(running_pids)}). "
            "Please close the application or run with --force to uninstall anyway."
        )
        return False

    targets_to_remove: list[str] = []

    # 1. Main Directory
    if resolved_hub_dir and os.path.exists(resolved_hub_dir):
        targets_to_remove.append(resolved_hub_dir)
        parent_dir = os.path.dirname(os.path.abspath(resolved_hub_dir))
        if os.path.basename(parent_dir) in ("antigravity", "Antigravity") and parent_dir != resolved_hub_dir:
            targets_to_remove.append(parent_dir)

    # 2. Launcher Symlink
    if launcher_path and (os.path.islink(launcher_path) or os.path.exists(launcher_path)):
        targets_to_remove.append(launcher_path)

    # 3. Linux Desktop Entries & Icons
    if OS_NAME == "linux":
        if scope == "system":
            app_dirs = [SYSTEM_APPLICATIONS_DIR, USER_APPLICATIONS_DIR]
            icon_dirs = [SYSTEM_ICONS_DIR, USER_ICONS_DIR]
        else:
            app_dirs = [USER_APPLICATIONS_DIR]
            icon_dirs = [USER_ICONS_DIR]

        for app_d in app_dirs:
            dt = os.path.join(app_d, "antigravity.desktop")
            if os.path.exists(dt):
                targets_to_remove.append(dt)

        for icon_d in icon_dirs:
            icon = os.path.join(icon_d, "antigravity.png")
            if os.path.exists(icon):
                targets_to_remove.append(icon)

    if not targets_to_remove:
        print_info("No Antigravity Hub installation files found to uninstall.")
        return True

    # Preflight write permissions
    for target in targets_to_remove:
        if not is_path_writable(target):
            print_error(
                f"Permission denied: Cannot remove '{target}'. "
                "To uninstall a system-wide installation, please run with sudo: sudo antigravity-updater --uninstall"
            )
            return False

    if dry_run:
        print_info("Dry Run: The following items would be removed:")
        for target in targets_to_remove:
            print_info(f"  - {target}")
        return True

    for target in targets_to_remove:
        try:
            if os.path.islink(target) or os.path.isfile(target):
                os.remove(target)
                print_status(f"Removed file: {target}")
            elif os.path.isdir(target):
                shutil.rmtree(target)
                print_status(f"Removed directory: {target}")
        except Exception as err:
            print_warning(f"Could not remove '{target}': {err}")

    if OS_NAME == "linux":
        refresh_linux_desktop_caches()

    print_success("Antigravity Hub successfully uninstalled!")
    return True


def uninstall_cli(
    cli_path: Optional[str] = None,
    scope: Optional[str] = None,
    dry_run: bool = False,
    force: bool = False,
) -> bool:
    """Uninstall the Antigravity CLI (agy) binary."""
    print_status("Checking Antigravity CLI installation for removal...")

    if not cli_path:
        detected_path, _ = detect_preferred_cli(scope)
        cli_path = detected_path

    if not cli_path or not (os.path.islink(cli_path) or os.path.exists(cli_path)):
        print_info("No Antigravity CLI binary found to uninstall.")
        return True

    # Preflight write permissions
    if not is_path_writable(cli_path):
        print_error(
            f"Permission denied: Cannot remove '{cli_path}'. "
            "To uninstall a system-wide binary, please run with sudo: sudo antigravity-updater --uninstall"
        )
        return False

    if dry_run:
        print_info(f"Dry Run: Would remove CLI binary: {cli_path}")
        return True

    try:
        os.remove(cli_path)
        print_status(f"Removed CLI binary: {cli_path}")
        print_success("Antigravity CLI successfully uninstalled!")
        return True
    except Exception as err:
        print_error(f"Failed to remove CLI binary '{cli_path}': {err}")
        return False
