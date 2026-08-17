"""Discovery, environment diagnostics, and duplicate desktop entry cleanup."""

import os
import shutil
from dataclasses import asdict, dataclass
from typing import Any, Optional

from .const import (
    HOME,
    OS_NAME,
    SYSTEM_APPLICATIONS_DIR,
    SYSTEM_CLI_BINARY,
    SYSTEM_HUB_DIR,
    SYSTEM_HUB_LAUNCHER,
    SYSTEM_IDE_DIR,
    SYSTEM_IDE_LAUNCHER,
    USER_APPLICATIONS_DIR,
    USER_BIN_DIR,
    USER_CLI_BINARY,
    USER_HUB_DIR,
    USER_HUB_LAUNCHER,
    USER_ICONS_DIR,
    USER_IDE_DIR,
    USER_IDE_LAUNCHER,
    USER_OPT_DIR,
)
from .utils import (
    get_cli_version,
    get_hub_version,
    get_ide_version,
    get_running_pids,
    is_apparmor_enabled,
    is_path_writable,
    is_ubuntu_sandbox_distro,
    refresh_linux_desktop_caches,
    resolve_existing_hub_dir,
    resolve_existing_ide_dir,
)


@dataclass
class InstallationInfo:
    """Information about a detected Antigravity component installation."""

    component: str  # 'ide', 'hub', or 'cli'
    install_dir: str
    launcher_path: Optional[str]
    version: str
    scope: str  # 'system', 'user', or 'custom'
    is_writable: bool
    desktop_entry: Optional[str] = None
    icon_path: Optional[str] = None
    is_active_path: bool = False

    def to_dict(self) -> dict[str, Any]:
        """Convert installation info dataclass to dictionary."""
        return asdict(self)


def _is_system_path(path: str) -> bool:
    """Check if a path is in a system-wide directory (/opt, /usr, /Applications, %PROGRAMFILES%)."""
    if not path:
        return False
    norm = os.path.normpath(path)
    if OS_NAME == "linux":
        return norm.startswith("/opt") or norm.startswith("/usr") or norm.startswith("/etc")
    if OS_NAME == "darwin":
        return norm.startswith("/Applications") or norm.startswith("/Library") or norm.startswith("/usr")
    if OS_NAME == "windows":
        prog_files = os.environ.get("ProgramFiles", "C:\\Program Files")
        return norm.lower().startswith(prog_files.lower())
    return False


def _find_exec_from_desktop(desktop_path: str) -> Optional[str]:
    """Parse Exec line from a .desktop file and return the command path."""
    if not os.path.exists(desktop_path):
        return None
    try:
        with open(desktop_path, "r", encoding="utf-8") as fdesc:
            for line in fdesc:
                line = line.strip()
                if line.startswith("Exec="):
                    exec_cmd = line.split("=", 1)[1].strip()
                    parts = exec_cmd.split()
                    if parts:
                        return parts[0]
    except OSError:
        pass
    return None


def _find_binaries_in_path(binary_name: str) -> list[str]:
    """Find all instances of binary_name in system PATH (deduplicated)."""
    found: list[str] = []
    seen: set[str] = set()
    path_env = os.environ.get("PATH", "")
    for directory in path_env.split(os.pathsep):
        if not directory:
            continue
        candidate = os.path.join(directory, binary_name)
        if os.path.isfile(candidate) or os.path.islink(candidate):
            real_cand = os.path.realpath(candidate)
            if real_cand not in seen and os.path.exists(candidate):
                seen.add(real_cand)
                found.append(candidate)
    return found


