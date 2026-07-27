import hashlib
import json
import os
import struct
import subprocess
import tempfile
from io import StringIO
from typing import Any
from unittest.mock import mock_open, patch

import pytest
import responses

from missing_ag_updater.utils import (
    _get_linux_distro_id_like,
    can_fix_suid_sandbox,
    compute_sha512,
    configure_suid_sandbox,
    extract_asar_icon,
    fetch_json,
    get_cli_version,
    get_hub_version,
    get_ide_version,
    get_linux_distro_id,
    get_running_pids,
    is_apparmor_enabled,
    is_ubuntu_sandbox_distro,
    is_suid_sandbox_configured,
    print_error,
    print_info,
    print_status,
    print_success,
    print_warning,
    resolve_existing_hub_dir,
    resolve_existing_ide_dir,
    update_symlink,
)


def test_print_helpers() -> None:
    # Test that print helpers write expected icons/color codes to stdout
    with patch("sys.stdout", new=StringIO()) as fake_out:
        print_status("Checking status")
        val = fake_out.getvalue()
        assert "⠋" in val
        assert "Checking status" in val

    with patch("sys.stdout", new=StringIO()) as fake_out:
        print_success("Success message")
        val = fake_out.getvalue()
        assert "✓" in val
        assert "Success message" in val

    with patch("sys.stdout", new=StringIO()) as fake_out:
        print_warning("Warning message")
        val = fake_out.getvalue()
        assert "⚠" in val
        assert "Warning message" in val

    with patch("sys.stdout", new=StringIO()) as fake_out:
        print_error("Error message")
        val = fake_out.getvalue()
        assert "✗" in val
        assert "Error message" in val

    with patch("sys.stdout", new=StringIO()) as fake_out:
        print_info("Info message")
        val = fake_out.getvalue()
        assert "Info message" in val


def test_get_ide_version() -> None:
    with tempfile.TemporaryDirectory() as tmpdir:
        # Test non-existent product.json
        assert get_ide_version(tmpdir) == "0.0.0"

        # Test valid product.json
        app_dir = os.path.join(tmpdir, "resources", "app")
        os.makedirs(app_dir)
        with open(os.path.join(app_dir, "product.json"), "w", encoding="utf-8") as fdesc:
            json.dump({"ideVersion": "2.0.4"}, fdesc)

        assert get_ide_version(tmpdir) == "2.0.4"


def test_resolve_existing_dirs() -> None:
    with tempfile.TemporaryDirectory() as tmpdir:
        spaced_ide = os.path.join(tmpdir, "Antigravity IDE")
        hyphen_ide = os.path.join(tmpdir, "Antigravity-IDE")

        # Non-existent paths return original argument
        assert resolve_existing_ide_dir(hyphen_ide) == hyphen_ide

        # Creating spaced dir allows hyphen argument to resolve to spaced dir
        os.makedirs(spaced_ide)
        assert resolve_existing_ide_dir(hyphen_ide) == spaced_ide

        # Creating hyphen dir takes precedence
        os.makedirs(hyphen_ide)
        assert resolve_existing_ide_dir(hyphen_ide) == hyphen_ide

        spaced_hub = os.path.join(tmpdir, "Antigravity Hub")
        hyphen_hub = os.path.join(tmpdir, "Antigravity-x64")
        assert resolve_existing_hub_dir(hyphen_hub) == hyphen_hub
        os.makedirs(spaced_hub)
        assert resolve_existing_hub_dir(hyphen_hub) == spaced_hub


