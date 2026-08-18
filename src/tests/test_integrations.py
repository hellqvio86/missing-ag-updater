import os
import runpy
from typing import Any
from unittest.mock import ANY, MagicMock, patch

import pytest

from missing_ag_updater.cli import main
from missing_ag_updater.desktop import install_hub_desktop, install_ide_desktop
from missing_ag_updater.nautilus import install_ide_nautilus


def test_install_ide_desktop(tmp_path: Any) -> None:
    user_app_dir = str(tmp_path / "apps")
    user_icons_dir = str(tmp_path / "icons")
    ide_dir = str(tmp_path / "ide")
    launcher_path = str(tmp_path / "launcher")

    os.makedirs(os.path.join(ide_dir, "resources", "app", "resources", "linux"), exist_ok=True)
    icon_source = os.path.join(ide_dir, "resources", "app", "resources", "linux", "code.png")
    with open(icon_source, "w", encoding="utf-8") as fdesc:
        fdesc.write("icon-data")

    @patch("missing_ag_updater.desktop.refresh_linux_desktop_caches")
    @patch("missing_ag_updater.desktop.SYSTEM_ICONS_DIR", str(tmp_path / "sys_icons"))
    @patch("missing_ag_updater.desktop.USER_ICONS_DIR", user_icons_dir)
    @patch("missing_ag_updater.desktop.USER_APPLICATIONS_DIR", user_app_dir)
    def _run_test(mock_refresh: MagicMock) -> None:
        install_ide_desktop(ide_dir=ide_dir, launcher_path=launcher_path)

        desktop_file = os.path.join(user_app_dir, "antigravity-ide.desktop")
        assert os.path.exists(desktop_file)
        with open(desktop_file, "r", encoding="utf-8") as fdesc:
            content = fdesc.read()
            assert "Exec=" + launcher_path in content
            assert "Icon=antigravity" in content

        dest_icon = os.path.join(user_icons_dir, "antigravity-ide.png")
        assert os.path.exists(dest_icon)
        with open(dest_icon, "r", encoding="utf-8") as fdesc:
            assert fdesc.read() == "icon-data"

        mock_refresh.assert_called_once()

    _run_test()


def test_install_ide_desktop_prefers_official_branding(tmp_path: Any) -> None:
    user_app_dir = str(tmp_path / "apps")
    user_icons_dir = str(tmp_path / "icons")
    ide_dir = str(tmp_path / "ide")
    launcher_path = str(tmp_path / "launcher")

    os.makedirs(user_icons_dir, exist_ok=True)
    with open(os.path.join(user_icons_dir, "antigravity.png"), "w", encoding="utf-8") as fdesc:
        fdesc.write("official-branding-data")

    @patch("missing_ag_updater.desktop.refresh_linux_desktop_caches")
    @patch("missing_ag_updater.desktop.SYSTEM_ICONS_DIR", str(tmp_path / "sys_icons"))
    @patch("missing_ag_updater.desktop.USER_ICONS_DIR", user_icons_dir)
    @patch("missing_ag_updater.desktop.USER_APPLICATIONS_DIR", user_app_dir)
    def _run_test(mock_refresh: MagicMock) -> None:
        install_ide_desktop(ide_dir=ide_dir, launcher_path=launcher_path)
        dest_icon = os.path.join(user_icons_dir, "antigravity-ide.png")
        assert os.path.exists(dest_icon)
        with open(dest_icon, "r", encoding="utf-8") as fdesc:
            assert fdesc.read() == "official-branding-data"

    _run_test()


