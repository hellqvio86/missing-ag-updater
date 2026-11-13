"""Cross-platform smoke tests for the macOS DMG and Windows installer paths.

These complement the manual checklist in docs/platform-test-matrix.md. They do
not execute real installers; they verify that each platform branch wires the
download, checksum, and installer callbacks together correctly.
"""

from unittest.mock import MagicMock, patch

from missing_ag_updater.updater import update_ide

SAMPLE_SHA512 = "c" * 128
SAMPLE_RELEASE = [{"version": "2.5.5", "execution_id": "42", "sha512": SAMPLE_SHA512}]


@patch("missing_ag_updater.updater.is_path_writable", return_value=True)
@patch("missing_ag_updater.updater.install_macos_dmg", return_value=True)
@patch("missing_ag_updater.updater.compute_sha512", return_value=SAMPLE_SHA512)
@patch("missing_ag_updater.updater.download_file")
@patch("missing_ag_updater.updater.get_running_pids", return_value=[])
@patch("missing_ag_updater.updater.fetch_json", return_value=SAMPLE_RELEASE)
@patch("missing_ag_updater.updater.get_ide_version", return_value="2.5.4")
@patch("missing_ag_updater.updater.OS_NAME", "darwin")
def test_macos_ide_update_smoke(
    mock_version: MagicMock,
    mock_fetch: MagicMock,
    mock_pids: MagicMock,
    mock_download: MagicMock,
    mock_sha: MagicMock,
    mock_install_dmg: MagicMock,
    mock_writable: MagicMock,
) -> None:
    assert update_ide("/Applications/Antigravity IDE.app", None, force=True) is True
    mock_download.assert_called_once()
    download_url = mock_download.call_args.args[0]
    assert download_url.endswith("darwin-x64/Antigravity%20IDE.dmg")
    mock_install_dmg.assert_called_once()
    assert mock_install_dmg.call_args.args[1] == "/Applications/Antigravity IDE.app"


@patch("missing_ag_updater.updater.is_path_writable", return_value=True)
@patch("missing_ag_updater.updater.install_windows_exe", return_value=True)
@patch("missing_ag_updater.updater.compute_sha512", return_value=SAMPLE_SHA512)
@patch("missing_ag_updater.updater.download_file")
@patch("missing_ag_updater.updater.get_running_pids", return_value=[])
@patch("missing_ag_updater.updater.fetch_json", return_value=SAMPLE_RELEASE)
@patch("missing_ag_updater.updater.get_ide_version", return_value="2.5.4")
@patch("missing_ag_updater.updater.OS_NAME", "windows")
def test_windows_ide_update_smoke(
    mock_version: MagicMock,
    mock_fetch: MagicMock,
    mock_pids: MagicMock,
    mock_download: MagicMock,
    mock_sha: MagicMock,
    mock_install_exe: MagicMock,
    mock_writable: MagicMock,
) -> None:
    assert update_ide(r"C:\Users\test\AppData\Local\Programs\antigravity-ide", None, force=True) is True
    download_url = mock_download.call_args.args[0]
    assert download_url.endswith("windows-x64/Antigravity%20IDE.exe")
    mock_install_exe.assert_called_once()


def test_platform_smoke_arguments_are_structured() -> None:
    """Windows installers must always be launched with the fixed silent argv."""
    from missing_ag_updater.updater import install_windows_exe

    with patch("subprocess.run") as mock_run:
        assert install_windows_exe("installer.exe") is True
    mock_run.assert_called_once_with(["installer.exe", "/S"], check=True)


def test_download_payload_is_not_trusted_by_default() -> None:
    """Sanity check: an unverified release is rejected unless explicitly allowed."""
    from missing_ag_updater.updater import update_ide as smoke_update_ide

    with (
        patch("missing_ag_updater.updater.fetch_json", return_value=[{"version": "2.5.5", "execution_id": "42"}]),
        patch("missing_ag_updater.updater.get_ide_version", return_value="2.5.4"),
        patch("missing_ag_updater.updater.is_path_writable", return_value=True),
        patch("missing_ag_updater.updater.download_file") as mock_download,
    ):
        assert smoke_update_ide("/tmp/ide", None, force=True) is False
    # The archive is downloaded before its missing checksum is rejected.
    mock_download.assert_called_once()