def find_all_ide_installations() -> list[InstallationInfo]:
    """Scan the system and return all detected Antigravity IDE installations."""
    results: list[InstallationInfo] = []
    seen_dirs: set[str] = set()

    candidate_dirs: list[tuple[str, str, Optional[str]]] = []  # (dir, scope, launcher)

    if OS_NAME == "linux":
        # Candidate directories
        candidate_dirs.extend(
            [
                (SYSTEM_IDE_DIR, "system", SYSTEM_IDE_LAUNCHER),
                ("/opt/antigravity-ide/Antigravity-IDE", "system", SYSTEM_IDE_LAUNCHER),
                ("/opt/Antigravity-IDE", "system", SYSTEM_IDE_LAUNCHER),
                ("/opt/Antigravity IDE", "system", SYSTEM_IDE_LAUNCHER),
                ("/usr/lib/antigravity-ide", "system", SYSTEM_IDE_LAUNCHER),
                ("/usr/share/antigravity-ide", "system", SYSTEM_IDE_LAUNCHER),
                (USER_IDE_DIR, "user", USER_IDE_LAUNCHER),
                (
                    os.path.join(USER_OPT_DIR, "Antigravity-IDE"),
                    "user",
                    USER_IDE_LAUNCHER,
                ),
                (
                    os.path.join(USER_OPT_DIR, "Antigravity IDE"),
                    "user",
                    USER_IDE_LAUNCHER,
                ),
                (
                    os.path.join(HOME, ".local", "share", "antigravity-ide"),
                    "user",
                    USER_IDE_LAUNCHER,
                ),
            ]
        )

        # Check binaries in PATH
        for bin_path in _find_binaries_in_path("antigravity-ide"):
            real_bin = os.path.realpath(bin_path)
            # Binary might be in ide_dir/bin/antigravity-ide or ide_dir/antigravity-ide
            parent1 = os.path.dirname(real_bin)
            parent2 = os.path.dirname(parent1)
            cand_dir = parent2 if os.path.basename(parent1) == "bin" else parent1
            scope = "system" if _is_system_path(cand_dir) else "user"
            candidate_dirs.append((cand_dir, scope, bin_path))

        # Check desktop files
        desktop_candidates = [
            (
                os.path.join(SYSTEM_APPLICATIONS_DIR, "antigravity-ide.desktop"),
                "system",
            ),
            (os.path.join(USER_APPLICATIONS_DIR, "antigravity-ide.desktop"), "user"),
        ]
        for dt_path, dt_scope in desktop_candidates:
            exec_bin = _find_exec_from_desktop(dt_path)
            if exec_bin and os.path.exists(exec_bin):
                real_bin = os.path.realpath(exec_bin)
                parent1 = os.path.dirname(real_bin)
                parent2 = os.path.dirname(parent1)
                cand_dir = parent2 if os.path.basename(parent1) == "bin" else parent1
                candidate_dirs.append((cand_dir, dt_scope, exec_bin))

    elif OS_NAME == "darwin":
        candidate_dirs.extend(
            [
                (SYSTEM_IDE_DIR, "system", SYSTEM_IDE_LAUNCHER),
                (USER_IDE_DIR, "user", USER_IDE_LAUNCHER),
            ]
        )

    elif OS_NAME == "windows":
        candidate_dirs.extend(
            [
                (USER_IDE_DIR, "user", None),
                (SYSTEM_IDE_DIR, "system", None),
            ]
        )

    # Process all candidates and deduplicate
    for cand_dir, cand_scope, cand_launcher in candidate_dirs:
        resolved = resolve_existing_ide_dir(cand_dir)
        norm_resolved = os.path.normpath(resolved)
        if norm_resolved in seen_dirs:
            continue

        ver = get_ide_version(resolved)
        if ver != "0.0.0":
            seen_dirs.add(norm_resolved)
            scope = "system" if _is_system_path(resolved) else cand_scope

            dt_file = None
            if OS_NAME == "linux":
                dt_user = os.path.join(USER_APPLICATIONS_DIR, "antigravity-ide.desktop")
                dt_sys = os.path.join(SYSTEM_APPLICATIONS_DIR, "antigravity-ide.desktop")
                if scope == "user" and os.path.exists(dt_user):
                    dt_file = dt_user
                elif os.path.exists(dt_sys):
                    dt_file = dt_sys

            writable = is_path_writable(resolved)
            results.append(
                InstallationInfo(
                    component="ide",
                    install_dir=resolved,
                    launcher_path=cand_launcher,
                    version=ver,
                    scope=scope,
                    is_writable=writable,
                    desktop_entry=dt_file,
                )
            )

    return results