def test_get_hub_version() -> None:
    with tempfile.TemporaryDirectory() as tmpdir:
        asar_dir = os.path.join(tmpdir, "resources")
        os.makedirs(asar_dir)
        asar_path = os.path.join(asar_dir, "app.asar")

        # Create a dummy app.asar
        pkg_json = {"version": "2.1.4"}
        pkg_data = json.dumps(pkg_json).encode("utf-8")

        header = {"files": {"package.json": {"size": len(pkg_data), "offset": "0"}}}
        header_data = json.dumps(header).encode("utf-8")
        header_size = len(header_data) + 8
        padding_size = (8 + header_size) - (16 + len(header_data))

        with open(asar_path, "wb") as fdesc:
            fdesc.write(struct.pack("<I", 4))
            fdesc.write(struct.pack("<I", header_size))
            fdesc.write(struct.pack("<I", header_size - 4))
            fdesc.write(struct.pack("<I", len(header_data)))
            fdesc.write(header_data)
            if padding_size > 0:
                fdesc.write(b"\x00" * padding_size)
            fdesc.write(pkg_data)

        assert get_hub_version(tmpdir) == "2.1.4"


def test_get_cli_version() -> None:
    with tempfile.TemporaryDirectory() as tmpdir:
        cli_binary = os.path.join(tmpdir, "agy")
        # File doesn't exist
        assert get_cli_version(cli_binary) == "0.0.0"

        # Create dummy file
        with open(cli_binary, "w") as fdesc:
            fdesc.write("#!/bin/sh\necho 1.0.8")
        os.chmod(cli_binary, 0o755)

        # Mock subprocess.run
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = subprocess.CompletedProcess(args=[], returncode=0, stdout="1.0.8\n")
            assert get_cli_version(cli_binary) == "1.0.8"


def test_compute_sha512() -> None:
    with tempfile.NamedTemporaryFile(delete=False) as tmp:
        tmp.write(b"hello world")
        tmp_name = tmp.name
    try:
        expected = hashlib.sha512(b"hello world").hexdigest()
        assert compute_sha512(tmp_name) == expected
    finally:
        os.remove(tmp_name)


def test_get_running_pids() -> None:
    # Test on Unix with a mock subprocess.run
    with patch("missing_ag_updater.utils.OS_NAME", "linux"):
        with patch("subprocess.run") as mock_run:
            mock_res = subprocess.CompletedProcess(args=[], returncode=0, stdout="1234\n5678\n")
            mock_run.return_value = mock_res

            pids = get_running_pids("test")
            current_pid = str(os.getpid())
            expected = [pid for pid in ["1234", "5678"] if pid != current_pid]
            assert pids == expected

    # Test on Windows with tasklist mock
    with patch("missing_ag_updater.utils.OS_NAME", "windows"):
        with patch("subprocess.run") as mock_run:
            csv_output = '"Image Name","PID"\n"test.exe","4321"\n"other.exe","9999"\n'
            mock_res = subprocess.CompletedProcess(args=[], returncode=0, stdout=csv_output)
            mock_run.return_value = mock_res

            pids = get_running_pids("test")
            current_pid = str(os.getpid())
            expected = [pid for pid in ["4321"] if pid != current_pid]
            assert pids == expected


@responses.activate
@patch("time.sleep")
def test_fetch_json(mock_sleep) -> None:
    responses.add(
        responses.GET,
        "http://example.com/api",
        json={"key": "value"},
        status=200,
    )
    data = fetch_json("http://example.com/api")
    assert data == {"key": "value"}

    responses.add(
        responses.GET,
        "http://example.com/api-error",
        status=500,
    )
    with pytest.raises(RuntimeError) as exc_info:
        fetch_json("http://example.com/api-error")
    assert "Failed to query http://example.com/api-error" in str(exc_info.value)
    assert mock_sleep.call_count == 3


@responses.activate
@patch("time.sleep")
def test_fetch_json_retry_success(mock_sleep) -> None:
    responses.add(responses.GET, "http://example.com/api-retry", status=500)
    responses.add(responses.GET, "http://example.com/api-retry", status=502)
    responses.add(responses.GET, "http://example.com/api-retry", json={"ok": True}, status=200)

    data = fetch_json("http://example.com/api-retry")
    assert data == {"ok": True}
    assert mock_sleep.call_count == 2


