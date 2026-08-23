import os
import shutil
import subprocess
import tarfile
import tempfile
import zipfile
from typing import Any
from unittest.mock import MagicMock, patch

from missing_ag_updater.updater import (
    get_download_url,
    install_macos_dmg,
    install_windows_exe,
    update_cli,
    update_hub,
    update_ide,
)

SAMPLE_SHA512 = "a" * 128
SAMPLE_SHA256 = "b" * 64
SAMPLE_CLI_URL = "https://dl.google.com/release2/agy.tar.gz"
SAMPLE_CLI_ZIP_URL = "https://dl.google.com/release2/agy.zip"


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


@patch("subprocess.run")
def test_install_windows_exe_success(mock_run: MagicMock) -> None:
    mock_run.return_value = subprocess.CompletedProcess(args=[], returncode=0)
    assert install_windows_exe("dummy.exe") is True
    mock_run.assert_called_once_with(["dummy.exe", "/S"], check=True)


@patch("subprocess.run", side_effect=Exception("error"))
def test_install_windows_exe_failure(mock_run: MagicMock) -> None:
    assert install_windows_exe("dummy.exe") is False


@patch("os.rmdir")
@patch("shutil.copytree")
@patch("shutil.rmtree")
@patch("os.path.exists", return_value=True)
@patch("os.listdir", return_value=["Antigravity IDE.app"])
@patch("subprocess.run")
@patch("tempfile.mkdtemp", return_value="/tmp/mock_mount")
def test_install_macos_dmg(
    mock_mkdtemp: MagicMock,
    mock_run: MagicMock,
    mock_listdir: MagicMock,
    mock_exists: MagicMock,
    mock_rm: MagicMock,
    mock_cp: MagicMock,
    mock_rmdir: MagicMock,
) -> None:
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


@patch("missing_ag_updater.updater.fetch_json", return_value=[{"version": "2.0.4", "execution_id": "1234"}])
@patch("missing_ag_updater.updater.get_ide_version", return_value="2.0.4")
def test_update_ide_up_to_date(mock_ver: MagicMock, mock_fetch: MagicMock) -> None:
    res = update_ide("/dummy/ide", None)
    assert res is True


@patch("missing_ag_updater.updater.fetch_json", return_value=[{"version": "2.0.4", "execution_id": "1234"}])
@patch("missing_ag_updater.updater.get_ide_version", return_value="2.0.3")
def test_update_ide_dry_run(mock_ver: MagicMock, mock_fetch: MagicMock) -> None:
    res = update_ide("/dummy/ide", None, dry_run=True)
    assert res is True


@patch("missing_ag_updater.updater.get_running_pids", return_value=["1111", "2222"])
@patch("missing_ag_updater.updater.fetch_json", return_value=[{"version": "2.0.4", "execution_id": "1234"}])
@patch("missing_ag_updater.updater.get_ide_version", return_value="2.0.3")
def test_update_ide_running_process_aborts(
    mock_ver: MagicMock,
    mock_fetch: MagicMock,
    mock_pids: MagicMock,
) -> None:
    res = update_ide("/dummy/ide", None)
    assert res is False


@patch("missing_ag_updater.updater.fetch_json", return_value=[{"version": "2.1.4", "execution_id": "1234"}])
@patch("missing_ag_updater.updater.get_hub_version", return_value="2.1.4")
def test_update_hub_up_to_date(mock_ver: MagicMock, mock_fetch: MagicMock) -> None:
    res = update_hub("/dummy/hub", None)
    assert res is True


@patch(
    "missing_ag_updater.updater.fetch_json",
    return_value={
        "version": "1.0.8",
        "url": SAMPLE_CLI_URL,
        "sha512": SAMPLE_SHA512,
    },
)
@patch("missing_ag_updater.updater.get_cli_version", return_value="1.0.8")
def test_update_cli_up_to_date(mock_ver: MagicMock, mock_fetch: MagicMock) -> None:
    res = update_cli("/dummy/cli")
    assert res is True


