import os
import tempfile
from typing import Any
from unittest.mock import MagicMock, patch

from missing_ag_updater.uninstall import (
    uninstall_cli,
    uninstall_hub,
    uninstall_ide,
)


def test_uninstall_ide_success() -> None:
    with tempfile.TemporaryDirectory() as td:
        ide_dir = os.path.join(td, "opt", "antigravity-ide", "Antigravity-IDE")
        launcher = os.path.join(td, "bin", "antigravity-ide")
        apps_dir = os.path.join(td, "applications")
        icons_dir = os.path.join(td, "icons")
        os.makedirs(ide_dir)
        os.makedirs(os.path.dirname(launcher))
        os.makedirs(apps_dir)
        os.makedirs(icons_dir)
        with open(launcher, "w", encoding="utf-8") as fdesc:
            fdesc.write("#!/bin/sh")
        with open(os.path.join(apps_dir, "antigravity-ide.desktop"), "w", encoding="utf-8") as fdesc:
            fdesc.write("desktop")

        @patch("missing_ag_updater.uninstall.refresh_linux_desktop_caches")
        @patch("missing_ag_updater.uninstall.get_running_pids", return_value=[])
        @patch("missing_ag_updater.uninstall.USER_ICONS_DIR", icons_dir)
        @patch("missing_ag_updater.uninstall.USER_APPLICATIONS_DIR", apps_dir)
        @patch("missing_ag_updater.uninstall.OS_NAME", "linux")
        def _run_test(mock_pids: MagicMock, mock_refresh: MagicMock) -> None:
            res = uninstall_ide(ide_dir=ide_dir, launcher_path=launcher, scope="user", force=True)
            assert res is True
            assert not os.path.exists(ide_dir)
            assert not os.path.exists(launcher)
            mock_refresh.assert_called_once()

        _run_test()


@patch("missing_ag_updater.uninstall.get_running_pids", return_value=["99999"])
def test_uninstall_ide_running_process_aborts(mock_pids: MagicMock) -> None:
    with tempfile.TemporaryDirectory() as td:
        ide_dir = os.path.join(td, "Antigravity-IDE")
        launcher = os.path.join(td, "bin", "antigravity-ide")
        os.makedirs(ide_dir)
        res = uninstall_ide(ide_dir=ide_dir, launcher_path=launcher, force=False)
        assert res is False
        assert os.path.exists(ide_dir)


@patch("missing_ag_updater.uninstall.get_running_pids", return_value=[])
def test_uninstall_ide_dry_run(mock_pids: MagicMock) -> None:
    with tempfile.TemporaryDirectory() as td:
        ide_dir = os.path.join(td, "Antigravity-IDE")
        launcher = os.path.join(td, "bin", "antigravity-ide")
        apps_dir = os.path.join(td, "applications")
        os.makedirs(ide_dir)
        os.makedirs(apps_dir)

        with patch("missing_ag_updater.uninstall.USER_APPLICATIONS_DIR", apps_dir):
            res = uninstall_ide(ide_dir=ide_dir, launcher_path=launcher, scope="user", dry_run=True)
            assert res is True
            assert os.path.exists(ide_dir)


def test_uninstall_hub_success() -> None:
    with tempfile.TemporaryDirectory() as td:
        hub_dir = os.path.join(td, "opt", "antigravity", "Antigravity-x64")
        launcher = os.path.join(td, "bin", "antigravity")
        apps_dir = os.path.join(td, "applications")
        icons_dir = os.path.join(td, "icons")
        os.makedirs(hub_dir)
        os.makedirs(os.path.dirname(launcher))
        os.makedirs(apps_dir)
        os.makedirs(icons_dir)
        with open(launcher, "w", encoding="utf-8") as fdesc:
            fdesc.write("#!/bin/sh")
        with open(os.path.join(apps_dir, "antigravity.desktop"), "w", encoding="utf-8") as fdesc:
            fdesc.write("desktop")

        @patch("missing_ag_updater.uninstall.refresh_linux_desktop_caches")
        @patch("missing_ag_updater.uninstall.get_running_pids", return_value=[])
        @patch("missing_ag_updater.uninstall.USER_ICONS_DIR", icons_dir)
        @patch("missing_ag_updater.uninstall.USER_APPLICATIONS_DIR", apps_dir)
        @patch("missing_ag_updater.uninstall.OS_NAME", "linux")
        def _run_test(mock_pids: MagicMock, mock_refresh: MagicMock) -> None:
            res = uninstall_hub(hub_dir=hub_dir, launcher_path=launcher, scope="user", force=True)
            assert res is True
            assert not os.path.exists(hub_dir)
            assert not os.path.exists(launcher)
            mock_refresh.assert_called_once()

        _run_test()


