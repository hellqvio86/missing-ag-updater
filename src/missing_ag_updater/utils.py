import hashlib
import json
import os
import struct
import subprocess
import sys
from typing import Any

import requests

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


def resolve_existing_ide_dir(ide_dir: str) -> str:
    """Resolve existing IDE directory path, checking both hyphenated and spaced directory names."""
    if os.path.exists(ide_dir):
        return ide_dir
    if "Antigravity-IDE" in ide_dir:
        alt = ide_dir.replace("Antigravity-IDE", "Antigravity IDE")
        if os.path.exists(alt):
            return alt
    elif "Antigravity IDE" in ide_dir:
        alt = ide_dir.replace("Antigravity IDE", "Antigravity-IDE")
        if os.path.exists(alt):
            return alt
    return ide_dir


def resolve_existing_hub_dir(hub_dir: str) -> str:
    """Resolve existing Hub directory path, checking both hyphenated and spaced directory names."""
    if os.path.exists(hub_dir):
        return hub_dir
    if "Antigravity-x64" in hub_dir:
        alt = hub_dir.replace("Antigravity-x64", "Antigravity Hub")
        if os.path.exists(alt):
            return alt
    elif "Antigravity Hub" in hub_dir:
        alt = hub_dir.replace("Antigravity Hub", "Antigravity-x64")
        if os.path.exists(alt):
            return alt
    return hub_dir


def get_ide_version(ide_dir: str) -> str:
    """Read the current local IDE version from product.json."""
    resolved_dir = resolve_existing_ide_dir(ide_dir)
    if OS_NAME == "darwin":
        product_json_path = os.path.join(resolved_dir, "Contents", "Resources", "app", "product.json")
    else:
        product_json_path = os.path.join(resolved_dir, "resources", "app", "product.json")

    if not os.path.exists(product_json_path):
        return "0.0.0"
    try:
        with open(product_json_path, "r", encoding="utf-8") as fdesc:
            product_json = json.load(fdesc)
            return product_json.get("ideVersion", "0.0.0")
    except Exception:
        return "0.0.0"


def _read_asar_header(asar_path: str) -> tuple[dict[str, Any], int] | None:
    """Parse an Electron app.asar header, returning (header_json, data_start_offset).

    Electron ASAR archives use a 16-byte Chromium Pickle header structure:
      - Bytes 0..3:   uint32 size prefix (always 4)
      - Bytes 4..7:   uint32 total header section size (includes JSON + padding)
      - Bytes 8..11:  uint32 pickle string length (4 + json_size + padding)
      - Bytes 12..15: uint32 exact JSON string size (json_size)

    Reads exact `json_size` (bytes 12..15) to prevent 0-3 alignment null bytes
    (\\x00) from breaking json.loads. Falls back to `header_size - 8` if `json_size`
    is invalid.
    """
    if not os.path.exists(asar_path):
        return None
    try:
        with open(asar_path, "rb") as fdesc:
            prefix = fdesc.read(16)
            if len(prefix) < 16:
                return None
            header_size = struct.unpack("<I", prefix[4:8])[0]
            # Read exact json_size from Chromium Pickle payload length (bytes 12..15)
            json_size = struct.unpack("<I", prefix[12:16])[0]
            # Fall back to header_size - 8 if json_size is non-standard or corrupt
            if json_size <= 0 or json_size > header_size:
                json_size = header_size - 8
            fdesc.seek(16)
            header_json = json.loads(fdesc.read(json_size).decode("utf-8"))
            return header_json, 8 + header_size
    except Exception:
        return None