def test_update_ide_success_linux() -> None:
    def mock_download_write_tar(url: str, dest_path: str, **kwargs: Any) -> None:
        with tempfile.TemporaryDirectory() as td:
            bin_dir = os.path.join(td, "Antigravity IDE", "bin")
            os.makedirs(bin_dir)
            with open(os.path.join(bin_dir, "antigravity-ide"), "w", encoding="utf-8") as fdesc:
                fdesc.write("launcher content")
            with tarfile.open(dest_path, "w:gz") as tar:
                tar.add(os.path.join(td, "Antigravity IDE"), arcname="Antigravity IDE")

    @patch("missing_ag_updater.updater.install_ide_nautilus")
    @patch("missing_ag_updater.updater.install_ide_desktop")
    @patch("missing_ag_updater.updater.download_file", side_effect=mock_download_write_tar)
    @patch("missing_ag_updater.updater.get_running_pids", return_value=[])
    @patch("missing_ag_updater.updater.fetch_json", return_value=[{"version": "2.0.4", "execution_id": "1234"}])
    @patch("missing_ag_updater.updater.get_ide_version", return_value="2.0.3")
    @patch("missing_ag_updater.updater.OS_NAME", "linux")
    def _run_test(
        mock_ver: MagicMock,
        mock_fetch: MagicMock,
        mock_pids: MagicMock,
        mock_dl: MagicMock,
        mock_dt: MagicMock,
        mock_naut: MagicMock,
    ) -> None:
        with tempfile.TemporaryDirectory() as target_ide_dir:
            launcher = os.path.join(target_ide_dir, "bin_launcher", "ide-launch")
            res = update_ide(target_ide_dir, launcher, force=True)
            assert res is True
            assert os.path.exists(os.path.join(target_ide_dir, "bin", "antigravity-ide"))
            mock_dt.assert_called_once_with(ide_dir=target_ide_dir, launcher_path=launcher, scope="user")
            mock_naut.assert_called_once_with(ide_dir=target_ide_dir, launcher_path=launcher, scope="user")

    _run_test()


def test_update_ide_skips_legacy_cleanup_on_non_sandbox_distro() -> None:
    def mock_download_write_tar(url: str, dest_path: str, **kwargs: Any) -> None:
        with tempfile.TemporaryDirectory() as td:
            bin_dir = os.path.join(td, "Antigravity IDE", "bin")
            os.makedirs(bin_dir)
            with open(os.path.join(bin_dir, "antigravity-ide"), "w", encoding="utf-8") as fdesc:
                fdesc.write("launcher content")
            with tarfile.open(dest_path, "w:gz") as tar:
                tar.add(os.path.join(td, "Antigravity IDE"), arcname="Antigravity IDE")

    original_rmtree = shutil.rmtree

    def record_rmtree(path: str, *args: Any, **kwargs: Any) -> None:
        if path.endswith("Antigravity IDE"):
            raise AssertionError("legacy directory should not be removed")
        return original_rmtree(path, *args, **kwargs)

    @patch("missing_ag_updater.updater.install_ide_nautilus")
    @patch("missing_ag_updater.updater.install_ide_desktop")
    @patch("missing_ag_updater.updater.shutil.rmtree", side_effect=record_rmtree)
    @patch("missing_ag_updater.updater.is_ubuntu_sandbox_distro", return_value=False)
    @patch("missing_ag_updater.updater.download_file", side_effect=mock_download_write_tar)
    @patch("missing_ag_updater.updater.get_running_pids", return_value=[])
    @patch("missing_ag_updater.updater.fetch_json", return_value=[{"version": "2.0.4", "execution_id": "1234"}])
    @patch("missing_ag_updater.updater.get_ide_version", return_value="2.0.3")
    @patch("missing_ag_updater.updater.OS_NAME", "linux")
    def _run_test(
        mock_ver: MagicMock,
        mock_fetch: MagicMock,
        mock_pids: MagicMock,
        mock_dl: MagicMock,
        mock_distro: MagicMock,
        mock_rm: MagicMock,
        mock_install_desktop: MagicMock,
        mock_naut: MagicMock,
    ) -> None:
        with tempfile.TemporaryDirectory() as root:
            target_ide_dir = os.path.join(root, "target-ide")
            legacy_ide_dir = os.path.join(root, "Antigravity IDE")
            os.makedirs(legacy_ide_dir)
            res = update_ide(target_ide_dir, None, force=True)
            assert res is True
            mock_install_desktop.assert_called_once()

    _run_test()