@patch("missing_ag_updater.uninstall.get_running_pids", return_value=["99999"])
def test_uninstall_hub_running_process_aborts(mock_pids: MagicMock) -> None:
    with tempfile.TemporaryDirectory() as td:
        hub_dir = os.path.join(td, "Antigravity-x64")
        launcher = os.path.join(td, "bin", "antigravity")
        os.makedirs(hub_dir)
        res = uninstall_hub(hub_dir=hub_dir, launcher_path=launcher, force=False)
        assert res is False
        assert os.path.exists(hub_dir)


@patch("missing_ag_updater.uninstall.get_running_pids", return_value=[])
def test_uninstall_cli_success(mock_pids: MagicMock) -> None:
    with tempfile.TemporaryDirectory() as td:
        cli_bin = os.path.join(td, "bin", "agy")
        os.makedirs(os.path.dirname(cli_bin))
        with open(cli_bin, "w", encoding="utf-8") as fdesc:
            fdesc.write("#!/bin/sh")

        res = uninstall_cli(cli_path=cli_bin)
        assert res is True
        assert not os.path.exists(cli_bin)


@patch("missing_ag_updater.uninstall.get_running_pids", return_value=["12345"])
def test_uninstall_cli_running_process_aborts(mock_pids: MagicMock) -> None:
    with tempfile.TemporaryDirectory() as td:
        cli_bin = os.path.join(td, "bin", "agy")
        os.makedirs(os.path.dirname(cli_bin))
        with open(cli_bin, "w", encoding="utf-8") as fdesc:
            fdesc.write("#!/bin/sh")

        res = uninstall_cli(cli_path=cli_bin, force=False)
        assert res is False
        assert os.path.exists(cli_bin)


@patch("missing_ag_updater.uninstall.get_running_pids", return_value=["12345"])
def test_uninstall_cli_running_process_force(mock_pids: MagicMock) -> None:
    with tempfile.TemporaryDirectory() as td:
        cli_bin = os.path.join(td, "bin", "agy")
        os.makedirs(os.path.dirname(cli_bin))
        with open(cli_bin, "w", encoding="utf-8") as fdesc:
            fdesc.write("#!/bin/sh")

        res = uninstall_cli(cli_path=cli_bin, force=True)
        assert res is True
        assert not os.path.exists(cli_bin)


def test_uninstall_cli_nonexistent_returns_true() -> None:
    res = uninstall_cli(cli_path="/nonexistent/bin/agy")
    assert res is True


def test_uninstall_ide_system_scope_and_error(tmp_path: Any) -> None:
    ide_dir = str(tmp_path / "opt" / "antigravity-ide")
    os.makedirs(ide_dir)
    sys_app_dir = str(tmp_path / "sys_apps")
    user_app_dir = str(tmp_path / "user_apps")
    sys_icons_dir = str(tmp_path / "sys_icons")
    sys_naut_dir = str(tmp_path / "sys_nautilus")
    os.makedirs(sys_app_dir)
    os.makedirs(user_app_dir)
    os.makedirs(sys_icons_dir)
    os.makedirs(sys_naut_dir)

    with open(os.path.join(sys_app_dir, "antigravity-ide.desktop"), "w", encoding="utf-8") as fdesc:
        fdesc.write("desktop")
    with open(os.path.join(sys_icons_dir, "antigravity-ide.png"), "w", encoding="utf-8") as fdesc:
        fdesc.write("icon")
    with open(os.path.join(sys_naut_dir, "antigravity-nautilus.py"), "w", encoding="utf-8") as fdesc:
        fdesc.write("nautilus")

    @patch("missing_ag_updater.uninstall.refresh_linux_desktop_caches")
    @patch("missing_ag_updater.uninstall.get_running_pids", return_value=[])
    @patch("missing_ag_updater.uninstall.USER_NAUTILUS_DIR", str(tmp_path / "u_naut"))
    @patch("missing_ag_updater.uninstall.SYSTEM_NAUTILUS_DIR", sys_naut_dir)
    @patch("missing_ag_updater.uninstall.USER_ICONS_DIR", str(tmp_path / "u_icons"))
    @patch("missing_ag_updater.uninstall.SYSTEM_ICONS_DIR", sys_icons_dir)
    @patch("missing_ag_updater.uninstall.USER_APPLICATIONS_DIR", user_app_dir)
    @patch("missing_ag_updater.uninstall.SYSTEM_APPLICATIONS_DIR", sys_app_dir)
    @patch("missing_ag_updater.uninstall.OS_NAME", "linux")
    def _run_test(mock_pids: MagicMock, mock_refresh: MagicMock) -> None:
        res = uninstall_ide(ide_dir=ide_dir, launcher_path=None, scope="system")
        assert res is True
        assert not os.path.exists(ide_dir)

    _run_test()