def get_hub_version(hub_dir: str) -> str:
    """Read the current local Hub version by parsing app.asar package.json."""
    resolved_dir = resolve_existing_hub_dir(hub_dir)
    if OS_NAME == "darwin":
        asar_path = os.path.join(resolved_dir, "Contents", "Resources", "app.asar")
    else:
        asar_path = os.path.join(resolved_dir, "resources", "app.asar")

    parsed = _read_asar_header(asar_path)
    if parsed is None:
        return "0.0.0"
    header_json, data_start_offset = parsed
    try:
        files = header_json.get("files", {})
        package_json_info = files.get("package.json", {})
        if not package_json_info:
            return "0.0.0"
        offset = int(package_json_info.get("offset"))
        size = int(package_json_info.get("size"))
        with open(asar_path, "rb") as fdesc:
            fdesc.seek(data_start_offset + offset)
            pkg_json = json.loads(fdesc.read(size).decode("utf-8"))
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
    """Fetch JSON from a URL with custom user agent headers, retrying on transient failures."""
    import time

    headers = {"User-Agent": "Mozilla/5.0 (AntigravityUpdater)"}
    max_retries = 3
    backoff_factor = 0.5
    last_err: Exception | None = None

    for attempt in range(max_retries + 1):
        try:
            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()
            return response.json()
        except (requests.exceptions.ConnectionError, requests.exceptions.Timeout) as err:
            last_err = err
            if attempt < max_retries:
                time.sleep(backoff_factor * (2**attempt))
            continue
        except requests.exceptions.HTTPError as err:
            last_err = err
            if err.response is not None and err.response.status_code in [500, 502, 503, 504]:
                if attempt < max_retries:
                    time.sleep(backoff_factor * (2**attempt))
                    continue
            raise RuntimeError(f"Failed to query {url}: {err}")
        except Exception as err:
            raise RuntimeError(f"Failed to query {url}: {err}")

    raise RuntimeError(f"Failed to query {url}: {last_err}")


def download_file(url: str, dest_path: str, *, label: str = "Downloading") -> None:
    """Download a file with a visually appealing text progress bar, retrying on transient failures."""
    import time

    headers = {"User-Agent": "Mozilla/5.0 (AntigravityUpdater)"}
    max_retries = 3
    backoff_factor = 0.5
    last_err: Exception | None = None

    for attempt in range(max_retries + 1):
        try:
            with requests.get(url, headers=headers, stream=True, timeout=60) as response:
                response.raise_for_status()
                total_size = int(response.headers.get("content-length", 0))
                block_size = 1024 * 64
                downloaded = 0

                with open(dest_path, "wb") as fdesc:
                    for chunk in response.iter_content(chunk_size=block_size):
                        if chunk:
                            fdesc.write(chunk)
                            downloaded += len(chunk)
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
                return
        except (requests.exceptions.ConnectionError, requests.exceptions.Timeout) as err:
            last_err = err
            if attempt < max_retries:
                time.sleep(backoff_factor * (2**attempt))
            continue
        except requests.exceptions.HTTPError as err:
            last_err = err
            if err.response is not None and err.response.status_code in [500, 502, 503, 504]:
                if attempt < max_retries:
                    time.sleep(backoff_factor * (2**attempt))
                    continue
            sys.stdout.write("\n")
            raise RuntimeError(f"Download error from {url}: {err}")
        except Exception as err:
            sys.stdout.write("\n")
            raise RuntimeError(f"Download error from {url}: {err}")

    sys.stdout.write("\n")
    raise RuntimeError(f"Download error from {url}: {last_err}")


def compute_sha512(file_path: str) -> str:
    """Compute the SHA512 hash of a file."""
    h = hashlib.sha512()
    with open(file_path, "rb") as fdesc:
        while True:
            chunk = fdesc.read(8192)
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
    except Exception as err:
        print_warning(f"Could not update symbolic link {link_name}: {err}")