def test_update_symlink() -> None:
    # On Windows it does nothing
    with patch("missing_ag_updater.utils.OS_NAME", "windows"):
        update_symlink("target", "link")

    # On non-windows, test symlink creation and updates
    with patch("missing_ag_updater.utils.OS_NAME", "linux"):
        with tempfile.TemporaryDirectory() as tmpdir:
            target = os.path.join(tmpdir, "target_file")
            with open(target, "w") as fdesc:
                fdesc.write("target contents")

            link_name = os.path.join(tmpdir, "symlink_file")
            update_symlink(target, link_name)
            assert os.path.islink(link_name)
            assert os.readlink(link_name) == target

            # Update link again to see if it replaces correctly
            new_target = os.path.join(tmpdir, "new_target_file")
            with open(new_target, "w") as fdesc:
                fdesc.write("new target contents")

            update_symlink(new_target, link_name)
            assert os.path.islink(link_name)
            assert os.readlink(link_name) == new_target


@responses.activate
def test_download_file_success() -> None:
    responses.add(
        responses.GET,
        "http://example.com/file",
        body=b"0123456789",
        headers={"content-length": "10"},
        status=200,
    )
    with tempfile.TemporaryDirectory() as tmpdir:
        dest = os.path.join(tmpdir, "downloaded.txt")
        from missing_ag_updater.utils import download_file

        download_file("http://example.com/file", dest)
        with open(dest, "rb") as fdesc:
            assert fdesc.read() == b"0123456789"


@responses.activate
@patch("time.sleep")
def test_download_file_error(mock_sleep) -> None:
    responses.add(
        responses.GET,
        "http://example.com/file",
        status=404,
    )
    with tempfile.TemporaryDirectory() as tmpdir:
        dest = os.path.join(tmpdir, "downloaded.txt")
        from missing_ag_updater.utils import download_file

        with pytest.raises(RuntimeError) as exc_info:
            download_file("http://example.com/file", dest)
        assert "Download error from http://example.com/file" in str(exc_info.value)
        assert mock_sleep.call_count == 0


@responses.activate
@patch("time.sleep")
def test_download_file_retry_success(mock_sleep) -> None:
    responses.add(responses.GET, "http://example.com/file-retry", status=503)
    responses.add(
        responses.GET,
        "http://example.com/file-retry",
        body=b"retry-success",
        headers={"content-length": "13"},
        status=200,
    )
    with tempfile.TemporaryDirectory() as tmpdir:
        dest = os.path.join(tmpdir, "downloaded-retry.txt")
        from missing_ag_updater.utils import download_file

        download_file("http://example.com/file-retry", dest)
        with open(dest, "rb") as fdesc:
            assert fdesc.read() == b"retry-success"
        assert mock_sleep.call_count == 1


def test_get_hub_version_exceptions() -> None:
    with tempfile.TemporaryDirectory() as tmpdir:
        # 1. Non-existent path
        assert get_hub_version(os.path.join(tmpdir, "non-existent")) == "0.0.0"

        # 2. Path exists but is empty / short header
        asar_dir = os.path.join(tmpdir, "resources")
        os.makedirs(asar_dir, exist_ok=True)
        asar_path = os.path.join(asar_dir, "app.asar")
        with open(asar_path, "wb") as fdesc:
            fdesc.write(b"short")
        assert get_hub_version(tmpdir) == "0.0.0"

        # 3. Valid length but invalid JSON or error reading
        with open(asar_path, "wb") as fdesc:
            fdesc.write(struct.pack("<I", 4))
            fdesc.write(struct.pack("<I", 100))
            fdesc.write(struct.pack("<I", 96))
            fdesc.write(struct.pack("<I", 10))
            fdesc.write(b"invalidjson")
        assert get_hub_version(tmpdir) == "0.0.0"


