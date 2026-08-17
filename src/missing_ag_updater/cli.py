import argparse
import os
import sys

from .config import get_default_config_path, load_toml_config
from .const import (
    ARCH_NAME,
    COLOR_BOLD,
    COLOR_ENDC,
    COLOR_HEADER,
    DEFAULT_HUB_LAUNCHER,
    DEFAULT_IDE_LAUNCHER,
    OS_NAME,
)
from .discovery import (
    clean_duplicate_desktop_entries,
    detect_preferred_cli,
    detect_preferred_hub,
    detect_preferred_ide,
    diagnose_all,
)
from .uninstall import uninstall_cli, uninstall_hub, uninstall_ide
from .updater import update_cli, update_hub, update_ide
from .utils import (
    is_apparmor_enabled,
    print_error,
    print_info,
    print_status,
    print_success,
    print_warning,
)


def get_env_bool(names: list[str], default: bool) -> bool:
    """Check a list of environment variable names for a boolean value."""
    for name in names:
        val = os.environ.get(name)
        if val is not None:
            return val.lower() in ("1", "true", "yes", "on")
    return default


def get_env_str(names: list[str], default: str) -> str:
    """Check a list of environment variable names for a string value."""
    for name in names:
        val = os.environ.get(name)
        if val is not None:
            return val
    return default