def find_all_hub_installations() -> list[InstallationInfo]:
    """Scan the system and return all detected Antigravity Hub installations."""
    results: list[InstallationInfo] = []
    seen_dirs: set[str] = set()

    candidate_dirs: list[tuple[str, str, Optional[str]]] = []

    if OS_NAME == "linux":
        candidate_dirs.extend(
            [
                (SYSTEM_HUB_DIR, "system", SYSTEM_HUB_LAUNCHER),
                ("/opt/antigravity/Antigravity-x64", "system", SYSTEM_HUB_LAUNCHER),
                ("/opt/Antigravity-x64", "system", SYSTEM_HUB_LAUNCHER),
                ("/opt/Antigravity Hub", "system", SYSTEM_HUB_LAUNCHER),
                ("/usr/lib/antigravity", "system", SYSTEM_HUB_LAUNCHER),
                (USER_HUB_DIR, "user", USER_HUB_LAUNCHER),
                (
                    os.path.join(USER_OPT_DIR, "Antigravity-x64"),
                    "user",
                    USER_HUB_LAUNCHER,
                ),
                (
                    os.path.join(USER_OPT_DIR, "Antigravity Hub"),
                    "user",
                    USER_HUB_LAUNCHER,
                ),
                (
                    os.path.join(HOME, ".local", "share", "antigravity"),
                    "user",
                    USER_HUB_LAUNCHER,
                ),
            ]
        )

        for bin_path in _find_binaries_in_path("antigravity"):
            real_bin = os.path.realpath(bin_path)
            parent1 = os.path.dirname(real_bin)
            scope = "system" if _is_system_path(parent1) else "user"
            candidate_dirs.append((parent1, scope, bin_path))

        desktop_candidates = [
            (os.path.join(SYSTEM_APPLICATIONS_DIR, "antigravity.desktop"), "system"),
            (os.path.join(USER_APPLICATIONS_DIR, "antigravity.desktop"), "user"),
        ]
        for dt_path, dt_scope in desktop_candidates:
            exec_bin = _find_exec_from_desktop(dt_path)
            if exec_bin and os.path.exists(exec_bin):
                real_bin = os.path.realpath(exec_bin)
                parent1 = os.path.dirname(real_bin)
                candidate_dirs.append((parent1, dt_scope, exec_bin))

    elif OS_NAME == "darwin":
        candidate_dirs.extend(
            [
                (SYSTEM_HUB_DIR, "system", SYSTEM_HUB_LAUNCHER),
                (USER_HUB_DIR, "user", USER_HUB_LAUNCHER),
            ]
        )

    elif OS_NAME == "windows":
        candidate_dirs.extend(
            [
                (USER_HUB_DIR, "user", None),
                (SYSTEM_HUB_DIR, "system", None),
            ]
        )

    for cand_dir, cand_scope, cand_launcher in candidate_dirs:
        resolved = resolve_existing_hub_dir(cand_dir)
        norm_resolved = os.path.normpath(resolved)
        if norm_resolved in seen_dirs:
            continue

        ver = get_hub_version(resolved)
        if ver != "0.0.0":
            seen_dirs.add(norm_resolved)
            scope = "system" if _is_system_path(resolved) else cand_scope

            dt_file = None
            if OS_NAME == "linux":
                dt_user = os.path.join(USER_APPLICATIONS_DIR, "antigravity.desktop")
                dt_sys = os.path.join(SYSTEM_APPLICATIONS_DIR, "antigravity.desktop")
                if scope == "user" and os.path.exists(dt_user):
                    dt_file = dt_user
                elif os.path.exists(dt_sys):
                    dt_file = dt_sys

            writable = is_path_writable(resolved)
            results.append(
                InstallationInfo(
                    component="hub",
                    install_dir=resolved,
                    launcher_path=cand_launcher,
                    version=ver,
                    scope=scope,
                    is_writable=writable,
                    desktop_entry=dt_file,
                )
            )

    return results


