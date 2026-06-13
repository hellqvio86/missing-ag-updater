import hashlib
import json
import os
import struct
import subprocess
import tempfile
from io import StringIO
from unittest.mock import MagicMock, patch

import pytest

from missing_ag_updater.utils import (
    compute_sha512,
    fetch_json,
    get_cli_version,
    get_hub_version,
    get_ide_version,
    get_running_pids,
    print_error,
    print_info,
    print_status,
    print_success,
    print_warning,
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
        with open(os.path.join(app_dir, "product.json"), "w", encoding="utf-8") as f:
            json.dump({"ideVersion": "2.0.4"}, f)

        assert get_ide_version(tmpdir) == "2.0.4"


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

        with open(asar_path, "wb") as f:
            f.write(struct.pack("<I", 4))
            f.write(struct.pack("<I", header_size))
            f.write(struct.pack("<I", header_size - 4))
            f.write(struct.pack("<I", len(header_data)))
            f.write(header_data)
            if padding_size > 0:
                f.write(b"\x00" * padding_size)
            f.write(pkg_data)

        assert get_hub_version(tmpdir) == "2.1.4"


def test_get_cli_version() -> None:
    with tempfile.TemporaryDirectory() as tmpdir:
        cli_binary = os.path.join(tmpdir, "agy")
        # File doesn't exist
        assert get_cli_version(cli_binary) == "0.0.0"

        # Create dummy file
        with open(cli_binary, "w") as f:
            f.write("#!/bin/sh\necho 1.0.8")
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


def test_fetch_json() -> None:
    mock_response = MagicMock()
    mock_response.read.return_value = b'{"key": "value"}'
    mock_response.__enter__.return_value = mock_response

    with patch("urllib.request.urlopen", return_value=mock_response):
        data = fetch_json("http://example.com/api")
        assert data == {"key": "value"}

    with patch("urllib.request.urlopen", side_effect=Exception("network error")):
        with pytest.raises(RuntimeError) as exc_info:
            fetch_json("http://example.com/api")
        assert "Failed to query http://example.com/api" in str(exc_info.value)


def test_update_symlink() -> None:
    # On Windows it does nothing
    with patch("missing_ag_updater.utils.OS_NAME", "windows"):
        update_symlink("target", "link")

    # On non-windows, test symlink creation and updates
    with patch("missing_ag_updater.utils.OS_NAME", "linux"):
        with tempfile.TemporaryDirectory() as tmpdir:
            target = os.path.join(tmpdir, "target_file")
            with open(target, "w") as f:
                f.write("target contents")

            link_name = os.path.join(tmpdir, "symlink_file")
            update_symlink(target, link_name)
            assert os.path.islink(link_name)
            assert os.readlink(link_name) == target

            # Update link again to see if it replaces correctly
            new_target = os.path.join(tmpdir, "new_target_file")
            with open(new_target, "w") as f:
                f.write("new target contents")

            update_symlink(new_target, link_name)
            assert os.path.islink(link_name)
            assert os.readlink(link_name) == new_target