def run_diagnose() -> None:
    """Run diagnostics and print a human-readable report of installed Antigravity components."""
    data = diagnose_all()
    print(f"\n{COLOR_HEADER}{COLOR_BOLD}=== Antigravity System Diagnostics ==={COLOR_ENDC}\n")
    print(f"  Operating System: {COLOR_BOLD}{data['os']}{COLOR_ENDC}")

    print(f"\n{COLOR_BOLD}--- IDE Installations ---{COLOR_ENDC}")
    if not data["ide_installations"]:
        print_info("No IDE installations detected.")
    for i in data["ide_installations"]:
        writable_str = "writable" if i["is_writable"] else "read-only (requires sudo)"
        print_info(f"• Version: {COLOR_BOLD}{i['version']}{COLOR_ENDC} [{i['scope']}] ({writable_str})")
        print_info(f"    Path:     {i['install_dir']}")
        if i.get("launcher_path"):
            print_info(f"    Launcher: {i['launcher_path']}")
        if i.get("desktop_entry"):
            print_info(f"    Desktop:  {i['desktop_entry']}")

    print(f"\n{COLOR_BOLD}--- Hub Installations ---{COLOR_ENDC}")
    if not data["hub_installations"]:
        print_info("No Hub installations detected.")
    for i in data["hub_installations"]:
        writable_str = "writable" if i["is_writable"] else "read-only (requires sudo)"
        print_info(f"• Version: {COLOR_BOLD}{i['version']}{COLOR_ENDC} [{i['scope']}] ({writable_str})")
        print_info(f"    Path:     {i['install_dir']}")
        if i.get("launcher_path"):
            print_info(f"    Launcher: {i['launcher_path']}")
        if i.get("desktop_entry"):
            print_info(f"    Desktop:  {i['desktop_entry']}")

    print(f"\n{COLOR_BOLD}--- CLI Installations ---{COLOR_ENDC}")
    if not data["cli_installations"]:
        print_info("No CLI installations detected.")
    for i in data["cli_installations"]:
        writable_str = "writable" if i["is_writable"] else "read-only (requires sudo)"
        print_info(f"• Version: {COLOR_BOLD}{i['version']}{COLOR_ENDC} [{i['scope']}] ({writable_str})")
        print_info(f"    Path:     {i['launcher_path']}")

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

    # 1. Resolve configuration path: CLI arg > Env Variable > Default Path
    config_path = args.config
    explicit_config = True
    if not config_path:
        config_path = os.environ.get("ANTIGRAVITY_CONFIG") or os.environ.get("AG_CONFIG")
        if config_path:
            explicit_config = True
        else:
            config_path = get_default_config_path()
            explicit_config = False

    # 2. Load TOML configuration if exists
    try:
        config_dict = load_toml_config(config_path, explicit=explicit_config)
    except Exception as err:
        print_error(str(err))
        sys.exit(1)

    # 3. Settings Resolution Helpers
    def resolve_bool(cli_val: bool | None, env_names: list[str], toml_key: str, default_val: bool) -> bool:
        if cli_val is not None:
            return cli_val
        for name in env_names:
            val = os.environ.get(name)
            if val is not None:
                return val.lower() in ("1", "true", "yes", "on")
        toml_val = config_dict.get(toml_key)
        if toml_val is not None:
            if isinstance(toml_val, bool):
                return toml_val
            if isinstance(toml_val, str):
                return toml_val.lower() in ("1", "true", "yes", "on")
        return default_val

    def resolve_str(cli_val: str | None, env_names: list[str], toml_key: str, default_val: str) -> str:
        if cli_val is not None:
            return cli_val
        for name in env_names:
            val = os.environ.get(name)
            if val is not None:
                return val
        toml_val = config_dict.get(toml_key)
        if toml_val is not None:
            return str(toml_val)
        return default_val

    # Scope resolution
    is_system = resolve_bool(args.system, ["ANTIGRAVITY_SYSTEM", "AG_SYSTEM"], "system", False)
    is_user = resolve_bool(args.user, ["ANTIGRAVITY_USER", "AG_USER"], "user", False)
    scope: str | None = "system" if is_system else ("user" if is_user else None)

    # Auto-detect preferred locations based on scope
    detected_ide_dir, detected_ide_launcher, _ = detect_preferred_ide(scope=scope)
    detected_hub_dir, detected_hub_launcher, _ = detect_preferred_hub(scope=scope)
    detected_cli_binary, _ = detect_preferred_cli(scope=scope)

    # Resolve settings (CLI > Env > TOML > Detected / Default)
    check = resolve_bool(args.check, ["ANTIGRAVITY_CHECK", "AG_CHECK"], "check", False)
    ide = resolve_bool(args.ide, ["ANTIGRAVITY_IDE", "AG_IDE"], "ide", False)
    hub = resolve_bool(args.hub, ["ANTIGRAVITY_HUB", "AG_HUB"], "hub", False)
    cli = resolve_bool(args.cli, ["ANTIGRAVITY_CLI", "AG_CLI"], "cli", False)
    force = resolve_bool(args.force, ["ANTIGRAVITY_FORCE", "AG_FORCE"], "force", False)
    # AppArmor sandbox: CLI flag > env var > TOML config > auto-detect
    if args.apparmor_sandbox is not None:
        # Explicit CLI flag (--apparmor-sandbox or --no-apparmor-sandbox)
        apparmor_sandbox: bool = args.apparmor_sandbox
    else:
        # Check environment variables
        sandbox_env = None
        for name in ["ANTIGRAVITY_APPARMOR_SANDBOX", "AG_APPARMOR_SANDBOX"]:
            val = os.environ.get(name)
            if val is not None:
                sandbox_env = val.lower() in ("1", "true", "yes", "on")
                break

        if sandbox_env is not None:
            apparmor_sandbox = sandbox_env
        else:
            # Check TOML config
            toml_val = config_dict.get("apparmor_sandbox")
            if toml_val is not None:
                if isinstance(toml_val, bool):
                    apparmor_sandbox = toml_val
                else:
                    apparmor_sandbox = str(toml_val).lower() in (
                        "1",
                        "true",
                        "yes",
                        "on",
                    )
            else:
                # Auto-detect: enable on Linux when AppArmor is active
                apparmor_sandbox = OS_NAME == "linux" and is_apparmor_enabled()

    dir_ide = resolve_str(args.dir_ide, ["ANTIGRAVITY_DIR_IDE", "AG_DIR_IDE"], "dir_ide", detected_ide_dir)
    dir_hub = resolve_str(args.dir_hub, ["ANTIGRAVITY_DIR_HUB", "AG_DIR_HUB"], "dir_hub", detected_hub_dir)
    path_cli = resolve_str(
        args.path_cli,
        ["ANTIGRAVITY_PATH_CLI", "AG_PATH_CLI"],
        "path_cli",
        detected_cli_binary,
    )

    ide_launcher = (
        detected_ide_launcher
        if args.dir_ide is None
        else (DEFAULT_IDE_LAUNCHER if scope != "system" else detected_ide_launcher)
    )
    hub_launcher = (
        detected_hub_launcher
        if args.dir_hub is None
        else (DEFAULT_HUB_LAUNCHER if scope != "system" else detected_hub_launcher)
    )

    # Resolve install_desktop (with NO_DESKTOP checks)
    if args.install_desktop is not None:
        install_desktop = args.install_desktop
    else:
        if get_env_bool(["ANTIGRAVITY_NO_DESKTOP", "AG_NO_DESKTOP"], False):
            install_desktop = False
        else:
            desktop_env = None
            for name in ["ANTIGRAVITY_DESKTOP", "AG_DESKTOP"]:
                val = os.environ.get(name)
                if val is not None:
                    desktop_env = val.lower() in ("1", "true", "yes", "on")
                    break

            if desktop_env is not None:
                install_desktop = desktop_env
            else:
                toml_desktop = config_dict.get("desktop")
                toml_no_desktop = config_dict.get("no_desktop")
                if toml_desktop is not None:
                    if isinstance(toml_desktop, bool):
                        install_desktop = toml_desktop
                    else:
                        install_desktop = str(toml_desktop).lower() in (
                            "1",
                            "true",
                            "yes",
                            "on",
                        )
                elif toml_no_desktop is not None:
                    if isinstance(toml_no_desktop, bool):
                        install_desktop = not toml_no_desktop
                    else:
                        install_desktop = str(toml_no_desktop).lower() not in (
                            "1",
                            "true",
                            "yes",
                            "on",
                        )
                else:
                    install_desktop = True

    # Resolve install_nautilus (with NO_NAUTILUS checks)
    if args.install_nautilus is not None:
        install_nautilus = args.install_nautilus
    else:
        if get_env_bool(["ANTIGRAVITY_NO_NAUTILUS", "AG_NO_NAUTILUS"], False):
            install_nautilus = False
        else:
            nautilus_env = None
            for name in ["ANTIGRAVITY_NAUTILUS", "AG_NAUTILUS"]:
                val = os.environ.get(name)
                if val is not None:
                    nautilus_env = val.lower() in ("1", "true", "yes", "on")
                    break

            if nautilus_env is not None:
                install_nautilus = nautilus_env
            else:
                toml_nautilus = config_dict.get("nautilus")
                toml_no_nautilus = config_dict.get("no_nautilus")
                if toml_nautilus is not None:
                    if isinstance(toml_nautilus, bool):
                        install_nautilus = toml_nautilus
                    else:
                        install_nautilus = str(toml_nautilus).lower() in (
                            "1",
                            "true",
                            "yes",
                            "on",
                        )
                elif toml_no_nautilus is not None:
                    if isinstance(toml_no_nautilus, bool):
                        install_nautilus = not toml_no_nautilus
                    else:
                        install_nautilus = str(toml_no_nautilus).lower() not in (
                            "1",
                            "true",
                            "yes",
                            "on",
                        )
                else:
                    install_nautilus = True

    # If no specific component is selected, default to all components
    update_all = not (ide or hub or cli)

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
        if ide or update_all:
            res = uninstall_ide(
                ide_dir=dir_ide if args.dir_ide else None,
                launcher_path=ide_launcher if args.dir_ide else None,
                scope=scope,
                dry_run=check,
                force=force,
            )
            success = success and res
            print()

        if hub or update_all:
            res = uninstall_hub(
                hub_dir=dir_hub if args.dir_hub else None,
                launcher_path=hub_launcher if args.dir_hub else None,
                scope=scope,
                dry_run=check,
                force=force,
            )
            success = success and res
            print()

        if cli or update_all:
            res = uninstall_cli(
                cli_path=path_cli if args.path_cli else None,
                scope=scope,
                dry_run=check,
                force=force,
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

    if ide or update_all:
        res = update_ide(
            dir_ide,
            ide_launcher,
            dry_run=check,
            force=force,
            install_desktop=install_desktop,
            install_nautilus=install_nautilus,
            suid_sandbox=apparmor_sandbox,
            scope=scope,
        )
        success = success and res
        print()

    if hub or update_all:
        res = update_hub(
            dir_hub,
            hub_launcher,
            dry_run=check,
            force=force,
            install_desktop=install_desktop,
            suid_sandbox=apparmor_sandbox,
            scope=scope,
        )
        success = success and res
        print()

    if cli or update_all:
        res = update_cli(path_cli, dry_run=check, force=force, scope=scope)
        success = success and res
        print()

    if success:
        print_success("Operation completed successfully.")
        sys.exit(0)
    else:
        print_error("One or more update operations failed.")
        sys.exit(1)