def find_all_cli_installations() -> list[InstallationInfo]:
    """Scan the system and return all detected Antigravity CLI installations."""
    results: list[InstallationInfo] = []
    seen_bins: set[str] = set()

    candidate_bins: list[tuple[str, str]] = []

    if OS_NAME == "linux":
        candidate_bins.extend(
            [
                (SYSTEM_CLI_BINARY, "system"),
                ("/usr/bin/agy", "system"),
                (USER_CLI_BINARY, "user"),
                (os.path.join(HOME, ".antigravity", "bin", "agy"), "user"),
            ]
        )
        for b in _find_binaries_in_path("agy"):
            scope = "system" if _is_system_path(b) else "user"
            candidate_bins.append((b, scope))

    elif OS_NAME == "darwin":
        candidate_bins.extend(
            [
                (SYSTEM_CLI_BINARY, "system"),
                (USER_CLI_BINARY, "user"),
            ]
        )
        for b in _find_binaries_in_path("agy"):
            scope = "system" if _is_system_path(b) else "user"
            candidate_bins.append((b, scope))

    elif OS_NAME == "windows":
        candidate_bins.extend(
            [
                (USER_CLI_BINARY, "user"),
                (SYSTEM_CLI_BINARY, "system"),
            ]
        )

    for cand_bin, cand_scope in candidate_bins:
        norm_bin = os.path.normpath(cand_bin)
        if norm_bin in seen_bins:
            continue

        ver = get_cli_version(cand_bin)
        if ver != "0.0.0":
            seen_bins.add(norm_bin)
            scope = "system" if _is_system_path(cand_bin) else cand_scope
            writable = is_path_writable(cand_bin)
            results.append(
                InstallationInfo(
                    component="cli",
                    install_dir=os.path.dirname(cand_bin),
                    launcher_path=cand_bin,
                    version=ver,
                    scope=scope,
                    is_writable=writable,
                )
            )

    return results


def detect_preferred_ide(scope: Optional[str] = None) -> tuple[str, Optional[str], str]:
    """Detect the preferred Antigravity IDE directory, launcher, and scope ('system' or 'user')."""
    is_root = hasattr(os, "geteuid") and os.geteuid() == 0
    all_installs = find_all_ide_installations()

    if scope == "system":
        for inst in all_installs:
            if inst.scope == "system":
                return (
                    inst.install_dir,
                    inst.launcher_path or SYSTEM_IDE_LAUNCHER,
                    "system",
                )
        return SYSTEM_IDE_DIR, SYSTEM_IDE_LAUNCHER, "system"

    if scope == "user":
        for inst in all_installs:
            if inst.scope == "user":
                return inst.install_dir, inst.launcher_path or USER_IDE_LAUNCHER, "user"
        return USER_IDE_DIR, USER_IDE_LAUNCHER, "user"

    # Auto-detection
    if is_root:
        for inst in all_installs:
            if inst.scope == "system":
                return (
                    inst.install_dir,
                    inst.launcher_path or SYSTEM_IDE_LAUNCHER,
                    "system",
                )
        return SYSTEM_IDE_DIR, SYSTEM_IDE_LAUNCHER, "system"

    # If non-root: if an active user install exists, prefer that
    user_inst = next((i for i in all_installs if i.scope == "user"), None)
    if user_inst:
        return (
            user_inst.install_dir,
            user_inst.launcher_path or USER_IDE_LAUNCHER,
            "user",
        )

    # If only system install exists
    sys_inst = next((i for i in all_installs if i.scope == "system"), None)
    if sys_inst:
        return (
            sys_inst.install_dir,
            sys_inst.launcher_path or SYSTEM_IDE_LAUNCHER,
            "system",
        )

    # Default fallback
    return USER_IDE_DIR, USER_IDE_LAUNCHER, "user"


