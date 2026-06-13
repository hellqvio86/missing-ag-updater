import os
import subprocess
import tempfile
from typing import Any
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


def test_update_ide_success_linux() -> None:
    import tarfile

    def mock_download_write_tar(url: str, dest_path: str, **kwargs: Any) -> None:
        with tempfile.TemporaryDirectory() as td:
            d = os.path.join(td, "Antigravity IDE", "bin")
            os.makedirs(d)
            with open(os.path.join(d, "antigravity-ide"), "w") as f:
                f.write("launcher content")
            with tarfile.open(dest_path, "w:gz") as tar:
                tar.add(os.path.join(td, "Antigravity IDE"), arcname="Antigravity IDE")

    with patch("missing_ag_updater.updater.OS_NAME", "linux"):
        with patch("missing_ag_updater.updater.get_ide_version", return_value="2.0.3"):
            with patch(
                "missing_ag_updater.updater.fetch_json",
                return_value=[{"version": "2.0.4", "execution_id": "1234"}],
            ):
                with patch("missing_ag_updater.updater.get_running_pids", return_value=[]):
                    with patch(
                        "missing_ag_updater.updater.download_file",
                        side_effect=mock_download_write_tar,
                    ):
                        with tempfile.TemporaryDirectory() as target_ide_dir:
                            launcher = os.path.join(target_ide_dir, "bin_launcher", "ide-launch")
                            res = update_ide(target_ide_dir, launcher, force=True)
                            assert res is True
                            assert os.path.exists(os.path.join(target_ide_dir, "bin", "antigravity-ide"))


def test_update_ide_empty_releases() -> None:
    with patch("missing_ag_updater.updater.get_ide_version", return_value="2.0.3"):
        with patch("missing_ag_updater.updater.fetch_json", return_value=[]):
            assert update_ide("/dummy/ide", None) is False


def test_update_ide_fetch_error() -> None:
    with patch("missing_ag_updater.updater.get_ide_version", return_value="2.0.3"):
        with patch("missing_ag_updater.updater.fetch_json", side_effect=Exception("api down")):
            assert update_ide("/dummy/ide", None) is False


def test_update_ide_running_process_forced() -> None:
    with patch("missing_ag_updater.updater.get_ide_version", return_value="2.0.3"):
        with patch(
            "missing_ag_updater.updater.fetch_json",
            return_value=[{"version": "2.0.4", "execution_id": "1234"}],
        ):
            with patch("missing_ag_updater.updater.get_running_pids", return_value=["1111"]):
                # Force should bypass and proceed (fails later on download URL resolved)
                assert update_ide("/dummy/ide", None, force=True) is False


def test_update_ide_download_url_failure() -> None:
    with patch("missing_ag_updater.updater.get_ide_version", return_value="2.0.3"):
        with patch(
            "missing_ag_updater.updater.fetch_json",
            return_value=[{"version": "2.0.4", "execution_id": "1234"}],
        ):
            with patch("missing_ag_updater.updater.get_running_pids", return_value=[]):
                with patch("missing_ag_updater.updater.get_download_url", return_value=""):
                    assert update_ide("/dummy/ide", None) is False


def test_update_ide_invalid_tarball() -> None:
    # Test when tarball extracts but doesn't have the expected root folder
    import tarfile

    def mock_download_empty_tar(url: str, dest_path: str, **kwargs: Any) -> None:
        with tarfile.open(dest_path, "w:gz"):
            pass  # empty tarball

    with patch("missing_ag_updater.updater.OS_NAME", "linux"):
        with patch("missing_ag_updater.updater.get_ide_version", return_value="2.0.3"):
            with patch(
                "missing_ag_updater.updater.fetch_json",
                return_value=[{"version": "2.0.4", "execution_id": "1234"}],
            ):
                with patch("missing_ag_updater.updater.get_running_pids", return_value=[]):
                    with patch(
                        "missing_ag_updater.updater.download_file",
                        side_effect=mock_download_empty_tar,
                    ):
                        with tempfile.TemporaryDirectory() as target_ide_dir:
                            res = update_ide(target_ide_dir, None)
                            assert res is False


def test_update_hub_success_linux() -> None:
    import tarfile

    def mock_download_write_tar_hub(url: str, dest_path: str, **kwargs: Any) -> None:
        with tempfile.TemporaryDirectory() as td:
            d = os.path.join(td, "Antigravity-x64")
            os.makedirs(d)
            with open(os.path.join(d, "antigravity"), "w") as f:
                f.write("launcher content")
            with tarfile.open(dest_path, "w:gz") as tar:
                tar.add(d, arcname="Antigravity-x64")

    with patch("missing_ag_updater.updater.OS_NAME", "linux"):
        with patch("missing_ag_updater.updater.get_hub_version", return_value="2.1.3"):
            with patch(
                "missing_ag_updater.updater.fetch_json",
                return_value=[{"version": "2.1.4", "execution_id": "1234"}],
            ):
                with patch("missing_ag_updater.updater.get_running_pids", return_value=[]):
                    with patch(
                        "missing_ag_updater.updater.download_file",
                        side_effect=mock_download_write_tar_hub,
                    ):
                        with tempfile.TemporaryDirectory() as target_hub_dir:
                            launcher = os.path.join(target_hub_dir, "bin_launcher", "hub-launch")
                            res = update_hub(target_hub_dir, launcher)
                            assert res is True


