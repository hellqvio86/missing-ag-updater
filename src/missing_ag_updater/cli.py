import argparse
import sys

from .config import resolve_config
from .const import (
    ARCH_NAME,
    COLOR_BOLD,
    COLOR_ENDC,
    COLOR_HEADER,
    OS_NAME,
    __version__,
)
from .discovery import (
    clean_duplicate_desktop_entries,
    diagnose_all,
)
from .uninstall import uninstall_cli, uninstall_hub, uninstall_ide
from .updater import update_cli, update_hub, update_ide
from .utils import (
    print_error,
    print_info,
    print_status,
    print_success,
    print_warning,
)


def run_diagnose() -> None:
    """Run diagnostics and print a human-readable report of installed Antigravity components."""
    data = diagnose_all()
    print(f"\n{COLOR_HEADER}{COLOR_BOLD}=== Antigravity System Diagnostics ==={COLOR_ENDC}\n")
    print(f"  Operating System: {COLOR_BOLD}{data['os']}{COLOR_ENDC}")

    print(f"\n{COLOR_BOLD}--- IDE Installations ---{COLOR_ENDC}")
    if not data["ide_installations"]:
        print_info("No IDE installations detected.")
    for inst in data["ide_installations"]:
        writable_str = "writable" if inst["is_writable"] else "read-only (requires sudo)"
        print_info(f"• Version: {COLOR_BOLD}{inst['version']}{COLOR_ENDC} [{inst['scope']}] ({writable_str})")
        print_info(f"    Path:     {inst['install_dir']}")
        if inst.get("launcher_path"):
            print_info(f"    Launcher: {inst['launcher_path']}")
        if inst.get("desktop_entry"):
            print_info(f"    Desktop:  {inst['desktop_entry']}")

    print(f"\n{COLOR_BOLD}--- Hub Installations ---{COLOR_ENDC}")
    if not data["hub_installations"]:
        print_info("No Hub installations detected.")
    for inst in data["hub_installations"]:
        writable_str = "writable" if inst["is_writable"] else "read-only (requires sudo)"
        print_info(f"• Version: {COLOR_BOLD}{inst['version']}{COLOR_ENDC} [{inst['scope']}] ({writable_str})")
        print_info(f"    Path:     {inst['install_dir']}")
        if inst.get("launcher_path"):
            print_info(f"    Launcher: {inst['launcher_path']}")
        if inst.get("desktop_entry"):
            print_info(f"    Desktop:  {inst['desktop_entry']}")

    print(f"\n{COLOR_BOLD}--- CLI Installations ---{COLOR_ENDC}")
    if not data["cli_installations"]:
        print_info("No CLI installations detected.")
    for inst in data["cli_installations"]:
        writable_str = "writable" if inst["is_writable"] else "read-only (requires sudo)"
        print_info(f"• Version: {COLOR_BOLD}{inst['version']}{COLOR_ENDC} [{inst['scope']}] ({writable_str})")
        print_info(f"    Path:     {inst['launcher_path']}")

    if data.get("desktop_files"):
        print(f"\n{COLOR_BOLD}--- Desktop Entries ---{COLOR_ENDC}")
        for dt in data["desktop_files"]:
            print_info(f"• [{dt['scope']}] {dt['component']}: {dt['path']}")
            if dt.get("exec"):
                print_info(f"    Exec: {dt['exec']}")

    running = data.get("running_processes", {})
    if running.get("ide_pids") or running.get("hub_pids"):
        print(f"\n{COLOR_BOLD}--- Running Processes ---{COLOR_ENDC}")
        if running.get("ide_pids"):
            print_warning(f"IDE PIDs: {', '.join(running['ide_pids'])}")
        if running.get("hub_pids"):
            print_warning(f"Hub PIDs: {', '.join(running['hub_pids'])}")

    sandbox = data.get("sandbox_status", {})
    if sandbox:
        print(f"\n{COLOR_BOLD}--- Sandbox / AppArmor ---{COLOR_ENDC}")
        print_info(f"Ubuntu-style Distro: {sandbox.get('distro_ubuntu_style', False)}")
        print_info(f"AppArmor Active:     {sandbox.get('apparmor_active', False)}")

    print()


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Auto-updater utility for Google Antigravity developer tools (Cross-Platform).",
        formatter_class=argparse.RawTextHelpFormatter,
    )
    parser.add_argument(
        "-v",
        "--version",
        action="version",
        version=f"%(prog)s {__version__}",
        help="Show program's version number and exit",
    )
    parser.add_argument(
        "--check",
        action="store_true",
        default=None,
        help="Check for available updates without installing",
    )
    parser.add_argument(
        "--ide",
        action="store_true",
        default=None,
        help="Update only the Antigravity IDE",
    )
    parser.add_argument(
        "--hub",
        action="store_true",
        default=None,
        help="Update only the Antigravity Hub",
    )
    parser.add_argument(
        "--cli",
        action="store_true",
        default=None,
        help="Update only the Antigravity CLI",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        default=None,
        help="Bypass version checks and active process warnings",
    )
    parser.add_argument(
        "--system",
        action="store_true",
        default=None,
        help="Target system-wide installation (/opt, /usr/local/bin) - requires root/sudo",
    )
    parser.add_argument(
        "--user",
        action="store_true",
        default=None,
        help="Target user-level installation (~/opt, ~/.local/bin)",
    )
    parser.add_argument(
        "--diagnose",
        "--diagnostic",
        "--diagnostics",
        "--doctor",
        action="store_true",
        default=False,
        help="Scan system and display all installed Antigravity components, versions, and desktop files",
    )
    parser.add_argument(
        "--clean-duplicates",
        action="store_true",
        default=False,
        help="Clean duplicate desktop entries and symlinks causing multiple app launcher icons",
    )
    parser.add_argument(
        "--uninstall",
        action="store_true",
        default=False,
        help="Uninstall specified Antigravity components (IDE, Hub, CLI, or all if none specified)",
    )
    parser.add_argument(
        "--remove-user-dirs",
        action="store_true",
        default=False,
        help="When cleaning duplicates with system keep scope, also remove ~/opt/Antigravity* directories",
    )
    parser.add_argument(
        "--dir-ide",
        type=str,
        default=None,
        help="Override path to Antigravity IDE folder/bundle",
    )
    parser.add_argument(
        "--dir-hub",
        type=str,
        default=None,
        help="Override path to Antigravity Hub folder/bundle",
    )
    parser.add_argument(
        "--path-cli",
        type=str,
        default=None,
        help="Override path to Antigravity CLI binary",
    )
    parser.add_argument(
        "--no-desktop",
        action="store_false",
        dest="install_desktop",
        default=None,
        help="Skip installing local .desktop files and application icons on Linux",
    )
    parser.add_argument(
        "--no-nautilus",
        action="store_false",
        dest="install_nautilus",
        default=None,
        help="Skip installing Nautilus context-menu integration on Linux",
    )
    parser.add_argument(
        "--apparmor-sandbox",
        action="store_true",
        default=None,
        help="Force SUID sandbox fix on chrome-sandbox (auto-detected by default on AppArmor systems)",
    )
    parser.add_argument(
        "--no-apparmor-sandbox",
        action="store_false",
        dest="apparmor_sandbox",
        help="Disable automatic SUID sandbox fix even if AppArmor is detected",
    )
    parser.add_argument(
        "--config",
        type=str,
        default=None,
        help="Path to TOML configuration file override",
    )

    args = parser.parse_args()

    if OS_NAME == "unknown":
        print_error("Unsupported operating system.")
        sys.exit(1)

    if args.diagnose:
        run_diagnose()
        sys.exit(0)

    if args.clean_duplicates:
        keep_scope = "system" if args.system or not args.user else "user"
        print_status(f"Cleaning duplicate Antigravity desktop entries and symlinks (keeping {keep_scope})...")
        removed = clean_duplicate_desktop_entries(keep_scope=keep_scope, remove_user_dirs=args.remove_user_dirs)
        if removed:
            for item in removed:
                print_success(f"Removed: {item}")
            print_success("Desktop entries cleaned up and caches refreshed.")
        else:
            print_info("No duplicate desktop entries or symlinks found.")
        sys.exit(0)

    # Resolve settings (CLI Args > Env > TOML > Detected / Default)
    try:
        cfg = resolve_config(args)
    except Exception as err:
        print_error(str(err))
        sys.exit(1)

    if args.uninstall:
        print(
            f"\n{COLOR_HEADER}{COLOR_BOLD}"
            "=== Unofficial Antigravity Applications Auto-Updater (missing-ag-updater) ==="
            f"{COLOR_ENDC}"
        )
        print_warning(
            "This project is a community tool and is NOT affiliated with, sponsored by, or supported by Google."
        )
        print_info(f"Uninstall Mode - Target Platform: {COLOR_BOLD}{OS_NAME} ({ARCH_NAME}){COLOR_ENDC}\n")

        success = True
        if cfg.ide or cfg.update_all:
            res = uninstall_ide(
                ide_dir=cfg.dir_ide if args.dir_ide else None,
                launcher_path=cfg.ide_launcher if args.dir_ide else None,
                scope=cfg.scope,
                dry_run=cfg.check,
                force=cfg.force,
            )
            success = success and res
            print()

        if cfg.hub or cfg.update_all:
            res = uninstall_hub(
                hub_dir=cfg.dir_hub if args.dir_hub else None,
                launcher_path=cfg.hub_launcher if args.dir_hub else None,
                scope=cfg.scope,
                dry_run=cfg.check,
                force=cfg.force,
            )
            success = success and res
            print()

        if cfg.cli or cfg.update_all:
            res = uninstall_cli(
                cli_path=cfg.path_cli if args.path_cli else None,
                scope=cfg.scope,
                dry_run=cfg.check,
                force=cfg.force,
            )
            success = success and res
            print()

        if success:
            print_success("Uninstallation completed successfully.")
            sys.exit(0)
        else:
            print_error("One or more uninstallation operations failed.")
            sys.exit(1)

    print(
        f"\n{COLOR_HEADER}{COLOR_BOLD}"
        "=== Unofficial Antigravity Applications Auto-Updater (missing-ag-updater) ==="
        f"{COLOR_ENDC}"
    )
    print_warning("This project is a community tool and is NOT affiliated with, sponsored by, or supported by Google.")
    print_info(f"Target Platform: {COLOR_BOLD}{OS_NAME} ({ARCH_NAME}){COLOR_ENDC}\n")

    success = True

    if cfg.ide or cfg.update_all:
        res = update_ide(
            cfg.dir_ide,
            cfg.ide_launcher,
            dry_run=cfg.check,
            force=cfg.force,
            install_desktop=cfg.install_desktop,
            install_nautilus=cfg.install_nautilus,
            suid_sandbox=cfg.apparmor_sandbox,
            scope=cfg.scope,
        )
        success = success and res
        print()

    if cfg.hub or cfg.update_all:
        res = update_hub(
            cfg.dir_hub,
            cfg.hub_launcher,
            dry_run=cfg.check,
            force=cfg.force,
            install_desktop=cfg.install_desktop,
            suid_sandbox=cfg.apparmor_sandbox,
            scope=cfg.scope,
        )
        success = success and res
        print()

    if cfg.cli or cfg.update_all:
        res = update_cli(cfg.path_cli, dry_run=cfg.check, force=cfg.force, scope=cfg.scope)
        success = success and res
        print()

    if success:
        print_success("Operation completed successfully.")
        sys.exit(0)
    else:
        print_error("One or more update operations failed.")
        sys.exit(1)