def test_update_ide_checksum_verification() -> None:
    def mock_download(url: str, dest_path: str, **kwargs: Any) -> None:
        with open(dest_path, "wb") as fdesc:
            fdesc.write(b"mock payload")

    # Mismatch failure
    @patch("missing_ag_updater.updater.compute_sha512", return_value="different_hash")
    @patch("missing_ag_updater.updater.download_file", side_effect=mock_download)
    @patch("missing_ag_updater.updater.get_running_pids", return_value=[])
    @patch(
        "missing_ag_updater.updater.fetch_json",
        return_value=[{"version": "2.0.4", "execution_id": "1234", "sha512": SAMPLE_SHA512}],
    )
    @patch("missing_ag_updater.updater.get_ide_version", return_value="2.0.3")
    def _test_mismatch(
        mock_ver: MagicMock, mock_fetch: MagicMock, mock_pids: MagicMock, mock_dl: MagicMock, mock_sha: MagicMock
    ) -> None:
        res = update_ide("/dummy/ide", None, force=True)
        assert res is False

    _test_mismatch()


def test_update_hub_checksum_verification() -> None:
    def mock_download(url: str, dest_path: str, **kwargs: Any) -> None:
        with open(dest_path, "wb") as fdesc:
            fdesc.write(b"mock payload")

    @patch("missing_ag_updater.updater.compute_sha256", return_value="different_hash")
    @patch("missing_ag_updater.updater.download_file", side_effect=mock_download)
    @patch("missing_ag_updater.updater.get_running_pids", return_value=[])
    @patch(
        "missing_ag_updater.updater.fetch_json",
        return_value=[{"version": "2.1.4", "execution_id": "1234", "sha256": SAMPLE_SHA256}],
    )
    @patch("missing_ag_updater.updater.get_hub_version", return_value="2.1.3")
    def _test_mismatch(
        mock_ver: MagicMock, mock_fetch: MagicMock, mock_pids: MagicMock, mock_dl: MagicMock, mock_sha: MagicMock
    ) -> None:
        res = update_hub("/dummy/hub", None, force=True)
        assert res is False

    _test_mismatch()


@patch("missing_ag_updater.updater.fetch_json", return_value=[])
@patch("missing_ag_updater.updater.get_ide_version", return_value="2.0.3")
def test_update_ide_empty_releases(mock_ver: MagicMock, mock_fetch: MagicMock) -> None:
    assert update_ide("/dummy/ide", None) is False


@patch("missing_ag_updater.updater.fetch_json", side_effect=Exception("api down"))
@patch("missing_ag_updater.updater.get_ide_version", return_value="2.0.3")
def test_update_ide_fetch_error(mock_ver: MagicMock, mock_fetch: MagicMock) -> None:
    assert update_ide("/dummy/ide", None) is False


@patch("missing_ag_updater.updater.get_running_pids", return_value=["1111"])
@patch("missing_ag_updater.updater.fetch_json", return_value=[{"version": "2.0.4", "execution_id": "1234"}])
@patch("missing_ag_updater.updater.get_ide_version", return_value="2.0.3")
def test_update_ide_running_process_forced(
    mock_ver: MagicMock,
    mock_fetch: MagicMock,
    mock_pids: MagicMock,
) -> None:
    with patch("missing_ag_updater.updater.download_file", side_effect=Exception("Stop after check")):
        res = update_ide("/dummy/ide", None, force=True)
        assert res is False


@patch("missing_ag_updater.updater.get_running_pids", return_value=[])
@patch("missing_ag_updater.updater.fetch_json", return_value=[{"version": "2.0.4", "execution_id": "1234"}])
@patch("missing_ag_updater.updater.get_ide_version", return_value="2.0.3")
def test_update_ide_download_failure(
    mock_ver: MagicMock,
    mock_fetch: MagicMock,
    mock_pids: MagicMock,
) -> None:
    with patch("missing_ag_updater.updater.download_file", side_effect=RuntimeError("download fail")):
        assert update_ide("/dummy/ide", None) is False