def detect_preferred_hub(scope: Optional[str] = None) -> tuple[str, Optional[str], str]:
    """Detect the preferred Antigravity Hub directory, launcher, and scope ('system' or 'user')."""
    is_root = hasattr(os, "geteuid") and os.geteuid() == 0
    all_installs = find_all_hub_installations()

    if scope == "system":
        for inst in all_installs:
            if inst.scope == "system":
                return (
                    inst.install_dir,
                    inst.launcher_path or SYSTEM_HUB_LAUNCHER,
                    "system",
                )
        return SYSTEM_HUB_DIR, SYSTEM_HUB_LAUNCHER, "system"

    if scope == "user":
        for inst in all_installs:
            if inst.scope == "user":
                return inst.install_dir, inst.launcher_path or USER_HUB_LAUNCHER, "user"
        return USER_HUB_DIR, USER_HUB_LAUNCHER, "user"

    if is_root:
        for inst in all_installs:
            if inst.scope == "system":
                return (
                    inst.install_dir,
                    inst.launcher_path or SYSTEM_HUB_LAUNCHER,
                    "system",
                )
        return SYSTEM_HUB_DIR, SYSTEM_HUB_LAUNCHER, "system"

    user_inst = next((i for i in all_installs if i.scope == "user"), None)
    if user_inst:
        return (
            user_inst.install_dir,
            user_inst.launcher_path or USER_HUB_LAUNCHER,
            "user",
        )

    sys_inst = next((i for i in all_installs if i.scope == "system"), None)
    if sys_inst:
        return (
            sys_inst.install_dir,
            sys_inst.launcher_path or SYSTEM_HUB_LAUNCHER,
            "system",
        )

    return USER_HUB_DIR, USER_HUB_LAUNCHER, "user"


def detect_preferred_cli(scope: Optional[str] = None) -> tuple[str, str]:
    """Detect the preferred Antigravity CLI binary path and scope ('system' or 'user')."""
    is_root = hasattr(os, "geteuid") and os.geteuid() == 0
    all_installs = find_all_cli_installations()

    if scope == "system":
        for inst in all_installs:
            if inst.scope == "system" and inst.launcher_path:
                return inst.launcher_path, "system"
        return SYSTEM_CLI_BINARY, "system"

    if scope == "user":
        for inst in all_installs:
            if inst.scope == "user" and inst.launcher_path:
                return inst.launcher_path, "user"
        return USER_CLI_BINARY, "user"

    if is_root:
        for inst in all_installs:
            if inst.scope == "system" and inst.launcher_path:
                return inst.launcher_path, "system"
        return SYSTEM_CLI_BINARY, "system"

    user_inst = next((i for i in all_installs if i.scope == "user" and i.launcher_path), None)
    if user_inst and user_inst.launcher_path:
        return user_inst.launcher_path, "user"

    sys_inst = next((i for i in all_installs if i.scope == "system" and i.launcher_path), None)
    if sys_inst and sys_inst.launcher_path:
        return sys_inst.launcher_path, "system"

    return USER_CLI_BINARY, "user"