def test_get_ide_version_darwin_and_exception() -> None:
    # Darwin path product.json
    with patch("missing_ag_updater.utils.OS_NAME", "darwin"):
        with tempfile.TemporaryDirectory() as tmpdir:
            # Non-existent
            assert get_ide_version(tmpdir) == "0.0.0"

            # Valid
            app_dir = os.path.join(tmpdir, "Contents", "Resources", "app")
            os.makedirs(app_dir)
            with open(os.path.join(app_dir, "product.json"), "w", encoding="utf-8") as fdesc:
                json.dump({"ideVersion": "2.0.4"}, fdesc)
            assert get_ide_version(tmpdir) == "2.0.4"

            # Invalid json format raises exception and returns "0.0.0"
            with open(os.path.join(app_dir, "product.json"), "w", encoding="utf-8") as fdesc:
                fdesc.write("invalid json")
            assert get_ide_version(tmpdir) == "0.0.0"


def test_get_hub_version_darwin() -> None:
    with patch("missing_ag_updater.utils.OS_NAME", "darwin"):
        with tempfile.TemporaryDirectory() as tmpdir:
            assert get_hub_version(tmpdir) == "0.0.0"


def test_get_cli_version_exception() -> None:
    with patch("subprocess.run", side_effect=Exception("execution error")):
        assert get_cli_version("/dummy/binary") == "0.0.0"


def test_get_running_pids_exceptions() -> None:
    with patch("missing_ag_updater.utils.OS_NAME", "windows"):
        with patch("subprocess.run", side_effect=Exception("tasklist error")):
            assert get_running_pids("test") == []

    with patch("missing_ag_updater.utils.OS_NAME", "linux"):
        with patch("subprocess.run", side_effect=Exception("pgrep error")):
            assert get_running_pids("test") == []


def test_update_symlink_exception() -> None:
    with patch("missing_ag_updater.utils.OS_NAME", "linux"):
        with patch("os.path.exists", return_value=True):
            with patch("os.remove", side_effect=Exception("permission denied")):
                # Should print a warning but not raise exception
                update_symlink("target", "link")


def _build_asar(asar_path: str, files: dict[str, bytes]) -> int:
    # Build a minimal Electron app.asar archive using Chromium Pickle format,
    # including 4-byte alignment padding for the JSON header.
    # Returns the number of null padding bytes added.
    header: dict[str, Any] = {"files": {}}
    payload = bytearray()
    offset = 0
    for name, data in files.items():
        header["files"][name] = {"size": len(data), "offset": str(offset)}
        payload += data
        offset += len(data)
    header_data = json.dumps(header).encode("utf-8")
    json_len = len(header_data)
    padding = (4 - json_len % 4) % 4
    header_size = 8 + json_len + padding
    with open(asar_path, "wb") as fdesc:
        fdesc.write(struct.pack("<I", 4))
        fdesc.write(struct.pack("<I", header_size))
        fdesc.write(struct.pack("<I", 4 + json_len + padding))
        fdesc.write(struct.pack("<I", json_len))
        fdesc.write(header_data)
        fdesc.write(b"\x00" * padding)
        fdesc.write(bytes(payload))
    return padding


def test_get_hub_version_padded_header() -> None:
    # Regression test: a real asar header whose length is not a multiple of four
    # is null-padded. The parser must read only the JSON bytes and ignore padding.
    with tempfile.TemporaryDirectory() as tmpdir:
        asar_dir = os.path.join(tmpdir, "resources")
        os.makedirs(asar_dir)
        asar_path = os.path.join(asar_dir, "app.asar")
        files = {
            "package.json": json.dumps({"version": "2.4.2"}).encode("utf-8"),
            "icon.png": b"\x89PNG\r\n\x1a\nICON",
        }
        padding = _build_asar(asar_path, files)
        assert padding != 0
        assert get_hub_version(tmpdir) == "2.4.2"


def test_extract_asar_icon_padded_header() -> None:
    with tempfile.TemporaryDirectory() as tmpdir:
        asar_path = os.path.join(tmpdir, "app.asar")
        icon_bytes = b"\x89PNG\r\n\x1a\nICON"
        files = {
            "package.json": json.dumps({"version": "2.4.2"}).encode("utf-8"),
            "icon.png": icon_bytes,
        }
        padding = _build_asar(asar_path, files)
        assert padding != 0

        dest_icon = os.path.join(tmpdir, "out", "icon.png")
        assert extract_asar_icon(asar_path, dest_icon) is True
        with open(dest_icon, "rb") as fdesc:
            assert fdesc.read() == icon_bytes