def test_install_ide_desktop_system_scope_and_cleanup(tmp_path: Any) -> None:
    sys_app_dir = str(tmp_path / "sys_apps")
    sys_icons_dir = str(tmp_path / "sys_icons")
    user_app_dir = str(tmp_path / "user_apps")
    user_icons_dir = str(tmp_path / "user_icons")
    ide_dir = str(tmp_path / "ide")

    os.makedirs(os.path.join(ide_dir, "Antigravity-IDE", "resources", "app", "resources", "linux"), exist_ok=True)
    icon_source = os.path.join(ide_dir, "Antigravity-IDE", "resources", "app", "resources", "linux", "code.png")
    with open(icon_source, "w", encoding="utf-8") as fdesc:
        fdesc.write("nested-icon-data")

    os.makedirs(user_app_dir, exist_ok=True)
    user_dt = os.path.join(user_app_dir, "antigravity-ide.desktop")
    with open(user_dt, "w", encoding="utf-8") as fdesc:
        fdesc.write("old user desktop")

    @patch("missing_ag_updater.desktop.refresh_linux_desktop_caches")
    @patch("missing_ag_updater.desktop.USER_ICONS_DIR", user_icons_dir)
    @patch("missing_ag_updater.desktop.USER_APPLICATIONS_DIR", user_app_dir)
    @patch("missing_ag_updater.desktop.SYSTEM_ICONS_DIR", sys_icons_dir)
    @patch("missing_ag_updater.desktop.SYSTEM_APPLICATIONS_DIR", sys_app_dir)
    def _run_test(mock_refresh: MagicMock) -> None:
        install_ide_desktop(ide_dir=ide_dir, launcher_path=None, scope="system")
        assert os.path.exists(os.path.join(sys_app_dir, "antigravity-ide.desktop"))
        assert not os.path.exists(user_dt)
        mock_refresh.assert_called_once()

    _run_test()


def test_install_ide_desktop_notice_when_system_exists(tmp_path: Any, capsys: Any) -> None:
    user_app_dir = str(tmp_path / "user_apps")
    sys_app_dir = str(tmp_path / "sys_apps")
    os.makedirs(sys_app_dir, exist_ok=True)
    with open(os.path.join(sys_app_dir, "antigravity-ide.desktop"), "w", encoding="utf-8") as fdesc:
        fdesc.write("sys desktop")

    @patch("missing_ag_updater.desktop.refresh_linux_desktop_caches")
    @patch("missing_ag_updater.desktop.USER_ICONS_DIR", str(tmp_path / "icons"))
    @patch("missing_ag_updater.desktop.SYSTEM_APPLICATIONS_DIR", sys_app_dir)
    @patch("missing_ag_updater.desktop.USER_APPLICATIONS_DIR", user_app_dir)
    def _run_test(mock_refresh: MagicMock) -> None:
        install_ide_desktop(ide_dir=str(tmp_path / "ide"), launcher_path="/bin/ide", scope="user")
        captured = capsys.readouterr().out
        assert "Notice: System desktop entry also exists" in captured

    _run_test()


def test_install_hub_desktop(tmp_path: Any) -> None:
    user_app_dir = str(tmp_path / "apps")
    user_icons_dir = str(tmp_path / "icons")
    hub_dir = str(tmp_path / "hub")
    launcher_path = str(tmp_path / "launcher")

    os.makedirs(os.path.join(hub_dir, "resources"), exist_ok=True)
    asar_path = os.path.join(hub_dir, "resources", "app.asar")
    with open(asar_path, "w", encoding="utf-8") as fdesc:
        fdesc.write("asar-data")

    @patch("missing_ag_updater.desktop.refresh_linux_desktop_caches")
    @patch("missing_ag_updater.desktop.extract_asar_icon", return_value=True)
    @patch("missing_ag_updater.desktop.USER_ICONS_DIR", user_icons_dir)
    @patch("missing_ag_updater.desktop.USER_APPLICATIONS_DIR", user_app_dir)
    def _run_test(mock_extract: MagicMock, mock_refresh: MagicMock) -> None:
        install_hub_desktop(hub_dir=hub_dir, launcher_path=launcher_path)

        desktop_file = os.path.join(user_app_dir, "antigravity.desktop")
        assert os.path.exists(desktop_file)
        with open(desktop_file, "r", encoding="utf-8") as fdesc:
            content = fdesc.read()
            assert "Exec=" + launcher_path in content
            assert "Icon=antigravity" in content

        mock_extract.assert_called_once_with(asar_path, os.path.join(user_icons_dir, "antigravity.png"))
        mock_refresh.assert_called_once()

    _run_test()