def test_update_hub_invalid_tarball() -> None:
    import tarfile

    def mock_download_empty_tar(url: str, dest_path: str, **kwargs: Any) -> None:
        with tarfile.open(dest_path, "w:gz"):
            pass

    with patch("missing_ag_updater.updater.OS_NAME", "linux"):
        with patch("missing_ag_updater.updater.get_hub_version", return_value="2.1.3"):
            with patch(
                "missing_ag_updater.updater.fetch_json",
                return_value=[{"version": "2.1.4", "execution_id": "1234"}],
            ):
                with patch("missing_ag_updater.updater.get_running_pids", return_value=[]):
                    with patch(
                        "missing_ag_updater.updater.download_file",
                        side_effect=mock_download_empty_tar,
                    ):
                        with tempfile.TemporaryDirectory() as target_hub_dir:
                            res = update_hub(target_hub_dir, None)
                            assert res is False


def test_update_cli_success_linux() -> None:
    import tarfile

    def mock_download_write_tar_cli(url: str, dest_path: str, **kwargs: Any) -> None:
        with tempfile.TemporaryDirectory() as td:
            p = os.path.join(td, "antigravity")
            with open(p, "w") as f:
                f.write("cli binary content")
            with tarfile.open(dest_path, "w:gz") as tar:
                tar.add(p, arcname="antigravity")

    with patch("missing_ag_updater.updater.OS_NAME", "linux"):
        with patch("missing_ag_updater.updater.get_cli_version", return_value="1.0.7"):
            with patch(
                "missing_ag_updater.updater.fetch_json",
                return_value={
                    "version": "1.0.8",
                    "url": "https://example.com/agy.tar.gz",
                    "sha512": "expectedhash",
                },
            ):
                with patch("missing_ag_updater.updater.download_file", side_effect=mock_download_write_tar_cli):
                    with patch("missing_ag_updater.updater.compute_sha512", return_value="expectedhash"):
                        with tempfile.TemporaryDirectory() as target_dir:
                            cli_binary = os.path.join(target_dir, "bin", "agy")
                            res = update_cli(cli_binary)
                            assert res is True
                            assert os.path.exists(cli_binary)


def test_update_cli_checksum_mismatch() -> None:
    with patch("missing_ag_updater.updater.OS_NAME", "linux"):
        with patch("missing_ag_updater.updater.get_cli_version", return_value="1.0.7"):
            with patch(
                "missing_ag_updater.updater.fetch_json",
                return_value={
                    "version": "1.0.8",
                    "url": "https://example.com/agy.tar.gz",
                    "sha512": "expectedhash",
                },
            ):
                with patch("missing_ag_updater.updater.download_file"):
                    with patch("missing_ag_updater.updater.compute_sha512", return_value="wronghash"):
                        assert update_cli("/dummy/cli") is False


def test_update_cli_zip_success_windows() -> None:
    import zipfile

    def mock_download_write_zip_cli(url: str, dest_path: str, **kwargs: Any) -> None:
        with tempfile.TemporaryDirectory() as td:
            p = os.path.join(td, "agy.exe")
            with open(p, "w") as f:
                f.write("cli binary exe content")
            with zipfile.ZipFile(dest_path, "w") as z:
                z.write(p, arcname="agy.exe")

    with patch("missing_ag_updater.updater.OS_NAME", "windows"):
        with patch("missing_ag_updater.updater.get_cli_version", return_value="1.0.7"):
            with patch(
                "missing_ag_updater.updater.fetch_json",
                return_value={
                    "version": "1.0.8",
                    "url": "https://example.com/agy.zip",
                    "sha512": None,
                },
            ):
                with patch("missing_ag_updater.updater.download_file", side_effect=mock_download_write_zip_cli):
                    with tempfile.TemporaryDirectory() as target_dir:
                        cli_binary = os.path.join(target_dir, "agy.exe")
                        res = update_cli(cli_binary)
                        assert res is True


def test_update_cli_missing_extracted_binary() -> None:
    import tarfile

    def mock_download_empty_tar(url: str, dest_path: str, **kwargs: Any) -> None:
        with tarfile.open(dest_path, "w:gz"):
            pass

    with patch("missing_ag_updater.updater.OS_NAME", "linux"):
        with patch("missing_ag_updater.updater.get_cli_version", return_value="1.0.7"):
            with patch(
                "missing_ag_updater.updater.fetch_json",
                return_value={
                    "version": "1.0.8",
                    "url": "https://example.com/agy.tar.gz",
                    "sha512": None,
                },
            ):
                with patch("missing_ag_updater.updater.download_file", side_effect=mock_download_empty_tar):
                    assert update_cli("/dummy/cli") is False
