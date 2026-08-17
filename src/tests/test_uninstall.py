import os
import tempfile
from unittest.mock import patch

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
        with open(launcher, "w") as f:
            f.write("#!/bin/sh")
        with open(os.path.join(apps_dir, "antigravity-ide.desktop"), "w") as f:
            f.write("desktop")

        with patch("missing_ag_updater.uninstall.OS_NAME", "linux"):
            with patch("missing_ag_updater.uninstall.USER_APPLICATIONS_DIR", apps_dir):
                with patch("missing_ag_updater.uninstall.USER_ICONS_DIR", icons_dir):
                    with patch("missing_ag_updater.uninstall.get_running_pids", return_value=[]):
                        with patch("missing_ag_updater.uninstall.refresh_linux_desktop_caches") as mock_refresh:
                            res = uninstall_ide(ide_dir=ide_dir, launcher_path=launcher, scope="user", force=True)
                            assert res is True
                            assert not os.path.exists(ide_dir)
                            assert not os.path.exists(launcher)
                            mock_refresh.assert_called_once()


def test_uninstall_ide_running_process_aborts() -> None:
    with tempfile.TemporaryDirectory() as td:
        ide_dir = os.path.join(td, "Antigravity-IDE")
        launcher = os.path.join(td, "bin", "antigravity-ide")
        os.makedirs(ide_dir)

        with patch("missing_ag_updater.uninstall.get_running_pids", return_value=["99999"]):
            res = uninstall_ide(ide_dir=ide_dir, launcher_path=launcher, force=False)
            assert res is False
            assert os.path.exists(ide_dir)


def test_uninstall_ide_dry_run() -> None:
    with tempfile.TemporaryDirectory() as td:
        ide_dir = os.path.join(td, "Antigravity-IDE")
        launcher = os.path.join(td, "bin", "antigravity-ide")
        apps_dir = os.path.join(td, "applications")
        os.makedirs(ide_dir)
        os.makedirs(apps_dir)

        with patch("missing_ag_updater.uninstall.USER_APPLICATIONS_DIR", apps_dir):
            with patch("missing_ag_updater.uninstall.get_running_pids", return_value=[]):
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
        with open(launcher, "w") as f:
            f.write("#!/bin/sh")
        with open(os.path.join(apps_dir, "antigravity.desktop"), "w") as f:
            f.write("desktop")

        with patch("missing_ag_updater.uninstall.OS_NAME", "linux"):
            with patch("missing_ag_updater.uninstall.USER_APPLICATIONS_DIR", apps_dir):
                with patch("missing_ag_updater.uninstall.USER_ICONS_DIR", icons_dir):
                    with patch("missing_ag_updater.uninstall.get_running_pids", return_value=[]):
                        with patch("missing_ag_updater.uninstall.refresh_linux_desktop_caches") as mock_refresh:
                            res = uninstall_hub(hub_dir=hub_dir, launcher_path=launcher, scope="user", force=True)
                            assert res is True
                            assert not os.path.exists(hub_dir)
                            assert not os.path.exists(launcher)
                            mock_refresh.assert_called_once()


def test_uninstall_hub_running_process_aborts() -> None:
    with tempfile.TemporaryDirectory() as td:
        hub_dir = os.path.join(td, "Antigravity-x64")
        launcher = os.path.join(td, "bin", "antigravity")
        os.makedirs(hub_dir)

        with patch("missing_ag_updater.uninstall.get_running_pids", return_value=["99999"]):
            res = uninstall_hub(hub_dir=hub_dir, launcher_path=launcher, force=False)
            assert res is False
            assert os.path.exists(hub_dir)


def test_uninstall_cli_success() -> None:
    with tempfile.TemporaryDirectory() as td:
        cli_bin = os.path.join(td, "bin", "agy")
        os.makedirs(os.path.dirname(cli_bin))
        with open(cli_bin, "w") as f:
            f.write("#!/bin/sh")

        res = uninstall_cli(cli_path=cli_bin)
        assert res is True
        assert not os.path.exists(cli_bin)


def test_uninstall_cli_nonexistent_returns_true() -> None:
    res = uninstall_cli(cli_path="/nonexistent/bin/agy")
    assert res is True