def test_update_hub_success_linux() -> None:
    def mock_download_write_tar_hub(url: str, dest_path: str, **kwargs: Any) -> None:
        with tempfile.TemporaryDirectory() as td:
            hub_dir = os.path.join(td, "Antigravity-x64")
            os.makedirs(hub_dir)
            with open(os.path.join(hub_dir, "antigravity"), "w", encoding="utf-8") as fdesc:
                fdesc.write("hub launcher")
            with tarfile.open(dest_path, "w:gz") as tar:
                tar.add(hub_dir, arcname="Antigravity-x64")

    @patch("missing_ag_updater.updater.install_hub_desktop")
    @patch("missing_ag_updater.updater.download_file", side_effect=mock_download_write_tar_hub)
    @patch("missing_ag_updater.updater.get_running_pids", return_value=[])
    @patch("missing_ag_updater.updater.fetch_json", return_value=[{"version": "2.1.4", "execution_id": "1234"}])
    @patch("missing_ag_updater.updater.get_hub_version", return_value="2.1.3")
    @patch("missing_ag_updater.updater.OS_NAME", "linux")
    def _run_test(
        mock_ver: MagicMock,
        mock_fetch: MagicMock,
        mock_pids: MagicMock,
        mock_dl: MagicMock,
        mock_dt: MagicMock,
    ) -> None:
        with tempfile.TemporaryDirectory() as target_hub_dir:
            launcher = os.path.join(target_hub_dir, "bin", "antigravity")
            res = update_hub(target_hub_dir, launcher, force=True)
            assert res is True
            assert os.path.exists(os.path.join(target_hub_dir, "antigravity"))
            mock_dt.assert_called_once_with(hub_dir=target_hub_dir, launcher_path=launcher, scope="user")

    _run_test()


def test_update_hub_invalid_tarball() -> None:
    def mock_download_empty_tar(url: str, dest_path: str, **kwargs: Any) -> None:
        with tarfile.open(dest_path, "w:gz"):
            pass

    @patch("missing_ag_updater.updater.download_file", side_effect=mock_download_empty_tar)
    @patch("missing_ag_updater.updater.get_running_pids", return_value=[])
    @patch("missing_ag_updater.updater.fetch_json", return_value=[{"version": "2.1.4", "execution_id": "1234"}])
    @patch("missing_ag_updater.updater.get_hub_version", return_value="2.1.3")
    @patch("missing_ag_updater.updater.OS_NAME", "linux")
    def _run_test(
        mock_ver: MagicMock,
        mock_fetch: MagicMock,
        mock_pids: MagicMock,
        mock_dl: MagicMock,
    ) -> None:
        with tempfile.TemporaryDirectory() as target_hub_dir:
            res = update_hub(target_hub_dir, None)
            assert res is False

    _run_test()


def test_update_cli_success_linux() -> None:
    def mock_download_write_tar_cli(url: str, dest_path: str, **kwargs: Any) -> None:
        with tempfile.TemporaryDirectory() as td:
            binary_path = os.path.join(td, "antigravity")
            with open(binary_path, "w", encoding="utf-8") as fdesc:
                fdesc.write("cli binary content")
            with tarfile.open(dest_path, "w:gz") as tar:
                tar.add(binary_path, arcname="antigravity")

    @patch("missing_ag_updater.updater.compute_sha512", return_value=SAMPLE_SHA512)
    @patch("missing_ag_updater.updater.download_file", side_effect=mock_download_write_tar_cli)
    @patch(
        "missing_ag_updater.updater.fetch_json",
        return_value={
            "version": "1.0.8",
            "url": SAMPLE_CLI_URL,
            "sha512": SAMPLE_SHA512,
        },
    )
    @patch("missing_ag_updater.updater.get_cli_version", return_value="1.0.7")
    @patch("missing_ag_updater.updater.OS_NAME", "linux")
    def _run_test(
        mock_ver: MagicMock,
        mock_fetch: MagicMock,
        mock_dl: MagicMock,
        mock_sha: MagicMock,
    ) -> None:
        with tempfile.TemporaryDirectory() as target_dir:
            cli_binary = os.path.join(target_dir, "bin", "agy")
            res = update_cli(cli_binary)
            assert res is True
            assert os.path.exists(cli_binary)

    _run_test()


