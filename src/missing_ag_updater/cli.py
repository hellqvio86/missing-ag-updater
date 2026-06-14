import argparse
import os
import sys

from .config import get_default_config_path, load_toml_config
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
    except Exception as e:
        print_error(str(e))
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

    # Resolve settings (CLI > Env > TOML > Default)
    check = resolve_bool(args.check, ["ANTIGRAVITY_CHECK", "AG_CHECK"], "check", False)
    ide = resolve_bool(args.ide, ["ANTIGRAVITY_IDE", "AG_IDE"], "ide", False)
    hub = resolve_bool(args.hub, ["ANTIGRAVITY_HUB", "AG_HUB"], "hub", False)
    cli = resolve_bool(args.cli, ["ANTIGRAVITY_CLI", "AG_CLI"], "cli", False)
    force = resolve_bool(args.force, ["ANTIGRAVITY_FORCE", "AG_FORCE"], "force", False)

    dir_ide = resolve_str(args.dir_ide, ["ANTIGRAVITY_DIR_IDE", "AG_DIR_IDE"], "dir_ide", DEFAULT_IDE_DIR)
    dir_hub = resolve_str(args.dir_hub, ["ANTIGRAVITY_DIR_HUB", "AG_DIR_HUB"], "dir_hub", DEFAULT_HUB_DIR)
    path_cli = resolve_str(args.path_cli, ["ANTIGRAVITY_PATH_CLI", "AG_PATH_CLI"], "path_cli", DEFAULT_CLI_BINARY)

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
                        install_desktop = str(toml_desktop).lower() in ("1", "true", "yes", "on")
                elif toml_no_desktop is not None:
                    if isinstance(toml_no_desktop, bool):
                        install_desktop = not toml_no_desktop
                    else:
                        install_desktop = str(toml_no_desktop).lower() not in ("1", "true", "yes", "on")
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
                        install_nautilus = str(toml_nautilus).lower() in ("1", "true", "yes", "on")
                elif toml_no_nautilus is not None:
                    if isinstance(toml_no_nautilus, bool):
                        install_nautilus = not toml_no_nautilus
                    else:
                        install_nautilus = str(toml_no_nautilus).lower() not in ("1", "true", "yes", "on")
                else:
                    install_nautilus = True

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