def test_extract_asar_icon_failure_cases() -> None:
    with tempfile.TemporaryDirectory() as tmpdir:
        # Missing archive
        assert extract_asar_icon(os.path.join(tmpdir, "missing.asar"), os.path.join(tmpdir, "i.png")) is False

        # Archive without an icon.png entry
        asar_path = os.path.join(tmpdir, "app.asar")
        _build_asar(asar_path, {"package.json": json.dumps({"version": "1.0.0"}).encode("utf-8")})
        assert extract_asar_icon(asar_path, os.path.join(tmpdir, "i.png")) is False


# ── Distro detection tests ──


def test_get_linux_distro_id_ubuntu() -> None:
    """Parses ID=ubuntu from /etc/os-release."""
    content = 'NAME="Ubuntu"\nID=ubuntu\nVERSION_ID="24.04"\n'
    with patch("missing_ag_updater.utils.OS_NAME", "linux"):
        with patch("builtins.open", mock_open(read_data=content)):
            assert get_linux_distro_id() == "ubuntu"


def test_get_linux_distro_id_fedora() -> None:
    """Parses ID=fedora from /etc/os-release."""
    content = 'NAME="Fedora Linux"\nID=fedora\nVERSION_ID="40"\n'
    with patch("missing_ag_updater.utils.OS_NAME", "linux"):
        with patch("builtins.open", mock_open(read_data=content)):
            assert get_linux_distro_id() == "fedora"


def test_get_linux_distro_id_quoted() -> None:
    """Handles quoted ID values like ID=\"ubuntu\"."""
    content = 'ID="ubuntu"\n'
    with patch("missing_ag_updater.utils.OS_NAME", "linux"):
        with patch("builtins.open", mock_open(read_data=content)):
            assert get_linux_distro_id() == "ubuntu"


def test_get_linux_distro_id_non_linux() -> None:
    """Returns empty string on non-Linux platforms."""
    with patch("missing_ag_updater.utils.OS_NAME", "darwin"):
        assert get_linux_distro_id() == ""


def test_get_linux_distro_id_file_missing() -> None:
    """Returns empty string when /etc/os-release cannot be read."""
    with patch("missing_ag_updater.utils.OS_NAME", "linux"):
        with patch("builtins.open", side_effect=FileNotFoundError):
            assert get_linux_distro_id() == ""


def test_get_linux_distro_id_like_ubuntu_derivative() -> None:
    """Linux Mint returns ID_LIKE with ubuntu."""
    content = 'ID=linuxmint\nID_LIKE="ubuntu debian"\n'
    with patch("missing_ag_updater.utils.OS_NAME", "linux"):
        with patch("builtins.open", mock_open(read_data=content)):
            result = _get_linux_distro_id_like()
            assert "ubuntu" in result
            assert "debian" in result


def test_get_linux_distro_id_like_non_linux() -> None:
    """Returns empty list on non-Linux."""
    with patch("missing_ag_updater.utils.OS_NAME", "windows"):
        assert _get_linux_distro_id_like() == []


def test_get_linux_distro_id_like_no_field() -> None:
    """Returns empty list when ID_LIKE is absent."""
    content = 'ID=arch\nNAME="Arch Linux"\n'
    with patch("missing_ag_updater.utils.OS_NAME", "linux"):
        with patch("builtins.open", mock_open(read_data=content)):
            assert _get_linux_distro_id_like() == []


def test_is_ubuntu_sandbox_distro_ubuntu() -> None:
    """Ubuntu is in the Ubuntu sandbox allowlist."""
    with patch("missing_ag_updater.utils.get_linux_distro_id", return_value="ubuntu"):
        assert is_ubuntu_sandbox_distro() is True


