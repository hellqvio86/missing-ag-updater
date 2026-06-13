import argparse
import os
import sys

from .const import (
    ARCH_NAME,
    COLOR_BOLD,
    COLOR_ENDC,
    COLOR_HEADER,
    DEFAULT_CLI_BINARY,
    DEFAULT_HUB_DIR,
    DEFAULT_HUB_LAUNCHER,
    DEFAULT_IDE_DIR,
    DEFAULT_IDE_LAUNCHER,
    OS_NAME,
)
from .updater import update_cli, update_hub, update_ide
from .utils import print_error, print_info, print_success, print_warning


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


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Auto-updater utility for Google Antigravity developer tools (Cross-Platform).",
        formatter_class=argparse.RawTextHelpFormatter,
    )
    parser.add_argument(
        "--check", action="store_true", default=None, help="Check for available updates without installing"
    )
    parser.add_argument("--ide", action="store_true", default=None, help="Update only the Antigravity IDE")
    parser.add_argument("--hub", action="store_true", default=None, help="Update only the Antigravity Hub")
    parser.add_argument("--cli", action="store_true", default=None, help="Update only the Antigravity CLI")
    parser.add_argument(
        "--force", action="store_true", default=None, help="Bypass version checks and active process warnings"
    )
    parser.add_argument("--dir-ide", type=str, default=None, help="Override path to Antigravity IDE folder/bundle")
    parser.add_argument("--dir-hub", type=str, default=None, help="Override path to Antigravity Hub folder/bundle")
    parser.add_argument("--path-cli", type=str, default=None, help="Override path to Antigravity CLI binary")
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

    args = parser.parse_args()

    if OS_NAME == "unknown":
        print_error("Unsupported operating system.")
        sys.exit(1)

    # Resolve settings from CLI arguments or environment variables
    check = args.check if args.check is not None else get_env_bool(["ANTIGRAVITY_CHECK", "AG_CHECK"], False)
    ide = args.ide if args.ide is not None else get_env_bool(["ANTIGRAVITY_IDE", "AG_IDE"], False)
    hub = args.hub if args.hub is not None else get_env_bool(["ANTIGRAVITY_HUB", "AG_HUB"], False)
    cli = args.cli if args.cli is not None else get_env_bool(["ANTIGRAVITY_CLI", "AG_CLI"], False)
    force = args.force if args.force is not None else get_env_bool(["ANTIGRAVITY_FORCE", "AG_FORCE"], False)

    dir_ide = args.dir_ide or get_env_str(["ANTIGRAVITY_DIR_IDE", "AG_DIR_IDE"], DEFAULT_IDE_DIR)
    dir_hub = args.dir_hub or get_env_str(["ANTIGRAVITY_DIR_HUB", "AG_DIR_HUB"], DEFAULT_HUB_DIR)
    path_cli = args.path_cli or get_env_str(["ANTIGRAVITY_PATH_CLI", "AG_PATH_CLI"], DEFAULT_CLI_BINARY)

    if args.install_desktop is not None:
        install_desktop = args.install_desktop
    else:
        if get_env_bool(["ANTIGRAVITY_NO_DESKTOP", "AG_NO_DESKTOP"], False):
            install_desktop = False
        else:
            install_desktop = get_env_bool(["ANTIGRAVITY_DESKTOP", "AG_DESKTOP"], True)

    if args.install_nautilus is not None:
        install_nautilus = args.install_nautilus
    else:
        if get_env_bool(["ANTIGRAVITY_NO_NAUTILUS", "AG_NO_NAUTILUS"], False):
            install_nautilus = False
        else:
            install_nautilus = get_env_bool(["ANTIGRAVITY_NAUTILUS", "AG_NAUTILUS"], True)

    # If no specific component is selected, default to all components
    update_all = not (ide or hub or cli)

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
            DEFAULT_IDE_LAUNCHER,
            dry_run=check,
            force=force,
            install_desktop=install_desktop,
            install_nautilus=install_nautilus,
        )
        success = success and res
        print()

    if hub or update_all:
        res = update_hub(
            dir_hub,
            DEFAULT_HUB_LAUNCHER,
            dry_run=check,
            force=force,
            install_desktop=install_desktop,
        )
        success = success and res
        print()

    if cli or update_all:
        res = update_cli(path_cli, dry_run=check, force=force)
        success = success and res
        print()

    if success:
        print_success("Operation completed successfully.")
        sys.exit(0)
    else:
        print_error("One or more update operations failed.")
        sys.exit(1)