def test_install_hub_desktop_system_scope_and_extract_failure(tmp_path: Any) -> None:
    sys_app_dir = str(tmp_path / "sys_apps")
    sys_icons_dir = str(tmp_path / "sys_icons")
    user_app_dir = str(tmp_path / "user_apps")
    user_icons_dir = str(tmp_path / "user_icons")
    hub_dir = str(tmp_path / "hub")

    os.makedirs(os.path.join(hub_dir, "Antigravity-x64", "resources"), exist_ok=True)
    with open(os.path.join(hub_dir, "Antigravity-x64", "resources", "app.asar"), "w", encoding="utf-8") as fdesc:
        fdesc.write("asar")

    os.makedirs(user_app_dir, exist_ok=True)
    user_dt = os.path.join(user_app_dir, "antigravity.desktop")
    with open(user_dt, "w", encoding="utf-8") as fdesc:
        fdesc.write("user desktop")

    @patch("missing_ag_updater.desktop.refresh_linux_desktop_caches")
    @patch("missing_ag_updater.desktop.extract_asar_icon", return_value=False)
    @patch("missing_ag_updater.desktop.USER_ICONS_DIR", user_icons_dir)
    @patch("missing_ag_updater.desktop.USER_APPLICATIONS_DIR", user_app_dir)
    @patch("missing_ag_updater.desktop.SYSTEM_ICONS_DIR", sys_icons_dir)
    @patch("missing_ag_updater.desktop.SYSTEM_APPLICATIONS_DIR", sys_app_dir)
    def _run_test(mock_extract: MagicMock, mock_refresh: MagicMock) -> None:
        install_hub_desktop(hub_dir=hub_dir, launcher_path=None, scope="system")
        assert os.path.exists(os.path.join(sys_app_dir, "antigravity.desktop"))
        assert not os.path.exists(user_dt)

    _run_test()


def test_install_hub_desktop_notice_when_system_exists(tmp_path: Any, capsys: Any) -> None:
    user_app_dir = str(tmp_path / "user_apps")
    sys_app_dir = str(tmp_path / "sys_apps")
    os.makedirs(sys_app_dir, exist_ok=True)
    with open(os.path.join(sys_app_dir, "antigravity.desktop"), "w", encoding="utf-8") as fdesc:
        fdesc.write("sys desktop")

    @patch("missing_ag_updater.desktop.refresh_linux_desktop_caches")
    @patch("missing_ag_updater.desktop.USER_ICONS_DIR", str(tmp_path / "icons"))
    @patch("missing_ag_updater.desktop.SYSTEM_APPLICATIONS_DIR", sys_app_dir)
    @patch("missing_ag_updater.desktop.USER_APPLICATIONS_DIR", user_app_dir)
    def _run_test(mock_refresh: MagicMock) -> None:
        install_hub_desktop(hub_dir=str(tmp_path / "hub"), launcher_path="/bin/hub", scope="user")
        captured = capsys.readouterr().out
        assert "Notice: System desktop entry also exists" in captured

    _run_test()


def test_install_ide_nautilus(tmp_path: Any) -> None:
    user_nautilus_dir = str(tmp_path / "nautilus")
    ide_dir = str(tmp_path / "ide")
    launcher_path = str(tmp_path / "launcher")

    @patch("missing_ag_updater.nautilus.refresh_linux_desktop_caches")
    @patch("missing_ag_updater.nautilus.USER_NAUTILUS_DIR", user_nautilus_dir)
    def _run_test(mock_refresh: MagicMock) -> None:
        install_ide_nautilus(ide_dir=ide_dir, launcher_path=launcher_path)

        nautilus_file = os.path.join(user_nautilus_dir, "open-in-antigravity-ide.py")
        assert os.path.exists(nautilus_file)
        with open(nautilus_file, "r", encoding="utf-8") as fdesc:
            content = fdesc.read()
            assert "class OpenInAntigravityIDE" in content
            assert launcher_path in content

        mock_refresh.assert_called_once()

    _run_test()


@patch("sys.argv", ["antigravity-updater", "--help"])
def test_main_module_execution() -> None:
    with pytest.raises(SystemExit) as excinfo:
        runpy.run_module("missing_ag_updater.__main__", run_name="__main__")
    assert excinfo.value.code == 0


@patch("sys.exit", side_effect=SystemExit)
@patch("missing_ag_updater.cli.update_ide", return_value=True)
@patch("missing_ag_updater.config.load_toml_config", return_value={})
@patch("missing_ag_updater.cli.OS_NAME", "linux")
@patch(
    "sys.argv",
    [
        "antigravity-updater",
        "--ide",
        "--no-desktop",
        "--no-nautilus",
        "--no-apparmor-sandbox",
    ],
)
def test_cli_no_desktop_no_nautilus(
    mock_toml: MagicMock,
    mock_ide: MagicMock,
    mock_exit: MagicMock,
) -> None:
    with pytest.raises(SystemExit):
        main()
    mock_ide.assert_called_once_with(
        ANY,
        ANY,
        dry_run=False,
        force=False,
        install_desktop=False,
        install_nautilus=False,
        suid_sandbox=False,
        scope=None,
    )
    mock_exit.assert_called_once_with(0)