def test_is_ubuntu_sandbox_distro_fedora() -> None:
    """Fedora is NOT in the Ubuntu sandbox allowlist."""
    with patch("missing_ag_updater.utils.get_linux_distro_id", return_value="fedora"):
        with patch("missing_ag_updater.utils._get_linux_distro_id_like", return_value=[]):
            assert is_ubuntu_sandbox_distro() is False


def test_is_ubuntu_sandbox_distro_mint_derivative() -> None:
    """Linux Mint (ID_LIKE=ubuntu) is covered by the allowlist."""
    with patch("missing_ag_updater.utils.get_linux_distro_id", return_value="linuxmint"):
        with patch("missing_ag_updater.utils._get_linux_distro_id_like", return_value=["ubuntu", "debian"]):
            assert is_ubuntu_sandbox_distro() is True


def test_is_ubuntu_sandbox_distro_non_linux() -> None:
    """Non-Linux always returns False."""
    with patch("missing_ag_updater.utils.get_linux_distro_id", return_value=""):
        with patch("missing_ag_updater.utils._get_linux_distro_id_like", return_value=[]):
            assert is_ubuntu_sandbox_distro() is False


# ── AppArmor / sandbox tests ──


def test_is_apparmor_enabled() -> None:
    with patch("missing_ag_updater.utils.OS_NAME", "windows"):
        assert is_apparmor_enabled() is False

    with patch("missing_ag_updater.utils.OS_NAME", "linux"):
        with patch("missing_ag_updater.utils.is_ubuntu_sandbox_distro", return_value=True):
            with patch("os.path.exists", side_effect=lambda p: p == "/sys/module/apparmor/parameters/enabled"):
                with patch("builtins.open", mock_open(read_data="Y\n")):
                    assert is_apparmor_enabled() is True

            with patch(
                "os.path.exists",
                side_effect=lambda p: p == "/proc/sys/kernel/apparmor_restrict_unprivileged_userns",
            ):
                with patch("builtins.open", mock_open(read_data="1\n")):
                    assert is_apparmor_enabled() is True


def test_is_apparmor_enabled_non_sandbox_distro() -> None:
    """is_apparmor_enabled returns False on non-allowlisted distros even if AppArmor files exist."""
    with patch("missing_ag_updater.utils.OS_NAME", "linux"):
        with patch("missing_ag_updater.utils.is_ubuntu_sandbox_distro", return_value=False):
            assert is_apparmor_enabled() is False


def test_configure_suid_sandbox_non_sandbox_distro() -> None:
    """configure_suid_sandbox skips entirely on non-allowlisted distros."""
    with patch("missing_ag_updater.utils.is_ubuntu_sandbox_distro", return_value=False):
        assert configure_suid_sandbox("/tmp/fake_ide") is True


def test_configure_suid_sandbox_apparmor_disabled() -> None:
    with patch("missing_ag_updater.utils.is_ubuntu_sandbox_distro", return_value=True):
        with patch("missing_ag_updater.utils.is_apparmor_enabled", return_value=False):
            assert configure_suid_sandbox("/tmp/fake_ide") is True


def test_configure_suid_sandbox_missing() -> None:
    with patch("missing_ag_updater.utils.is_ubuntu_sandbox_distro", return_value=True):
        with patch("missing_ag_updater.utils.is_apparmor_enabled", return_value=True):
            with tempfile.TemporaryDirectory() as tmpdir:
                assert configure_suid_sandbox(tmpdir) is False


def test_configure_suid_sandbox_as_root() -> None:
    with patch("missing_ag_updater.utils.is_ubuntu_sandbox_distro", return_value=True):
        with patch("missing_ag_updater.utils.is_apparmor_enabled", return_value=True):
            with patch("missing_ag_updater.utils.is_suid_sandbox_configured", return_value=False):
                with tempfile.TemporaryDirectory() as tmpdir:
                    sandbox_file = os.path.join(tmpdir, "chrome-sandbox")
                    open(sandbox_file, "w").close()
                    with patch("os.geteuid", return_value=0, create=True):
                        with patch("os.chown") as mock_chown:
                            with patch("os.chmod") as mock_chmod:
                                assert configure_suid_sandbox(tmpdir) is True
                                mock_chown.assert_called_once_with(sandbox_file, 0, 0)
                                mock_chmod.assert_called_once_with(sandbox_file, 0o4755)