def extract_asar_icon(asar_path: str, dest_icon_path: str) -> bool:
    """Extract icon.png from app.asar package and write to dest_icon_path."""
    parsed = _read_asar_header(asar_path)
    if parsed is None:
        return False
    header_json, data_start_offset = parsed
    try:
        files = header_json.get("files", {})
        icon_info = files.get("icon.png")
        if not icon_info:
            return False
        offset = int(icon_info.get("offset"))
        size = int(icon_info.get("size"))
        with open(asar_path, "rb") as fdesc:
            fdesc.seek(data_start_offset + offset)
            icon_data = fdesc.read(size)
        os.makedirs(os.path.dirname(dest_icon_path), exist_ok=True)
        with open(dest_icon_path, "wb") as icon_file:
            icon_file.write(icon_data)
        return True
    except Exception:
        return False


def refresh_linux_desktop_caches() -> None:
    """Refresh the user-level desktop database and icon cache on Linux."""
    from .const import USER_APPLICATIONS_DIR, USER_ICONS_DIR

    if OS_NAME != "linux":
        return
    try:
        if os.path.exists(USER_APPLICATIONS_DIR):
            subprocess.run(["update-desktop-database", USER_APPLICATIONS_DIR], capture_output=True, check=False)
    except Exception:
        pass
    try:
        icon_parent = os.path.dirname(os.path.dirname(USER_ICONS_DIR))
        if os.path.exists(icon_parent):
            subprocess.run(["gtk-update-icon-cache", "-q", icon_parent], capture_output=True, check=False)
    except Exception:
        pass


def is_apparmor_enabled() -> bool:
    """Check if AppArmor is enabled and active on Linux."""
    if OS_NAME != "linux":
        return False

    param_path = "/sys/module/apparmor/parameters/enabled"
    if os.path.exists(param_path):
        try:
            with open(param_path, "r", encoding="utf-8") as fdesc:
                if fdesc.read().strip().upper() == "Y":
                    return True
        except Exception:
            pass

    userns_path = "/proc/sys/kernel/apparmor_restrict_unprivileged_userns"
    if os.path.exists(userns_path):
        try:
            with open(userns_path, "r", encoding="utf-8") as fdesc:
                if fdesc.read().strip() == "1":
                    return True
        except Exception:
            pass

    try:
        res = subprocess.run(["aa-enabled"], capture_output=True, text=True)
        if res.returncode == 0:
            return True
    except Exception:
        pass

    return False


def configure_suid_sandbox(ide_dir: str) -> bool:
    """Configure root:root 4755 permissions on chrome-sandbox binary if AppArmor is active."""
    if not is_apparmor_enabled():
        print_info("AppArmor is not active on this system; SUID sandbox configuration skipped.")
        return True

    dirs_to_check = [ide_dir]
    resolved = resolve_existing_ide_dir(ide_dir)
    if resolved not in dirs_to_check:
        dirs_to_check.append(resolved)

    found_any = False
    success = True
    for target_dir in dirs_to_check:
        sandbox_path = os.path.join(target_dir, "chrome-sandbox")
        if not os.path.exists(sandbox_path):
            continue

        found_any = True
        is_root = False
        if hasattr(os, "geteuid"):
            is_root = os.geteuid() == 0

        try:
            if is_root:
                os.chown(sandbox_path, 0, 0)
                os.chmod(sandbox_path, 0o4755)
                print_success(f"Configured root:root 4755 permissions on {sandbox_path}")
            else:
                print_info(f"Root privileges (euid 0) required. Requesting sudo for {sandbox_path}...")
                subprocess.run(["sudo", "chown", "root", sandbox_path], check=True)
                subprocess.run(["sudo", "chmod", "4755", sandbox_path], check=True)
                print_success(f"Configured root:root 4755 permissions on {sandbox_path}")
        except Exception as err:
            print_error(
                f"Failed to configure SUID sandbox permissions on {sandbox_path}: {err}\n"
                f"  Root privileges (euid 0) or sudo access are required.\n"
                f'  Manual command: sudo chown root "{sandbox_path}" && sudo chmod 4755 "{sandbox_path}"'
            )
            success = False

    if not found_any:
        sandbox_path = os.path.join(ide_dir, "chrome-sandbox")
        print_warning(f"chrome-sandbox binary not found at {sandbox_path}")
        return False

    return success
