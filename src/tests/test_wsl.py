"""Tests for WSL detection and the CLI-only default inside WSL."""

import argparse
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from missing_ag_updater.cli import main, run_diagnose
from missing_ag_updater.config import resolve_config
from missing_ag_updater.utils import is_wsl


@pytest.fixture
def wsl_host(monkeypatch: pytest.MonkeyPatch) -> None:
    """Simulate running inside WSL."""
    monkeypatch.setenv("WSL_DISTRO_NAME", "Ubuntu")


def _empty_args(**overrides: object) -> argparse.Namespace:
    defaults: dict[str, object] = {
        "config": None,
        "check": None,
        "ide": None,
        "hub": None,
        "cli": None,
        "force": None,
        "system": None,
        "user": None,
        "apparmor_sandbox": False,
        "dir_ide": None,
        "dir_hub": None,
        "path_cli": None,
        "install_desktop": None,
        "install_nautilus": None,
    }
    defaults.update(overrides)
    return argparse.Namespace(**defaults)


# --- is_wsl() -------------------------------------------------------------------------


@patch("missing_ag_updater.utils.OS_NAME", "linux")
def test_is_wsl_false_on_plain_linux() -> None:
    assert is_wsl() is False


@patch("missing_ag_updater.utils.OS_NAME", "linux")
@pytest.mark.parametrize("env_name", ["WSL_DISTRO_NAME", "WSL_INTEROP"])
def test_is_wsl_detects_env_markers(env_name: str, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv(env_name, "value")
    assert is_wsl() is True


@patch("missing_ag_updater.utils.OS_NAME", "linux")
@pytest.mark.parametrize(
    ("kernel_release", "expected"),
    [
        ("5.15.153.1-microsoft-standard-WSL2\n", True),
        ("4.4.0-19041-Microsoft\n", True),
        ("6.8.0-48-generic\n", False),
    ],
)
def test_is_wsl_kernel_release(
    kernel_release: str, expected: bool, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    release_file = tmp_path / "osrelease"
    release_file.write_text(kernel_release, encoding="utf-8")
    monkeypatch.setattr("missing_ag_updater.utils.WSL_KERNEL_RELEASE_FILES", (str(release_file),))
    assert is_wsl() is expected


@patch("missing_ag_updater.utils.OS_NAME", "linux")
def test_is_wsl_ignores_unreadable_release_files(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("missing_ag_updater.utils.WSL_KERNEL_RELEASE_FILES", (str(tmp_path / "missing"),))
    assert is_wsl() is False


@patch("missing_ag_updater.utils.OS_NAME", "windows")
def test_is_wsl_false_on_non_linux(wsl_host: None) -> None:
    assert is_wsl() is False


# --- resolve_config() -----------------------------------------------------------------


@patch("missing_ag_updater.utils.OS_NAME", "linux")
@patch("missing_ag_updater.config.load_toml_config", return_value={})
def test_resolve_config_wsl_defaults_to_cli_only(mock_toml: MagicMock, wsl_host: None) -> None:
    cfg = resolve_config(_empty_args())
    assert cfg.wsl is True
    assert cfg.wsl_cli_only is True
    assert cfg.cli is True
    assert cfg.ide is False
    assert cfg.hub is False
    assert cfg.update_all is False


@patch("missing_ag_updater.utils.OS_NAME", "linux")
@patch("missing_ag_updater.config.load_toml_config", return_value={})
def test_resolve_config_wsl_respects_explicit_gui_request(mock_toml: MagicMock, wsl_host: None) -> None:
    cfg = resolve_config(_empty_args(ide=True))
    assert cfg.wsl is True
    assert cfg.wsl_cli_only is False
    assert cfg.ide is True
    assert cfg.cli is False


@patch("missing_ag_updater.utils.OS_NAME", "linux")
@patch("missing_ag_updater.config.load_toml_config", return_value={"hub": True})
def test_resolve_config_wsl_respects_toml_components(mock_toml: MagicMock, wsl_host: None) -> None:
    cfg = resolve_config(_empty_args())
    assert cfg.wsl_cli_only is False
    assert cfg.hub is True
    assert cfg.cli is False


@patch("missing_ag_updater.config.load_toml_config", return_value={})
def test_resolve_config_non_wsl_updates_all(mock_toml: MagicMock) -> None:
    cfg = resolve_config(_empty_args())
    assert cfg.wsl is False
    assert cfg.wsl_cli_only is False
    assert cfg.update_all is True


# --- main() ---------------------------------------------------------------------------


@patch("sys.exit", side_effect=SystemExit)
@patch("missing_ag_updater.cli.update_cli", return_value=True)
@patch("missing_ag_updater.cli.update_hub", return_value=True)
@patch("missing_ag_updater.cli.update_ide", return_value=True)
@patch("missing_ag_updater.config.load_toml_config", return_value={})
@patch("missing_ag_updater.utils.OS_NAME", "linux")
@patch("missing_ag_updater.cli.OS_NAME", "linux")
@patch("sys.argv", ["antigravity-updater"])
def test_main_wsl_updates_only_cli(
    mock_toml: MagicMock,
    mock_ide: MagicMock,
    mock_hub: MagicMock,
    mock_cli: MagicMock,
    mock_exit: MagicMock,
    wsl_host: None,
    capsys: pytest.CaptureFixture[str],
) -> None:
    with pytest.raises(SystemExit):
        main()
    mock_ide.assert_not_called()
    mock_hub.assert_not_called()
    mock_cli.assert_called_once()
    mock_exit.assert_called_once_with(0)
    assert "WSL detected" in capsys.readouterr().out


@patch("sys.exit", side_effect=SystemExit)
@patch("missing_ag_updater.cli.uninstall_cli", return_value=True)
@patch("missing_ag_updater.cli.uninstall_hub", return_value=True)
@patch("missing_ag_updater.cli.uninstall_ide", return_value=True)
@patch("missing_ag_updater.config.load_toml_config", return_value={})
@patch("missing_ag_updater.utils.OS_NAME", "linux")
@patch("missing_ag_updater.cli.OS_NAME", "linux")
@patch("sys.argv", ["antigravity-updater", "--uninstall"])
def test_main_wsl_uninstall_still_removes_everything(
    mock_toml: MagicMock,
    mock_ide: MagicMock,
    mock_hub: MagicMock,
    mock_cli: MagicMock,
    mock_exit: MagicMock,
    wsl_host: None,
) -> None:
    with pytest.raises(SystemExit):
        main()
    mock_ide.assert_called_once()
    mock_hub.assert_called_once()
    mock_cli.assert_called_once()
    mock_exit.assert_called_once_with(0)


@patch("missing_ag_updater.utils.OS_NAME", "linux")
@patch("missing_ag_updater.cli.diagnose_all")
def test_run_diagnose_shows_wsl(mock_diag: MagicMock, capsys: pytest.CaptureFixture[str]) -> None:
    mock_diag.return_value = {
        "os": "linux",
        "wsl": True,
        "ide_installations": [],
        "hub_installations": [],
        "cli_installations": [],
    }
    run_diagnose()
    assert "WSL" in capsys.readouterr().out