def test_configure_suid_sandbox_via_sudo() -> None:
    with patch("missing_ag_updater.utils.is_ubuntu_sandbox_distro", return_value=True):
        with patch("missing_ag_updater.utils.is_apparmor_enabled", return_value=True):
            with patch("missing_ag_updater.utils.is_suid_sandbox_configured", return_value=False):
                with tempfile.TemporaryDirectory() as tmpdir:
                    sandbox_file = os.path.join(tmpdir, "chrome-sandbox")
                    open(sandbox_file, "w").close()
                    with patch("os.geteuid", return_value=1000, create=True):
                        with patch("subprocess.run") as mock_run:
                            assert configure_suid_sandbox(tmpdir) is True
                            assert mock_run.call_count == 2
                        # Must use root:root (not just root) so group is also fixed
                        assert mock_run.call_args_list[0][0][0] == ["sudo", "chown", "root:root", sandbox_file]


def test_configure_suid_sandbox_failure() -> None:
    with patch("missing_ag_updater.utils.is_ubuntu_sandbox_distro", return_value=True):
        with patch("missing_ag_updater.utils.is_apparmor_enabled", return_value=True):
            with patch("missing_ag_updater.utils.is_suid_sandbox_configured", return_value=False):
                with tempfile.TemporaryDirectory() as tmpdir:
                    sandbox_file = os.path.join(tmpdir, "chrome-sandbox")
                    open(sandbox_file, "w").close()
                    with patch("os.geteuid", return_value=1000, create=True):
                        with patch("subprocess.run", side_effect=subprocess.CalledProcessError(1, "sudo")):
                            assert configure_suid_sandbox(tmpdir) is False


def test_configure_suid_sandbox_already_ok() -> None:
    """If sandbox is already root:root 4755, no chown/chmod should be called."""
    with patch("missing_ag_updater.utils.is_ubuntu_sandbox_distro", return_value=True):
        with patch("missing_ag_updater.utils.is_apparmor_enabled", return_value=True):
            with patch("missing_ag_updater.utils.is_suid_sandbox_configured", return_value=True):
                with tempfile.TemporaryDirectory() as tmpdir:
                    sandbox_file = os.path.join(tmpdir, "chrome-sandbox")
                    open(sandbox_file, "w").close()
                    with patch("os.chown") as mock_chown:
                        with patch("os.chmod") as mock_chmod:
                            with patch("subprocess.run") as mock_run:
                                assert configure_suid_sandbox(tmpdir) is True
                                # Nothing should have been called — already configured
                                mock_chown.assert_not_called()
                                mock_chmod.assert_not_called()
                                mock_run.assert_not_called()


def test_is_suid_sandbox_configured_correct() -> None:
    """is_suid_sandbox_configured returns True for root:root 4755."""
    import stat as stat_mod

    mock_stat = os.stat_result((stat_mod.S_ISUID | 0o100755, 0, 0, 0, 0, 0, 0, 0, 0, 0))
    with patch("os.stat", return_value=mock_stat):
        assert is_suid_sandbox_configured("/fake/chrome-sandbox") is True


def test_is_suid_sandbox_configured_wrong_group() -> None:
    """is_suid_sandbox_configured returns False when group is not root."""
    import stat as stat_mod

    # uid=0, gid=1000 (non-root group) with 4755
    mock_stat = os.stat_result((stat_mod.S_ISUID | 0o100755, 0, 0, 0, 0, 1000, 0, 0, 0, 0))
    with patch("os.stat", return_value=mock_stat):
        assert is_suid_sandbox_configured("/fake/chrome-sandbox") is False


