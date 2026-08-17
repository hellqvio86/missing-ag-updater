"""Configuration file loading, path discovery, and settings resolution for missing-ag-updater."""

import argparse
import os
import tomllib
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional

from . import utils
from .const import (
    DEFAULT_HUB_LAUNCHER,
    DEFAULT_IDE_LAUNCHER,
    HOME,
    OS_NAME,
    TRUTHY_VALUES,
)
from .discovery import (
    detect_preferred_cli,
    detect_preferred_hub,
    detect_preferred_ide,
)
from .utils import is_apparmor_enabled


@dataclass
class ResolvedConfig:
    """Fully resolved configuration combining CLI args, environment variables, TOML config, and defaults."""

    check: bool = False
    ide: bool = False
    hub: bool = False
    cli: bool = False
    force: bool = False
    system: bool = False
    user: bool = False
    scope: Optional[str] = None
    apparmor_sandbox: bool = False
    dir_ide: str = ""
    dir_hub: str = ""
    path_cli: str = ""
    ide_launcher: Optional[str] = None
    hub_launcher: Optional[str] = None
    install_desktop: bool = True
    install_nautilus: bool = True
    update_all: bool = True
    config_path: Optional[str] = None


def get_default_config_path() -> Path:
    """Get the standard configuration file path based on OS."""
    home_path = Path(HOME)
    if OS_NAME == "linux":
        xdg_config = os.environ.get("XDG_CONFIG_HOME")
        if xdg_config:
            base_dir = Path(xdg_config)
        else:
            base_dir = home_path / ".config"
        return base_dir / "missing-ag-updater" / "config.toml"

    elif OS_NAME == "darwin":
        return home_path / "Library" / "Application Support" / "missing-ag-updater" / "config.toml"

    elif OS_NAME == "windows":
        appdata = os.environ.get("APPDATA")
        if appdata:
            base_dir = Path(appdata)
        else:
            base_dir = home_path / "AppData" / "Roaming"
        return base_dir / "missing-ag-updater" / "config.toml"

    else:
        return home_path / ".missing-ag-updater.toml"


def load_toml_config(path: str | Path, *, explicit: bool = False) -> Dict[str, Any]:
    """Load settings from a TOML configuration file.

    If explicit is True, raise FileNotFoundError if the file does not exist.
    Otherwise, return an empty dictionary if the file is missing.
    """
    config_file = Path(path)
    if not config_file.exists():
        if explicit:
            raise FileNotFoundError(f"Configuration file not found: {config_file}")
        return {}

    try:
        with config_file.open("rb") as fdesc:
            return tomllib.load(fdesc)
    except (tomllib.TOMLDecodeError, OSError) as err:
        if explicit:
            raise ValueError(f"Failed to parse TOML configuration file: {err}") from err
        utils.print_warning(f"Could not load configuration file {config_file}: {err}")
        return {}


def get_env_bool(names: List[str], default: bool) -> bool:
    """Check a list of environment variable names for a boolean value."""
    for name in names:
        val = os.environ.get(name)
        if val is not None:
            return val.lower() in TRUTHY_VALUES
    return default


def get_env_str(names: List[str], default: str) -> str:
    """Check a list of environment variable names for a string value."""
    for name in names:
        val = os.environ.get(name)
        if val is not None:
            return val
    return default