@patch("sys.exit", side_effect=SystemExit)
@patch("missing_ag_updater.cli.update_hub", return_value=True)
@patch("missing_ag_updater.config.load_toml_config", return_value={})
@patch("missing_ag_updater.cli.OS_NAME", "linux")
@patch(
    "sys.argv",
    [
        "antigravity-updater",
        "--hub",
        "--no-desktop",
        "--no-apparmor-sandbox",
    ],
)
def test_cli_no_desktop_hub(
    mock_toml: MagicMock,
    mock_hub: MagicMock,
    mock_exit: MagicMock,
) -> None:
    with pytest.raises(SystemExit):
        main()
    mock_hub.assert_called_once_with(
        ANY,
        ANY,
        dry_run=False,
        force=False,
        install_desktop=False,
        suid_sandbox=False,
        scope=None,
    )
    mock_exit.assert_called_once_with(0)


@patch("sys.exit", side_effect=SystemExit)
@patch("missing_ag_updater.cli.update_ide", return_value=True)
@patch("missing_ag_updater.config.load_toml_config", return_value={})
@patch("missing_ag_updater.cli.OS_NAME", "linux")
@patch("sys.argv", ["antigravity-updater", "--ide"])
def test_cli_env_variables(
    mock_toml: MagicMock,
    mock_ide: MagicMock,
    mock_exit: MagicMock,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("ANTIGRAVITY_CHECK", "true")
    monkeypatch.setenv("ANTIGRAVITY_FORCE", "yes")
    monkeypatch.setenv("ANTIGRAVITY_DIR_IDE", "/env/ide/path")
    monkeypatch.setenv("ANTIGRAVITY_NO_DESKTOP", "1")
    monkeypatch.setenv("ANTIGRAVITY_NO_NAUTILUS", "true")
    monkeypatch.setenv("ANTIGRAVITY_APPARMOR_SANDBOX", "0")

    with pytest.raises(SystemExit):
        main()
    mock_ide.assert_called_once_with(
        "/env/ide/path",
        ANY,
        dry_run=True,
        force=True,
        install_desktop=False,
        install_nautilus=False,
        suid_sandbox=False,
        scope=None,
    )
    mock_exit.assert_called_once_with(0)


@patch("sys.exit", side_effect=SystemExit)
@patch("missing_ag_updater.cli.update_hub", return_value=True)
@patch("missing_ag_updater.config.load_toml_config", return_value={})
@patch("missing_ag_updater.cli.OS_NAME", "linux")
@patch("sys.argv", ["antigravity-updater", "--hub", "--no-apparmor-sandbox"])
def test_cli_env_variables_alt_prefix(
    mock_toml: MagicMock,
    mock_hub: MagicMock,
    mock_exit: MagicMock,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("AG_CHECK", "1")
    monkeypatch.setenv("AG_FORCE", "true")
    monkeypatch.setenv("AG_DIR_HUB", "/env/hub/path")
    monkeypatch.setenv("AG_DESKTOP", "false")

    with pytest.raises(SystemExit):
        main()
    mock_hub.assert_called_once_with(
        "/env/hub/path",
        ANY,
        dry_run=True,
        force=True,
        install_desktop=False,
        suid_sandbox=False,
        scope=None,
    )
    mock_exit.assert_called_once_with(0)


@patch("sys.exit", side_effect=SystemExit)
@patch("missing_ag_updater.cli.update_ide", return_value=True)
@patch("missing_ag_updater.config.load_toml_config", return_value={})
@patch("missing_ag_updater.cli.OS_NAME", "linux")
@patch("sys.argv", ["antigravity-updater", "--ide", "--no-desktop", "--no-apparmor-sandbox"])
def test_cli_override_env_variables(
    mock_toml: MagicMock,
    mock_ide: MagicMock,
    mock_exit: MagicMock,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("ANTIGRAVITY_DESKTOP", "true")
    monkeypatch.setenv("ANTIGRAVITY_NAUTILUS", "false")

    with pytest.raises(SystemExit):
        main()
    mock_ide.assert_called_once_with(
        ANY,
        ANY,
        dry_run=False,
        force=False,
        install_desktop=False,
        install_nautilus=False,
        suid_sandbox=False,
        scope=None,
    )
    mock_exit.assert_called_once_with(0)