@patch("missing_ag_updater.updater.compute_sha512", return_value="f" * 128)
@patch("missing_ag_updater.updater.download_file")
@patch(
    "missing_ag_updater.updater.fetch_json",
    return_value={
        "version": "1.0.8",
        "url": SAMPLE_CLI_URL,
        "sha512": SAMPLE_SHA512,
    },
)
@patch("missing_ag_updater.updater.get_cli_version", return_value="1.0.7")
@patch("missing_ag_updater.updater.OS_NAME", "linux")
def test_update_cli_checksum_mismatch(
    mock_ver: MagicMock,
    mock_fetch: MagicMock,
    mock_dl: MagicMock,
    mock_sha: MagicMock,
) -> None:
    assert update_cli("/dummy/cli") is False


def test_update_cli_missing_sha512_rejected() -> None:
    @patch(
        "missing_ag_updater.updater.fetch_json",
        return_value={
            "version": "1.0.8",
            "url": SAMPLE_CLI_URL,
            "sha512": None,
        },
    )
    @patch("missing_ag_updater.updater.get_cli_version", return_value="1.0.7")
    def _test_missing(mock_ver: MagicMock, mock_fetch: MagicMock) -> None:
        assert update_cli("/dummy/cli") is False

    _test_missing()


def test_update_cli_zip_success_windows() -> None:
    def mock_download_write_zip_cli(url: str, dest_path: str, **kwargs: Any) -> None:
        with tempfile.TemporaryDirectory() as td:
            binary_path = os.path.join(td, "agy.exe")
            with open(binary_path, "w", encoding="utf-8") as fdesc:
                fdesc.write("cli binary exe content")
            with zipfile.ZipFile(dest_path, "w") as z:
                z.write(binary_path, arcname="agy.exe")

    @patch("missing_ag_updater.updater.compute_sha512", return_value=SAMPLE_SHA512)
    @patch("missing_ag_updater.updater.download_file", side_effect=mock_download_write_zip_cli)
    @patch(
        "missing_ag_updater.updater.fetch_json",
        return_value={
            "version": "1.0.8",
            "url": SAMPLE_CLI_ZIP_URL,
            "sha512": SAMPLE_SHA512,
        },
    )
    @patch("missing_ag_updater.updater.get_cli_version", return_value="1.0.7")
    @patch("missing_ag_updater.updater.OS_NAME", "windows")
    def _run_test(
        mock_ver: MagicMock,
        mock_fetch: MagicMock,
        mock_dl: MagicMock,
        mock_sha: MagicMock,
    ) -> None:
        with tempfile.TemporaryDirectory() as target_dir:
            cli_binary = os.path.join(target_dir, "agy.exe")
            res = update_cli(cli_binary)
            assert res is True

    _run_test()


def test_update_cli_missing_extracted_binary() -> None:
    def mock_download_empty_tar(url: str, dest_path: str, **kwargs: Any) -> None:
        with tarfile.open(dest_path, "w:gz"):
            pass

    @patch("missing_ag_updater.updater.compute_sha512", return_value=SAMPLE_SHA512)
    @patch("missing_ag_updater.updater.download_file", side_effect=mock_download_empty_tar)
    @patch(
        "missing_ag_updater.updater.fetch_json",
        return_value={
            "version": "1.0.8",
            "url": SAMPLE_CLI_URL,
            "sha512": SAMPLE_SHA512,
        },
    )
    @patch("missing_ag_updater.updater.get_cli_version", return_value="1.0.7")
    @patch("missing_ag_updater.updater.OS_NAME", "linux")
    def _run_test(
        mock_ver: MagicMock,
        mock_fetch: MagicMock,
        mock_dl: MagicMock,
        mock_sha: MagicMock,
    ) -> None:
        assert update_cli("/dummy/cli") is False

    _run_test()


