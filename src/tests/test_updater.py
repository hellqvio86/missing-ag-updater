import subprocess
from unittest.mock import patch

from missing_ag_updater.updater import (
    get_download_url,
    install_macos_dmg,
    install_windows_exe,
    update_cli,
    update_hub,
    update_ide,
)


def test_get_download_url() -> None:
    # Test IDE Linux
    with patch("missing_ag_updater.updater.OS_NAME", "linux"):
        url = get_download_url("ide", "2.0.4", "12345")
        assert "linux-x64/Antigravity%20IDE.tar.gz" in url

    # Test Hub macOS ARM64
    with patch("missing_ag_updater.updater.OS_NAME", "darwin"):
        with patch("missing_ag_updater.updater.ARCH_NAME", "arm64"):
            url = get_download_url("hub", "2.1.4", "67890")
            assert "darwin-arm/Antigravity.dmg" in url

    # Test Hub macOS X64
    with patch("missing_ag_updater.updater.OS_NAME", "darwin"):
        with patch("missing_ag_updater.updater.ARCH_NAME", "x64"):
            url = get_download_url("hub", "2.1.4", "67890")
            assert "darwin-x64/Antigravity.dmg" in url

    # Test IDE Windows
    with patch("missing_ag_updater.updater.OS_NAME", "windows"):
        url = get_download_url("ide", "2.0.4", "12345")
        assert "windows-x64/Antigravity%20IDE.exe" in url


def test_install_windows_exe() -> None:
    with patch("subprocess.run") as mock_run:
        mock_run.return_value = subprocess.CompletedProcess(args=[], returncode=0)
        assert install_windows_exe("dummy.exe") is True
        mock_run.assert_called_once_with(["dummy.exe", "/S"], check=True)

    with patch("subprocess.run", side_effect=Exception("error")):
        assert install_windows_exe("dummy.exe") is False


def test_install_macos_dmg() -> None:
    with patch("tempfile.mkdtemp", return_value="/tmp/mock_mount"):
        with patch("subprocess.run") as mock_run:
            with patch("os.listdir", return_value=["Antigravity IDE.app"]):
                with patch("os.path.exists", return_value=True):
                    with patch("shutil.rmtree") as mock_rm:
                        with patch("shutil.copytree") as mock_cp:
                            with patch("os.rmdir") as mock_rmdir:
                                mock_run.return_value = subprocess.CompletedProcess(args=[], returncode=0)
                                res = install_macos_dmg("dummy.dmg", "/Applications/Target.app")
                                assert res is True
                                mock_rm.assert_called_once_with("/Applications/Target.app")
                                mock_cp.assert_called_once_with(
                                    "/tmp/mock_mount/Antigravity IDE.app",
                                    "/Applications/Target.app",
                                    symlinks=True,
                                )
                                mock_rmdir.assert_called_once_with("/tmp/mock_mount")


def test_update_ide_up_to_date() -> None:
    with patch("missing_ag_updater.updater.get_ide_version", return_value="2.0.4"):
        with patch(
            "missing_ag_updater.updater.fetch_json",
            return_value=[{"version": "2.0.4", "execution_id": "1234"}],
        ):
            res = update_ide("/dummy/ide", None)
            assert res is True


def test_update_ide_dry_run() -> None:
    with patch("missing_ag_updater.updater.get_ide_version", return_value="2.0.3"):
        with patch(
            "missing_ag_updater.updater.fetch_json",
            return_value=[{"version": "2.0.4", "execution_id": "1234"}],
        ):
            res = update_ide("/dummy/ide", None, dry_run=True)
            assert res is True


def test_update_ide_running_process_aborts() -> None:
    with patch("missing_ag_updater.updater.get_ide_version", return_value="2.0.3"):
        with patch(
            "missing_ag_updater.updater.fetch_json",
            return_value=[{"version": "2.0.4", "execution_id": "1234"}],
        ):
            with patch("missing_ag_updater.updater.get_running_pids", return_value=["1111", "2222"]):
                res = update_ide("/dummy/ide", None)
                assert res is False


def test_update_hub_up_to_date() -> None:
    with patch("missing_ag_updater.updater.get_hub_version", return_value="2.1.4"):
        with patch(
            "missing_ag_updater.updater.fetch_json",
            return_value=[{"version": "2.1.4", "execution_id": "1234"}],
        ):
            res = update_hub("/dummy/hub", None)
            assert res is True


def test_update_cli_up_to_date() -> None:
    with patch("missing_ag_updater.updater.get_cli_version", return_value="1.0.8"):
        with patch(
            "missing_ag_updater.updater.fetch_json",
            return_value={
                "version": "1.0.8",
                "url": "https://example.com/agy.tar.gz",
                "sha512": "hash",
            },
        ):
            res = update_cli("/dummy/cli")
            assert res is True
