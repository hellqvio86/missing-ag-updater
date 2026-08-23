import argparse
from pathlib import Path
from typing import Any
from unittest.mock import ANY, MagicMock, patch

import pytest

from missing_ag_updater.cli import main
from missing_ag_updater.config import (
    get_default_config_path,
    get_env_bool,
    get_env_str,
    load_toml_config,
    resolve_config,
)


@patch("missing_ag_updater.config.OS_NAME", "linux")
def test_get_default_config_path_linux(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("XDG_CONFIG_HOME", "/custom/xdg")
    assert get_default_config_path() == Path("/custom/xdg/missing-ag-updater/config.toml")

    monkeypatch.delenv("XDG_CONFIG_HOME", raising=False)
    with patch("missing_ag_updater.config.HOME", "/home/user"):
        assert get_default_config_path() == Path("/home/user/.config/missing-ag-updater/config.toml")


@patch("missing_ag_updater.config.HOME", "/Users/user")
@patch("missing_ag_updater.config.OS_NAME", "darwin")
def test_get_default_config_path_mac() -> None:
    assert get_default_config_path() == Path("/Users/user/Library/Application Support/missing-ag-updater/config.toml")


@patch("missing_ag_updater.config.OS_NAME", "windows")
def test_get_default_config_path_windows(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("APPDATA", "C:\\Users\\user\\AppData\\Roaming")
    expected = Path("C:\\Users\\user\\AppData\\Roaming") / "missing-ag-updater" / "config.toml"
    assert get_default_config_path() == expected

    monkeypatch.delenv("APPDATA", raising=False)
    with patch("missing_ag_updater.config.HOME", "C:\\Users\\user"):
        expected_home = Path("C:\\Users\\user") / "AppData" / "Roaming" / "missing-ag-updater" / "config.toml"
        assert get_default_config_path() == expected_home


@patch("missing_ag_updater.config.HOME", "/home/user")
@patch("missing_ag_updater.config.OS_NAME", "unknown")
def test_get_default_config_path_other() -> None:
    assert get_default_config_path() == Path("/home/user/.missing-ag-updater.toml")


def test_load_toml_config_missing(tmp_path: Any) -> None:
    non_existent = str(tmp_path / "missing.toml")
    assert load_toml_config(non_existent, explicit=False) == {}

    with pytest.raises(FileNotFoundError):
        load_toml_config(non_existent, explicit=True)


@patch("missing_ag_updater.utils.print_warning")
def test_load_toml_config_corrupt(mock_warn: MagicMock, tmp_path: Any) -> None:
    corrupt_file = tmp_path / "corrupt.toml"
    with open(corrupt_file, "w", encoding="utf-8") as fdesc:
        fdesc.write("this is not valid toml = {")

    assert load_toml_config(str(corrupt_file), explicit=False) == {}
    mock_warn.assert_called_once()

    with pytest.raises(ValueError):
        load_toml_config(str(corrupt_file), explicit=True)


def test_load_toml_config_valid(tmp_path: Any) -> None:
    valid_file = tmp_path / "valid.toml"
    with open(valid_file, "w", encoding="utf-8") as fdesc:
        fdesc.write('force = true\ndir_ide = "/custom/ide"\n')

    data = load_toml_config(str(valid_file))
    assert data == {"force": True, "dir_ide": "/custom/ide"}


def test_cli_config_integration(tmp_path: Any) -> None:
    config_file = tmp_path / "cli_config.toml"
    with open(config_file, "w", encoding="utf-8") as fdesc:
        fdesc.write("force = true\ndesktop = false\nnautilus = false\napparmor_sandbox = false\n")

    @patch("sys.exit", side_effect=SystemExit)
    @patch("missing_ag_updater.cli.update_ide", return_value=True)
    @patch("missing_ag_updater.cli.OS_NAME", "linux")
    @patch("sys.argv", ["antigravity-updater", "--ide", "--config", str(config_file)])
    def _run_test(mock_ide: MagicMock, mock_exit: MagicMock) -> None:
        with pytest.raises(SystemExit):
            main()
        mock_ide.assert_called_once_with(
            ANY,
            ANY,
            dry_run=False,
            force=True,
            install_desktop=False,
            install_nautilus=False,
            suid_sandbox=False,
            scope=None,
        )
        mock_exit.assert_called_once_with(0)

    _run_test()


@patch("sys.exit", side_effect=SystemExit)
@patch("missing_ag_updater.cli.print_error")
@patch("missing_ag_updater.cli.OS_NAME", "linux")
@patch("sys.argv", ["antigravity-updater", "--config", "/nonexistent/config.toml"])
def test_cli_config_nonexistent_fails(mock_print_err: MagicMock, mock_exit: MagicMock) -> None:
    with pytest.raises(SystemExit):
        main()
    mock_print_err.assert_called_once_with("Configuration file not found: /nonexistent/config.toml")
    mock_exit.assert_called_once_with(1)


def test_get_env_bool(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("TEST_VAR_TRUE", "yes")
    monkeypatch.setenv("TEST_VAR_FALSE", "off")
    monkeypatch.setenv("TEST_VAR_INVALID", "banana")

    assert get_env_bool(["TEST_VAR_TRUE"], False) is True
    assert get_env_bool(["TEST_VAR_FALSE"], True) is False
    assert get_env_bool(["NON_EXISTENT"], True) is True
    assert get_env_bool(["NON_EXISTENT"], False) is False
    # Invalid value should warn and return default
    assert get_env_bool(["TEST_VAR_INVALID"], False) is False
    assert get_env_bool(["TEST_VAR_INVALID"], True) is True


def test_get_env_str(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("TEST_STR", "/custom/path")
    assert get_env_str(["TEST_STR"], "default") == "/custom/path"
    assert get_env_str(["NON_EXISTENT"], "default") == "default"


@patch("missing_ag_updater.config.is_apparmor_enabled", return_value=False)
@patch("missing_ag_updater.config.load_toml_config", return_value={})
def test_resolve_config_defaults(
    mock_toml: MagicMock,
    mock_apparmor: MagicMock,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    for env_var in [
        "ANTIGRAVITY_CHECK",
        "AG_CHECK",
        "ANTIGRAVITY_FORCE",
        "AG_FORCE",
        "ANTIGRAVITY_USER",
        "AG_USER",
        "ANTIGRAVITY_SYSTEM",
        "AG_SYSTEM",
    ]:
        monkeypatch.delenv(env_var, raising=False)

    cfg = resolve_config(None)
    assert cfg.check is False
    assert cfg.ide is False
    assert cfg.hub is False
    assert cfg.cli is False
    assert cfg.force is False
    assert cfg.scope is None
    assert cfg.install_desktop is True
    assert cfg.install_nautilus is True
    assert cfg.update_all is True


@patch("missing_ag_updater.config.is_apparmor_enabled", return_value=False)
def test_resolve_config_precedence(
    mock_apparmor: MagicMock,
    tmp_path: Any,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    config_file = tmp_path / "config.toml"
    with open(config_file, "w", encoding="utf-8") as fdesc:
        fdesc.write('force = false\ndir_ide = "/toml/path"\n')

    monkeypatch.setenv("ANTIGRAVITY_FORCE", "true")
    monkeypatch.setenv("ANTIGRAVITY_DIR_IDE", "/env/path")

    args = argparse.Namespace(
        config=str(config_file),
        force=None,
        dir_ide="/cli/path",
        check=None,
        ide=True,
        hub=None,
        cli=None,
        system=None,
        user=None,
        apparmor_sandbox=None,
        dir_hub=None,
        path_cli=None,
        install_desktop=None,
        install_nautilus=None,
    )
    cfg = resolve_config(args)
    assert cfg.dir_ide == "/cli/path"
    assert cfg.force is True
    assert cfg.ide is True
    assert cfg.update_all is False
    assert cfg.config_path == str(config_file)


@patch("missing_ag_updater.config.is_apparmor_enabled", return_value=False)
def test_resolve_config_scopes_and_inverses(
    mock_apparmor: MagicMock,
    tmp_path: Any,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    args_system = argparse.Namespace(
        config=None,
        system=True,
        user=False,
        force=False,
        check=False,
        ide=False,
        hub=False,
        cli=False,
        dir_ide=None,
        dir_hub=None,
        path_cli=None,
        install_desktop=False,
        install_nautilus=False,
        apparmor_sandbox=True,
    )
    cfg = resolve_config(args_system)
    assert cfg.scope == "system"
    assert cfg.install_desktop is False
    assert cfg.install_nautilus is False
    assert cfg.apparmor_sandbox is True

    monkeypatch.setenv("ANTIGRAVITY_USER", "1")
    monkeypatch.setenv("ANTIGRAVITY_NO_DESKTOP", "1")

    cfg_env = resolve_config(None)
    assert cfg_env.scope == "user"
    assert cfg_env.install_desktop is False


def test_load_example_config_file() -> None:
    repo_root = Path(__file__).parent.parent.parent
    example_toml = repo_root / "config.example.toml"
    if example_toml.exists():
        data = load_toml_config(str(example_toml), explicit=True)
        assert isinstance(data, dict)
        assert "check" in data or "ide" in data or len(data) > 0