@patch("subprocess.run", side_effect=Exception("hdiutil error"))
@patch("tempfile.mkdtemp", return_value="/tmp/mock_mount")
def test_install_macos_dmg_mount_error(mock_mkdtemp: MagicMock, mock_run: MagicMock) -> None:
    assert install_macos_dmg("dummy.dmg", "/Applications/Target.app") is False


@patch("os.listdir", return_value=["SomeOtherFile.txt"])
@patch("subprocess.run")
@patch("tempfile.mkdtemp", return_value="/tmp/mock_mount")
def test_install_macos_dmg_no_app_bundle(
    mock_mkdtemp: MagicMock,
    mock_run: MagicMock,
    mock_listdir: MagicMock,
) -> None:
    mock_run.return_value = subprocess.CompletedProcess(args=[], returncode=0)
    assert install_macos_dmg("dummy.dmg", "/Applications/Target.app") is False


@patch("missing_ag_updater.updater.is_path_writable", return_value=False)
@patch("missing_ag_updater.updater.get_running_pids", return_value=[])
@patch("missing_ag_updater.updater.fetch_json", return_value=[{"version": "2.0.4", "execution_id": "1"}])
@patch("missing_ag_updater.updater.get_ide_version", return_value="2.0.3")
def test_update_ide_permission_denied(
    mock_ver: MagicMock,
    mock_fetch: MagicMock,
    mock_pids: MagicMock,
    mock_writable: MagicMock,
) -> None:
    assert update_ide("/opt/antigravity-ide", None) is False


@patch("missing_ag_updater.updater.is_path_writable", return_value=False)
@patch("missing_ag_updater.updater.get_running_pids", return_value=[])
@patch("missing_ag_updater.updater.fetch_json", return_value=[{"version": "2.0.4", "execution_id": "1"}])
@patch("missing_ag_updater.updater.get_hub_version", return_value="2.0.3")
def test_update_hub_permission_denied(
    mock_ver: MagicMock,
    mock_fetch: MagicMock,
    mock_pids: MagicMock,
    mock_writable: MagicMock,
) -> None:
    assert update_hub("/opt/antigravity", None) is False


@patch("missing_ag_updater.updater.is_path_writable", return_value=False)
@patch("missing_ag_updater.updater.get_running_pids", return_value=[])
@patch(
    "missing_ag_updater.updater.fetch_json",
    return_value={"version": "1.0.8", "url": SAMPLE_CLI_URL, "sha512": SAMPLE_SHA512},
)
@patch("missing_ag_updater.updater.get_cli_version", return_value="1.0.7")
def test_update_cli_permission_denied(
    mock_ver: MagicMock,
    mock_fetch: MagicMock,
    mock_pids: MagicMock,
    mock_writable: MagicMock,
) -> None:
    assert update_cli("/usr/local/bin/agy") is False


@patch("missing_ag_updater.updater.fetch_json", return_value=[])
@patch("missing_ag_updater.updater.get_hub_version", return_value="2.0.3")
def test_update_hub_empty_releases(mock_ver: MagicMock, mock_fetch: MagicMock) -> None:
    assert update_hub("/dummy/hub", None) is False


@patch("missing_ag_updater.updater.fetch_json", return_value=None)
@patch("missing_ag_updater.updater.get_cli_version", return_value="1.0.7")
def test_update_cli_invalid_manifest(mock_ver: MagicMock, mock_fetch: MagicMock) -> None:
    assert update_cli("/dummy/cli") is False


@patch("missing_ag_updater.updater.get_running_pids", return_value=["1111"])
@patch("missing_ag_updater.updater.fetch_json", return_value=[{"version": "2.0.4", "execution_id": "1234"}])
@patch("missing_ag_updater.updater.get_hub_version", return_value="2.0.3")
def test_update_hub_running_process_aborts(
    mock_ver: MagicMock,
    mock_fetch: MagicMock,
    mock_pids: MagicMock,
) -> None:
    res = update_hub("/dummy/hub", None)
    assert res is False