@patch("missing_ag_updater.uninstall.detect_preferred_ide", return_value=("", None, "system"))
@patch("missing_ag_updater.uninstall.is_path_writable", return_value=False)
@patch("missing_ag_updater.uninstall.get_running_pids", return_value=[])
def test_uninstall_ide_permission_denied(
    mock_pids: MagicMock,
    mock_writable: MagicMock,
    mock_detect: MagicMock,
    tmp_path: Any,
) -> None:
    ide_dir = str(tmp_path / "opt" / "antigravity-ide")
    os.makedirs(ide_dir)
    res = uninstall_ide(ide_dir=ide_dir, launcher_path=None, scope="system")
    assert res is False


@patch("missing_ag_updater.uninstall.detect_preferred_ide", return_value=("", None, "user"))
@patch("missing_ag_updater.uninstall.USER_NAUTILUS_DIR", "/tmp/nonexistent_nautilus")
@patch("missing_ag_updater.uninstall.USER_ICONS_DIR", "/tmp/nonexistent_icons")
@patch("missing_ag_updater.uninstall.USER_APPLICATIONS_DIR", "/tmp/nonexistent_apps")
@patch("missing_ag_updater.uninstall.resolve_existing_ide_dir", return_value="")
@patch("missing_ag_updater.uninstall.get_running_pids", return_value=[])
def test_uninstall_ide_empty_targets(
    mock_pids: MagicMock,
    mock_resolve: MagicMock,
    mock_detect: MagicMock,
) -> None:
    res = uninstall_ide(ide_dir="", launcher_path="", scope="user")
    assert res is True


def test_uninstall_hub_system_scope_and_dry_run(tmp_path: Any) -> None:
    hub_dir = str(tmp_path / "opt" / "antigravity")
    os.makedirs(hub_dir)
    sys_app_dir = str(tmp_path / "sys_apps")
    user_app_dir = str(tmp_path / "user_apps")
    sys_icons_dir = str(tmp_path / "sys_icons")
    os.makedirs(sys_app_dir)
    os.makedirs(user_app_dir)
    os.makedirs(sys_icons_dir)

    with open(os.path.join(sys_app_dir, "antigravity.desktop"), "w", encoding="utf-8") as fdesc:
        fdesc.write("desktop")
    with open(os.path.join(sys_icons_dir, "antigravity.png"), "w", encoding="utf-8") as fdesc:
        fdesc.write("icon")

    @patch("missing_ag_updater.uninstall.refresh_linux_desktop_caches")
    @patch("missing_ag_updater.uninstall.get_running_pids", return_value=[])
    @patch("missing_ag_updater.uninstall.USER_ICONS_DIR", str(tmp_path / "u_icons"))
    @patch("missing_ag_updater.uninstall.SYSTEM_ICONS_DIR", sys_icons_dir)
    @patch("missing_ag_updater.uninstall.USER_APPLICATIONS_DIR", user_app_dir)
    @patch("missing_ag_updater.uninstall.SYSTEM_APPLICATIONS_DIR", sys_app_dir)
    @patch("missing_ag_updater.uninstall.OS_NAME", "linux")
    def _run_test(mock_pids: MagicMock, mock_refresh: MagicMock) -> None:
        dry_res = uninstall_hub(hub_dir=hub_dir, launcher_path=None, scope="system", dry_run=True)
        assert dry_res is True
        assert os.path.exists(hub_dir)

        res = uninstall_hub(hub_dir=hub_dir, launcher_path=None, scope="system")
        assert res is True
        assert not os.path.exists(hub_dir)

    _run_test()


@patch("missing_ag_updater.uninstall.detect_preferred_hub", return_value=("", None, "system"))
@patch("missing_ag_updater.uninstall.is_path_writable", return_value=False)
@patch("missing_ag_updater.uninstall.get_running_pids", return_value=[])
def test_uninstall_hub_permission_denied(
    mock_pids: MagicMock,
    mock_writable: MagicMock,
    mock_detect: MagicMock,
    tmp_path: Any,
) -> None:
    hub_dir = str(tmp_path / "opt" / "antigravity")
    os.makedirs(hub_dir)
    res = uninstall_hub(hub_dir=hub_dir, launcher_path=None, scope="system")
    assert res is False


@patch("missing_ag_updater.uninstall.get_running_pids", return_value=[])
def test_uninstall_cli_permission_denied_and_dry_run(mock_pids: MagicMock, tmp_path: Any) -> None:
    cli_bin = str(tmp_path / "bin" / "agy")
    os.makedirs(str(tmp_path / "bin"))
    with open(cli_bin, "w", encoding="utf-8") as fdesc:
        fdesc.write("#!/bin/sh")

    dry_res = uninstall_cli(cli_path=cli_bin, dry_run=True)
    assert dry_res is True
    assert os.path.exists(cli_bin)

    with patch("missing_ag_updater.uninstall.is_path_writable", return_value=False):
        res = uninstall_cli(cli_path=cli_bin)
        assert res is False

    with patch("os.remove", side_effect=OSError("Cannot delete")):
        fail_res = uninstall_cli(cli_path=cli_bin)
        assert fail_res is False
