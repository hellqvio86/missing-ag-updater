import hashlib
import json
import os
import struct
import tempfile
from unittest.mock import patch

import missing_ag_updater


def test_get_ide_version():
    with tempfile.TemporaryDirectory() as tmpdir:
        # Test non-existent product.json
        assert missing_ag_updater.get_ide_version(tmpdir) == "0.0.0"

        # Test valid product.json
        app_dir = os.path.join(tmpdir, "resources", "app")
        os.makedirs(app_dir)
        with open(os.path.join(app_dir, "product.json"), "w") as f:
            json.dump({"ideVersion": "2.0.4"}, f)

        assert missing_ag_updater.get_ide_version(tmpdir) == "2.0.4"


def test_get_hub_version():
    with tempfile.TemporaryDirectory() as tmpdir:
        asar_dir = os.path.join(tmpdir, "resources")
        os.makedirs(asar_dir)
        asar_path = os.path.join(asar_dir, "app.asar")

        # Create a dummy app.asar
        pkg_json = {"version": "2.1.4"}
        pkg_data = json.dumps(pkg_json).encode("utf-8")

        header = {"files": {"package.json": {"size": len(pkg_data), "offset": "0"}}}
        header_data = json.dumps(header).encode("utf-8")
        # header_size includes 8 bytes of padding/sizes in header json size representation
        header_size = len(header_data) + 8
        padding_size = (8 + header_size) - (16 + len(header_data))

        with open(asar_path, "wb") as f:
            # write size headers
            f.write(struct.pack("<I", 4))
            f.write(struct.pack("<I", header_size))
            f.write(struct.pack("<I", header_size - 4))
            f.write(struct.pack("<I", len(header_data)))
            f.write(header_data)
            # padding bytes to reach data offset
            if padding_size > 0:
                f.write(b"\x00" * padding_size)
            f.write(pkg_data)

        assert missing_ag_updater.get_hub_version(tmpdir) == "2.1.4"


def test_get_download_url():
    # Test IDE Linux
    with patch("missing_ag_updater.OS_NAME", "linux"):
        url = missing_ag_updater.get_download_url("ide", "2.0.4", "12345")
        assert "linux-x64/Antigravity%20IDE.tar.gz" in url

    # Test Hub macOS
    with patch("missing_ag_updater.OS_NAME", "darwin"):
        with patch("missing_ag_updater.ARCH_NAME", "arm64"):
            url = missing_ag_updater.get_download_url("hub", "2.1.4", "67890")
            assert "darwin-arm/Antigravity.dmg" in url


def test_compute_sha512():
    with tempfile.NamedTemporaryFile(delete=False) as tmp:
        tmp.write(b"hello world")
        tmp_name = tmp.name
    try:
        expected = hashlib.sha512(b"hello world").hexdigest()
        assert missing_ag_updater.compute_sha512(tmp_name) == expected
    finally:
        os.remove(tmp_name)