def diagnose_all() -> dict[str, Any]:
    """Run full diagnostics on Antigravity installations across the current machine."""
    ide_installs = find_all_ide_installations()
    hub_installs = find_all_hub_installations()
    cli_installs = find_all_cli_installations()

    running_ide = get_running_pids("antigravity-ide") or get_running_pids("Antigravity IDE")
    running_hub = get_running_pids("antigravity")

    # Check desktop files
    desktop_files: list[dict[str, Any]] = []
    if OS_NAME == "linux":
        dt_paths = [
            (
                os.path.join(SYSTEM_APPLICATIONS_DIR, "antigravity-ide.desktop"),
                "system",
                "IDE",
            ),
            (
                os.path.join(SYSTEM_APPLICATIONS_DIR, "antigravity.desktop"),
                "system",
                "Hub",
            ),
            (
                os.path.join(USER_APPLICATIONS_DIR, "antigravity-ide.desktop"),
                "user",
                "IDE",
            ),
            (os.path.join(USER_APPLICATIONS_DIR, "antigravity.desktop"), "user", "Hub"),
        ]
        for p, scope, comp in dt_paths:
            if os.path.exists(p):
                desktop_files.append(
                    {
                        "path": p,
                        "scope": scope,
                        "component": comp,
                        "exec": _find_exec_from_desktop(p),
                    }
                )

    # Sandbox status on Linux
    sandbox_status = {}
    if OS_NAME == "linux":
        sandbox_status = {
            "distro_ubuntu_style": is_ubuntu_sandbox_distro(),
            "apparmor_active": is_apparmor_enabled(),
        }

    return {
        "os": OS_NAME,
        "ide_installations": [i.to_dict() for i in ide_installs],
        "hub_installations": [i.to_dict() for i in hub_installs],
        "cli_installations": [i.to_dict() for i in cli_installs],
        "running_processes": {
            "ide_pids": running_ide,
            "hub_pids": running_hub,
        },
        "desktop_files": desktop_files,
        "sandbox_status": sandbox_status,
    }


def clean_duplicate_desktop_entries(
    keep_scope: str = "system",
    remove_user_dirs: bool = False,
    dry_run: bool = False,
) -> list[str]:
    """Clean duplicate or conflicting desktop entries and local files.

    If keep_scope == 'system':
      Removes duplicate user-level desktop files
      (~/.local/share/applications/antigravity*.desktop), user-level symlinks
      (~/.local/bin/antigravity*), and optionally user-level install directories.
    If keep_scope == 'user':
      Removes user-level duplicates if redundant or cleans orphaned files.
    """
    removed_items: list[str] = []

    if OS_NAME != "linux":
        return removed_items

    if keep_scope == "system":
        # Check user desktop entries
        user_dt_ide = os.path.join(USER_APPLICATIONS_DIR, "antigravity-ide.desktop")
        user_dt_hub = os.path.join(USER_APPLICATIONS_DIR, "antigravity.desktop")

        for dt in [user_dt_ide, user_dt_hub]:
            if os.path.exists(dt):
                if not dry_run:
                    os.remove(dt)
                removed_items.append(dt)

        # Check user symlinks in ~/.local/bin
        user_symlink_ide = os.path.join(USER_BIN_DIR, "antigravity-ide")
        user_symlink_hub = os.path.join(USER_BIN_DIR, "antigravity")
        for sym in [user_symlink_ide, user_symlink_hub]:
            if os.path.islink(sym) or os.path.exists(sym):
                if not dry_run:
                    os.remove(sym)
                removed_items.append(sym)

        # User icons
        user_icon_ide = os.path.join(USER_ICONS_DIR, "antigravity-ide.png")
        user_icon_hub = os.path.join(USER_ICONS_DIR, "antigravity.png")
        for icon in [user_icon_ide, user_icon_hub]:
            if os.path.exists(icon):
                if not dry_run:
                    os.remove(icon)
                removed_items.append(icon)

        # User install directories in ~/opt and ~/.local/share
        if remove_user_dirs:
            user_dirs = [
                os.path.join(USER_OPT_DIR, "Antigravity-IDE"),
                os.path.join(USER_OPT_DIR, "Antigravity IDE"),
                os.path.join(USER_OPT_DIR, "Antigravity-x64"),
                os.path.join(USER_OPT_DIR, "Antigravity Hub"),
                os.path.join(HOME, ".local", "share", "antigravity-ide"),
                os.path.join(HOME, ".local", "share", "antigravity"),
            ]
            for udir in user_dirs:
                if os.path.exists(udir):
                    if not dry_run:
                        shutil.rmtree(udir)
                    removed_items.append(udir)

        if not dry_run:
            refresh_linux_desktop_caches()

    return removed_items