def test_is_suid_sandbox_configured_no_suid_bit() -> None:
    """is_suid_sandbox_configured returns False when SUID bit is missing."""
    # mode 0o755 without S_ISUID
    mock_stat = os.stat_result((0o100755, 0, 0, 0, 0, 0, 0, 0, 0, 0))
    with patch("os.stat", return_value=mock_stat):
        assert is_suid_sandbox_configured("/fake/chrome-sandbox") is False


def test_is_suid_sandbox_configured_exception() -> None:
    """is_suid_sandbox_configured returns False on OS errors (file not found etc)."""
    with patch("os.stat", side_effect=OSError("No such file")):
        assert is_suid_sandbox_configured("/fake/chrome-sandbox") is False


def test_can_fix_suid_sandbox_non_sandbox_distro() -> None:
    """can_fix_suid_sandbox returns OK on non-allowlisted distros."""
    with patch("missing_ag_updater.utils.is_ubuntu_sandbox_distro", return_value=False):
        ok, reason = can_fix_suid_sandbox()
        assert ok is True
        assert reason == ""


def test_can_fix_suid_sandbox_no_apparmor() -> None:
    """If AppArmor is not active, sandbox fix is never needed — always OK."""
    with patch("missing_ag_updater.utils.is_ubuntu_sandbox_distro", return_value=True):
        with patch("missing_ag_updater.utils.is_apparmor_enabled", return_value=False):
            ok, reason = can_fix_suid_sandbox()
            assert ok is True
            assert reason == ""


def test_can_fix_suid_sandbox_as_root() -> None:
    """If we are root, we can always fix sandbox permissions directly."""
    with patch("missing_ag_updater.utils.is_ubuntu_sandbox_distro", return_value=True):
        with patch("missing_ag_updater.utils.is_apparmor_enabled", return_value=True):
            with patch("os.geteuid", return_value=0, create=True):
                ok, reason = can_fix_suid_sandbox()
                assert ok is True
                assert reason == ""


def test_can_fix_suid_sandbox_sudo_available() -> None:
    """Non-root but sudo -n true succeeds — fix is possible."""
    with patch("missing_ag_updater.utils.is_ubuntu_sandbox_distro", return_value=True):
        with patch("missing_ag_updater.utils.is_apparmor_enabled", return_value=True):
            with patch("os.geteuid", return_value=1000, create=True):
                mock_result: subprocess.CompletedProcess[bytes] = subprocess.CompletedProcess(
                    args=["sudo", "-n", "true"], returncode=0
                )
                with patch("subprocess.run", return_value=mock_result):
                    ok, reason = can_fix_suid_sandbox()
                    assert ok is True
                    assert reason == ""


def test_can_fix_suid_sandbox_sudo_unavailable() -> None:
    """Non-root and sudo -n true fails — bail out early with a clear reason."""
    with patch("missing_ag_updater.utils.is_ubuntu_sandbox_distro", return_value=True):
        with patch("missing_ag_updater.utils.is_apparmor_enabled", return_value=True):
            with patch("os.geteuid", return_value=1000, create=True):
                mock_result: subprocess.CompletedProcess[bytes] = subprocess.CompletedProcess(
                    args=["sudo", "-n", "true"], returncode=1
                )
                with patch("subprocess.run", return_value=mock_result):
                    ok, reason = can_fix_suid_sandbox()
                    assert ok is False
                    assert "AppArmor" in reason
                    assert "sudo" in reason


def test_can_fix_suid_sandbox_sudo_exception() -> None:
    """sudo not found or times out — bail out early with a clear reason."""
    with patch("missing_ag_updater.utils.is_ubuntu_sandbox_distro", return_value=True):
        with patch("missing_ag_updater.utils.is_apparmor_enabled", return_value=True):
            with patch("os.geteuid", return_value=1000, create=True):
                with patch("subprocess.run", side_effect=FileNotFoundError("sudo not found")):
                    ok, reason = can_fix_suid_sandbox()
                    assert ok is False
                    assert "AppArmor" in reason