def test_update_ide_symlink_failure(tmp_path: Any) -> None:
    def mock_download_write_tar(url: str, dest_path: str, **kwargs: Any) -> None:
        with tempfile.TemporaryDirectory() as td:
            bin_dir = os.path.join(td, "Antigravity IDE", "bin")
            os.makedirs(bin_dir)
            with open(os.path.join(bin_dir, "antigravity-ide"), "w", encoding="utf-8") as fdesc:
                fdesc.write("launcher content")
            with tarfile.open(dest_path, "w:gz") as tar:
                tar.add(os.path.join(td, "Antigravity IDE"), arcname="Antigravity IDE")

    @patch("missing_ag_updater.updater.update_symlink", return_value=False)
    @patch("missing_ag_updater.updater.download_file", side_effect=mock_download_write_tar)
    @patch("missing_ag_updater.updater.get_running_pids", return_value=[])
    @patch("missing_ag_updater.updater.fetch_json", return_value=[{"version": "2.0.4", "execution_id": "1234"}])
    @patch("missing_ag_updater.updater.get_ide_version", return_value="2.0.3")
    @patch("missing_ag_updater.updater.OS_NAME", "linux")
    def _run_test(
        mock_ver: MagicMock,
        mock_fetch: MagicMock,
        mock_pids: MagicMock,
        mock_dl: MagicMock,
        mock_symlink: MagicMock,
    ) -> None:
        target_ide = str(tmp_path / "ide")
        launcher = str(tmp_path / "bin" / "antigravity-ide")
        res = update_ide(target_ide, launcher, force=True)
        assert res is False

    _run_test()


def test_update_hub_symlink_failure(tmp_path: Any) -> None:
    def mock_download_write_tar_hub(url: str, dest_path: str, **kwargs: Any) -> None:
        with tempfile.TemporaryDirectory() as td:
            hub_dir = os.path.join(td, "Antigravity-x64")
            os.makedirs(hub_dir)
            with open(os.path.join(hub_dir, "antigravity"), "w", encoding="utf-8") as fdesc:
                fdesc.write("hub launcher")
            with tarfile.open(dest_path, "w:gz") as tar:
                tar.add(hub_dir, arcname="Antigravity-x64")

    @patch("missing_ag_updater.updater.update_symlink", return_value=False)
    @patch("missing_ag_updater.updater.download_file", side_effect=mock_download_write_tar_hub)
    @patch("missing_ag_updater.updater.get_running_pids", return_value=[])
    @patch("missing_ag_updater.updater.fetch_json", return_value=[{"version": "2.1.4", "execution_id": "1234"}])
    @patch("missing_ag_updater.updater.get_hub_version", return_value="2.1.3")
    @patch("missing_ag_updater.updater.OS_NAME", "linux")
    def _run_test(
        mock_ver: MagicMock,
        mock_fetch: MagicMock,
        mock_pids: MagicMock,
        mock_dl: MagicMock,
        mock_symlink: MagicMock,
    ) -> None:
        target_hub = str(tmp_path / "hub")
        launcher = str(tmp_path / "bin" / "antigravity")
        res = update_hub(target_hub, launcher, force=True)
        assert res is False

    _run_test()


def test_update_ide_downgrade_protection() -> None:
    @patch(
        "missing_ag_updater.updater.fetch_json",
        return_value=[{"version": "2.0.3", "execution_id": "1234"}],
    )
    @patch("missing_ag_updater.updater.get_ide_version", return_value="2.0.4")
    def _run_test(mock_ver: MagicMock, mock_fetch: MagicMock) -> None:
        # Local version 2.0.4 is newer than server version 2.0.3 -> skip update
        res = update_ide("/dummy/ide", None, force=False)
        assert res is True

    _run_test()


def test_update_ide_selects_highest_version_when_out_of_order() -> None:
    @patch(
        "missing_ag_updater.updater.fetch_json",
        return_value=[
            {"version": "2.0.3", "execution_id": "old"},
            {"version": "2.10.0", "execution_id": "newest"},
            {"version": "2.9.5", "execution_id": "middle"},
        ],
    )
    @patch("missing_ag_updater.updater.get_ide_version", return_value="2.9.0")
    def _run_test(mock_ver: MagicMock, mock_fetch: MagicMock) -> None:
        # Should detect available update to 2.10.0 in dry-run
        res = update_ide("/dummy/ide", None, dry_run=True)
        assert res is True

    _run_test()