def resolve_config(
    args: Optional[argparse.Namespace] = None,
) -> ResolvedConfig:
    """Resolve configuration from CLI arguments, environment variables, TOML config, and system defaults.

    Precedence order: CLI Arguments > Environment Variables > TOML Configuration > System Defaults / Auto-detection.
    """
    # 1. Resolve configuration file path
    cli_config = getattr(args, "config", None) if args else None
    explicit_config = True
    if cli_config:
        config_path_str = cli_config
    else:
        env_config = os.environ.get("ANTIGRAVITY_CONFIG") or os.environ.get("AG_CONFIG")
        if env_config:
            config_path_str = env_config
            explicit_config = True
        else:
            config_path_str = str(get_default_config_path())
            explicit_config = False

    # 2. Load TOML configuration if exists
    config_dict = load_toml_config(config_path_str, explicit=explicit_config)

    # 3. Helpers
    def _resolve_bool(cli_val: Optional[bool], env_names: List[str], toml_key: str, default_val: bool) -> bool:
        if cli_val is not None:
            return cli_val
        for name in env_names:
            val = os.environ.get(name)
            if val is not None:
                return val.lower() in TRUTHY_VALUES
        toml_val = config_dict.get(toml_key)
        if toml_val is not None:
            if isinstance(toml_val, bool):
                return toml_val
            if isinstance(toml_val, str):
                return toml_val.lower() in TRUTHY_VALUES
        return default_val

    def _resolve_str(cli_val: Optional[str], env_names: List[str], toml_key: str, default_val: str) -> str:
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
    arg_system = getattr(args, "system", None) if args else None
    arg_user = getattr(args, "user", None) if args else None
    is_system = _resolve_bool(arg_system, ["ANTIGRAVITY_SYSTEM", "AG_SYSTEM"], "system", False)
    is_user = _resolve_bool(arg_user, ["ANTIGRAVITY_USER", "AG_USER"], "user", False)
    scope: Optional[str] = "system" if is_system else ("user" if is_user else None)

    # Auto-detect preferred locations based on scope
    detected_ide_dir, detected_ide_launcher, _ = detect_preferred_ide(scope=scope)
    detected_hub_dir, detected_hub_launcher, _ = detect_preferred_hub(scope=scope)
    detected_cli_binary, _ = detect_preferred_cli(scope=scope)

    # Basic Flags
    check = _resolve_bool(
        getattr(args, "check", None) if args else None, ["ANTIGRAVITY_CHECK", "AG_CHECK"], "check", False
    )
    ide = _resolve_bool(getattr(args, "ide", None) if args else None, ["ANTIGRAVITY_IDE", "AG_IDE"], "ide", False)
    hub = _resolve_bool(getattr(args, "hub", None) if args else None, ["ANTIGRAVITY_HUB", "AG_HUB"], "hub", False)
    cli = _resolve_bool(getattr(args, "cli", None) if args else None, ["ANTIGRAVITY_CLI", "AG_CLI"], "cli", False)
    force = _resolve_bool(
        getattr(args, "force", None) if args else None, ["ANTIGRAVITY_FORCE", "AG_FORCE"], "force", False
    )

    # AppArmor sandbox: CLI flag > env var > TOML config > auto-detect
    arg_apparmor = getattr(args, "apparmor_sandbox", None) if args else None
    if arg_apparmor is not None:
        apparmor_sandbox = arg_apparmor
    else:
        sandbox_env = None
        for name in ["ANTIGRAVITY_APPARMOR_SANDBOX", "AG_APPARMOR_SANDBOX"]:
            val = os.environ.get(name)
            if val is not None:
                sandbox_env = val.lower() in TRUTHY_VALUES
                break

        if sandbox_env is not None:
            apparmor_sandbox = sandbox_env
        else:
            toml_val = config_dict.get("apparmor_sandbox")
            if toml_val is not None:
                if isinstance(toml_val, bool):
                    apparmor_sandbox = toml_val
                else:
                    apparmor_sandbox = str(toml_val).lower() in TRUTHY_VALUES
            else:
                apparmor_sandbox = OS_NAME == "linux" and is_apparmor_enabled()

    # Paths & Binaries
    arg_dir_ide = getattr(args, "dir_ide", None) if args else None
    arg_dir_hub = getattr(args, "dir_hub", None) if args else None
    arg_path_cli = getattr(args, "path_cli", None) if args else None

    dir_ide = _resolve_str(arg_dir_ide, ["ANTIGRAVITY_DIR_IDE", "AG_DIR_IDE"], "dir_ide", detected_ide_dir)
    dir_hub = _resolve_str(arg_dir_hub, ["ANTIGRAVITY_DIR_HUB", "AG_DIR_HUB"], "dir_hub", detected_hub_dir)
    path_cli = _resolve_str(arg_path_cli, ["ANTIGRAVITY_PATH_CLI", "AG_PATH_CLI"], "path_cli", detected_cli_binary)

    ide_launcher = (
        detected_ide_launcher
        if arg_dir_ide is None
        else (DEFAULT_IDE_LAUNCHER if scope != "system" else detected_ide_launcher)
    )
    hub_launcher = (
        detected_hub_launcher
        if arg_dir_hub is None
        else (DEFAULT_HUB_LAUNCHER if scope != "system" else detected_hub_launcher)
    )

    # Desktop entry integration
    arg_desktop = getattr(args, "install_desktop", None) if args else None
    if arg_desktop is not None:
        install_desktop = arg_desktop
    else:
        if get_env_bool(["ANTIGRAVITY_NO_DESKTOP", "AG_NO_DESKTOP"], False):
            install_desktop = False
        else:
            desktop_env = None
            for name in ["ANTIGRAVITY_DESKTOP", "AG_DESKTOP"]:
                val = os.environ.get(name)
                if val is not None:
                    desktop_env = val.lower() in TRUTHY_VALUES
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
                        install_desktop = str(toml_desktop).lower() in TRUTHY_VALUES
                elif toml_no_desktop is not None:
                    if isinstance(toml_no_desktop, bool):
                        install_desktop = not toml_no_desktop
                    else:
                        install_desktop = str(toml_no_desktop).lower() not in TRUTHY_VALUES
                else:
                    install_desktop = True

    # Nautilus integration
    arg_nautilus = getattr(args, "install_nautilus", None) if args else None
    if arg_nautilus is not None:
        install_nautilus = arg_nautilus
    else:
        if get_env_bool(["ANTIGRAVITY_NO_NAUTILUS", "AG_NO_NAUTILUS"], False):
            install_nautilus = False
        else:
            nautilus_env = None
            for name in ["ANTIGRAVITY_NAUTILUS", "AG_NAUTILUS"]:
                val = os.environ.get(name)
                if val is not None:
                    nautilus_env = val.lower() in TRUTHY_VALUES
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
                        install_nautilus = str(toml_nautilus).lower() in TRUTHY_VALUES
                elif toml_no_nautilus is not None:
                    if isinstance(toml_no_nautilus, bool):
                        install_nautilus = not toml_no_nautilus
                    else:
                        install_nautilus = str(toml_no_nautilus).lower() not in TRUTHY_VALUES
                else:
                    install_nautilus = True

    update_all = not (ide or hub or cli)

    return ResolvedConfig(
        check=check,
        ide=ide,
        hub=hub,
        cli=cli,
        force=force,
        system=is_system,
        user=is_user,
        scope=scope,
        apparmor_sandbox=apparmor_sandbox,
        dir_ide=dir_ide,
        dir_hub=dir_hub,
        path_cli=path_cli,
        ide_launcher=ide_launcher,
        hub_launcher=hub_launcher,
        install_desktop=install_desktop,
        install_nautilus=install_nautilus,
        update_all=update_all,
        config_path=config_path_str
        if (cli_config or os.environ.get("ANTIGRAVITY_CONFIG") or os.environ.get("AG_CONFIG"))
        else None,
    )
