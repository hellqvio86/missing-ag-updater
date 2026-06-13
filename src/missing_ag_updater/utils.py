import hashlib
import json
import os
import struct
import subprocess
import sys
import urllib.request
from typing import Any

from .const import (
    COLOR_BLUE,
    COLOR_ENDC,
    COLOR_FAIL,
    COLOR_GREEN,
    COLOR_WARNING,
    OS_NAME,
)


def print_status(msg: str) -> None:
    print(f"{COLOR_BLUE}⠋{COLOR_ENDC} {msg}")


def print_success(msg: str) -> None:
    print(f"{COLOR_GREEN}✓{COLOR_ENDC} {msg}")


def print_warning(msg: str) -> None:
    print(f"{COLOR_WARNING}⚠{COLOR_ENDC} {COLOR_WARNING}{msg}{COLOR_ENDC}")


def print_error(msg: str) -> None:
    print(f"{COLOR_FAIL}✗{COLOR_ENDC} {COLOR_FAIL}{msg}{COLOR_ENDC}")


def print_info(msg: str) -> None:
    print(f"  {msg}")


def get_running_pids(keyword: str) -> list[str]:
    """Get list of running PIDs matching the specified keyword (excluding current process)."""
    pids = []
    my_pid = str(os.getpid())
    if OS_NAME == "windows":
        try:
            res = subprocess.run(["tasklist", "/NH", "/FO", "CSV"], capture_output=True, text=True)
            for line in res.stdout.strip().split("\n"):
                if not line.strip():
                    continue
                parts = [p.strip('"') for p in line.split(",")]
                if len(parts) >= 2 and keyword.lower() in parts[0].lower():
                    pids.append(parts[1])
        except Exception:
            pass
    else:
        try:
            res = subprocess.run(["pgrep", "-f", keyword], capture_output=True, text=True)
            if res.returncode == 0:
                pids = [pid.strip() for pid in res.stdout.strip().split("\n") if pid.strip()]
        except Exception:
            pass
    # Exclude our own process PID to avoid false positives (e.g. matching launcher name)
    return [pid for pid in pids if pid != my_pid]


def get_ide_version(ide_dir: str) -> str:
    """Read the current local IDE version from product.json."""
    if OS_NAME == "darwin":
        product_json_path = os.path.join(ide_dir, "Contents", "Resources", "app", "product.json")
    else:
        product_json_path = os.path.join(ide_dir, "resources", "app", "product.json")

    if not os.path.exists(product_json_path):
        return "0.0.0"
    try:
        with open(product_json_path, "r", encoding="utf-8") as f:
            product_json = json.load(f)
            return product_json.get("ideVersion", "0.0.0")
    except Exception:
        return "0.0.0"


def get_hub_version(hub_dir: str) -> str:
    """Read the current local Hub version by parsing app.asar package.json."""
    if OS_NAME == "darwin":
        asar_path = os.path.join(hub_dir, "Contents", "Resources", "app.asar")
    else:
        asar_path = os.path.join(hub_dir, "resources", "app.asar")

    if not os.path.exists(asar_path):
        return "0.0.0"
    try:
        with open(asar_path, "rb") as f:
            header_size_data = f.read(8)
            if len(header_size_data) < 8:
                return "0.0.0"
            header_size = struct.unpack("<I", header_size_data[4:8])[0]
            f.seek(16)
            header_json_data = f.read(header_size - 8)
            header_json = json.loads(header_json_data.decode("utf-8"))
            files = header_json.get("files", {})
            package_json_info = files.get("package.json", {})
            if not package_json_info:
                return "0.0.0"
            offset = int(package_json_info.get("offset"))
            size = int(package_json_info.get("size"))
            data_start_offset = 8 + header_size
            f.seek(data_start_offset + offset)
            pkg_json = json.loads(f.read(size).decode("utf-8"))
            return pkg_json.get("version", "0.0.0")
    except Exception:
        return "0.0.0"


def get_cli_version(cli_binary: str) -> str:
    """Get the current local CLI version by calling the binary."""
    if not os.path.exists(cli_binary):
        return "0.0.0"
    try:
        res = subprocess.run([cli_binary, "--version"], capture_output=True, text=True, check=True)
        lines = res.stdout.strip().split("\n")
        if lines:
            return lines[0].strip()
        return "0.0.0"
    except Exception:
        return "0.0.0"


def fetch_json(url: str) -> Any:
    """Fetch JSON from a URL with custom user agent headers."""
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (AntigravityUpdater)"})
    try:
        with urllib.request.urlopen(req, timeout=10) as response:
            return json.loads(response.read().decode("utf-8"))
    except Exception as e:
        raise RuntimeError(f"Failed to query {url}: {e}")


def download_file(url: str, dest_path: str, *, label: str = "Downloading") -> None:
    """Download a file with a visually appealing text progress bar."""
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (AntigravityUpdater)"})
    try:
        with urllib.request.urlopen(req, timeout=60) as response:
            total_size = int(response.headers.get("content-length", 0))
            block_size = 1024 * 64
            downloaded = 0

            with open(dest_path, "wb") as f:
                while True:
                    buffer = response.read(block_size)
                    if not buffer:
                        break
                    f.write(buffer)
                    downloaded += len(buffer)
                    if total_size:
                        percent = int(downloaded * 100 / total_size)
                        bar_len = 40
                        filled_len = int(bar_len * downloaded // total_size)
                        bar = "█" * filled_len + "-" * (bar_len - filled_len)
                        current_mb = downloaded / 1024 / 1024
                        total_mb = total_size / 1024 / 1024
                        sys.stdout.write(
                            f"\r{COLOR_BLUE}⠋{COLOR_ENDC} {label}: [{bar}] {percent}% "
                            f"({current_mb:.1f}/{total_mb:.1f} MB)"
                        )
                        sys.stdout.flush()
                sys.stdout.write("\n")
    except Exception as e:
        sys.stdout.write("\n")
        raise RuntimeError(f"Download error from {url}: {e}")


def compute_sha512(file_path: str) -> str:
    """Compute the SHA512 hash of a file."""
    h = hashlib.sha512()
    with open(file_path, "rb") as f:
        while True:
            chunk = f.read(8192)
            if not chunk:
                break
            h.update(chunk)
    return h.hexdigest()


def update_symlink(target: str, link_name: str) -> None:
    """Safely create or update a symbolic link (Linux/macOS only)."""
    if OS_NAME == "windows":
        return
    try:
        if os.path.exists(link_name) or os.path.islink(link_name):
            os.remove(link_name)
        os.makedirs(os.path.dirname(link_name), exist_ok=True)
        os.symlink(target, link_name)
        print_success(f"Linked command: {link_name} -> {target}")
    except Exception as e:
        print_warning(f"Could not update symbolic link {link_name}: {e}")
