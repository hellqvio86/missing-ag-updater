"""General utilities, process checking, hash verification, downloads, and sandbox configuration."""

import hashlib
import json
import os
import random
import stat as stat_mod
import struct
import subprocess  # nosec B404
import sys
import time
from typing import Any

import requests

from .const import (
    COLOR_BLUE,
    COLOR_ENDC,
    COLOR_FAIL,
    COLOR_GREEN,
    COLOR_WARNING,
    OS_NAME,
    SYSTEM_APPLICATIONS_DIR,
    USER_AGENT,
    USER_APPLICATIONS_DIR,
    USER_ICONS_DIR,
)


def print_status(msg: str) -> None:
    """Print a status message with a spinner icon."""
    print(f"{COLOR_BLUE}⠋{COLOR_ENDC} {msg}")


def print_success(msg: str) -> None:
    """Print a success message with a checkmark."""
    print(f"{COLOR_GREEN}✓{COLOR_ENDC} {msg}")


def print_warning(msg: str) -> None:
    """Print a warning message with an alert icon."""
    print(f"{COLOR_WARNING}⚠{COLOR_ENDC} {COLOR_WARNING}{msg}{COLOR_ENDC}")


def print_error(msg: str) -> None:
    """Print an error message with a cross icon."""
    print(f"{COLOR_FAIL}✗{COLOR_ENDC} {COLOR_FAIL}{msg}{COLOR_ENDC}")


def print_info(msg: str) -> None:
    """Print an informational message with indentation."""
    print(f"  {msg}")


# Distro allowlist for sandbox features (opt-in per distro)
_SANDBOX_DISTROS = frozenset({"ubuntu"})


def get_linux_distro_id() -> str:
    """Return the lowercase distro ID from /etc/os-release (e.g. 'ubuntu', 'fedora').

    Returns an empty string on non-Linux platforms or if the file cannot be read.
    """
    if OS_NAME != "linux":
        return ""
    try:
        with open("/etc/os-release", "r", encoding="utf-8") as fdesc:
            for line in fdesc:
                if line.startswith("ID="):
                    return line.strip().split("=", 1)[1].strip('"').lower()
    except OSError:
        pass
    return ""


def _get_linux_distro_id_like() -> list[str]:
    """Return the lowercase ID_LIKE values from /etc/os-release as a list.

    For example, Linux Mint returns ['ubuntu', 'debian'].
    Returns an empty list on non-Linux or if the field is absent.
    """
    if OS_NAME != "linux":
        return []
    try:
        with open("/etc/os-release", "r", encoding="utf-8") as fdesc:
            for line in fdesc:
                if line.startswith("ID_LIKE="):
                    raw = line.strip().split("=", 1)[1].strip('"').lower()
                    return raw.split()
    except OSError:
        pass
    return []


def is_ubuntu_sandbox_distro() -> bool:
    """Return True if the current Linux distro is an Ubuntu-style distro requiring sandbox fixes.

    Checks both the ID and ID_LIKE fields from /etc/os-release against the
    Ubuntu allowlist. This covers Ubuntu itself as well as derivatives such as
    Linux Mint with ID_LIKE='ubuntu debian'.
    """
    distro_id = get_linux_distro_id()
    if distro_id in _SANDBOX_DISTROS:
        return True
    for like_id in _get_linux_distro_id_like():
        if like_id in _SANDBOX_DISTROS:
            return True
    return False


def is_path_writable(path: str) -> bool:
    """Check if the given path or its nearest existing parent directory is writable."""
    if not path:
        return False
    target = path
    while not os.path.exists(target):
        parent = os.path.dirname(target)
        if parent == target or not parent:
            break
        target = parent
    return os.access(target, os.W_OK)


def get_running_pids(keyword: str) -> list[str]:
    """Get running PIDs matching keyword, excluding updater and agent processes."""
    pids: list[str] = []
    my_pid = str(os.getpid())
    my_ppid = str(os.getppid()) if hasattr(os, "getppid") else ""
    keyword_clean = keyword.strip().lower()

    if OS_NAME == "windows":
        try:
            res = subprocess.run(
                ["tasklist", "/NH", "/FO", "CSV"],
                capture_output=True,
                text=True,
                check=False,
            )  # nosec B603, B607
            for line in res.stdout.strip().split("\n"):
                if not line.strip():
                    continue
                parts = [part.strip('"') for part in line.split(",")]
                if len(parts) >= 2 and keyword_clean in parts[0].lower():
                    image_name = parts[0].lower()
                    if keyword_clean == "antigravity" and "antigravity-ide" in image_name:
                        continue
                    if "updater" in image_name:
                        continue
                    pids.append(parts[1])
        except Exception:  # nosec B110
            pass
    else:
        try:
            res = subprocess.run(
                ["pgrep", "-f", keyword_clean],
                capture_output=True,
                text=True,
                check=False,
            )  # nosec B603, B607
            if res.returncode == 0:
                pids = [pid.strip() for pid in res.stdout.strip().split("\n") if pid.strip()]
        except Exception:  # nosec B110
            pass

    # Exclude our own process PID and parent process to avoid false positives
    filtered: list[str] = []
    ignored_substrings = [
        "missing_ag_updater",
        "missing-ag-updater",
        "antigravity-updater",
        "antigravity-cli",
        "antigravity_daemon",
        ".gemini/antigravity",
        "pytest",
        "/bin/agy",
        " agy",
    ]
    for pid in pids:
        if pid in (my_pid, my_ppid):
            continue
        if OS_NAME == "linux" and os.path.exists(f"/proc/{pid}/cmdline"):
            try:
                with open(f"/proc/{pid}/cmdline", "rb") as fdesc:
                    cmdline_raw = fdesc.read()
                    if not cmdline_raw:
                        continue
                    tokens = [tok.decode("utf-8", errors="ignore") for tok in cmdline_raw.split(b"\x00") if tok]
                    cmdline_str = " ".join(tokens)
                    if any(ignored in cmdline_str for ignored in ignored_substrings):
                        continue

                    # Determine binary basename from first argument
                    exe_basename = os.path.basename(tokens[0]).lower() if tokens else ""

                    if keyword_clean == "antigravity":
                        # Hub executable should match 'antigravity' or 'antigravity-hub', not 'antigravity-ide'
                        if "antigravity-ide" in exe_basename or "antigravity ide" in exe_basename:
                            continue
                        if not any(name in exe_basename for name in ("antigravity", "antigravity-hub", "electron")):
                            if not any(tok.lower() == "antigravity" for tok in tokens):
                                continue
                    elif keyword_clean in ("antigravity-ide", "antigravity ide"):
                        if not any(
                            name in exe_basename for name in ("antigravity-ide", "antigravity ide", "code", "electron")
                        ):
                            if not any(
                                "antigravity-ide" in tok.lower() or "antigravity ide" in tok.lower() for tok in tokens
                            ):
                                continue
                    elif keyword_clean == "agy":
                        if exe_basename != "agy" and not any(tok == "agy" for tok in tokens):
                            continue
            except OSError:
                pass
        filtered.append(pid)
    return filtered


def resolve_existing_ide_dir(ide_dir: str) -> str:
    """Resolve existing IDE directory path across nested, hyphenated, and spaced names."""
    if not ide_dir:
        return ""
    candidates = [
        ide_dir,
        os.path.join(ide_dir, "Antigravity-IDE"),
        os.path.join(ide_dir, "Antigravity IDE"),
    ]
    if "Antigravity-IDE" in ide_dir:
        candidates.append(ide_dir.replace("Antigravity-IDE", "Antigravity IDE"))
    elif "Antigravity IDE" in ide_dir:
        candidates.append(ide_dir.replace("Antigravity IDE", "Antigravity-IDE"))
    elif "antigravity-ide" in ide_dir:
        candidates.append(os.path.join(ide_dir, "Antigravity-IDE"))
        candidates.append(os.path.join(ide_dir, "Antigravity IDE"))

    for cand in candidates:
        if OS_NAME == "darwin":
            pj = os.path.join(cand, "Contents", "Resources", "app", "product.json")
        else:
            pj = os.path.join(cand, "resources", "app", "product.json")
        if os.path.exists(pj):
            return cand

    for cand in candidates:
        if os.path.exists(cand):
            return cand

    return ide_dir


def resolve_existing_hub_dir(hub_dir: str) -> str:
    """Resolve existing Hub directory path across nested, hyphenated, and spaced names."""
    if not hub_dir:
        return ""
    candidates = [
        hub_dir,
        os.path.join(hub_dir, "Antigravity-x64"),
        os.path.join(hub_dir, "Antigravity Hub"),
        os.path.join(hub_dir, "Antigravity"),
    ]
    if "Antigravity-x64" in hub_dir:
        candidates.append(hub_dir.replace("Antigravity-x64", "Antigravity Hub"))
        candidates.append(hub_dir.replace("Antigravity-x64", "Antigravity"))
    elif "Antigravity Hub" in hub_dir:
        candidates.append(hub_dir.replace("Antigravity Hub", "Antigravity-x64"))
    elif "antigravity" in hub_dir.lower():
        candidates.append(os.path.join(hub_dir, "Antigravity-x64"))
        candidates.append(os.path.join(hub_dir, "Antigravity"))

    for cand in candidates:
        if OS_NAME == "darwin":
            asar = os.path.join(cand, "Contents", "Resources", "app.asar")
        else:
            asar = os.path.join(cand, "resources", "app.asar")
        if os.path.exists(asar):
            return cand

    for cand in candidates:
        if os.path.exists(cand):
            return cand

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
    except (OSError, json.JSONDecodeError, KeyError, TypeError):
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
    is invalid, bounded strictly by actual file size.
    """
    if not os.path.exists(asar_path):
        return None
    try:
        file_size = os.path.getsize(asar_path)
        if file_size < 16:
            return None
        with open(asar_path, "rb") as fdesc:
            prefix = fdesc.read(16)
            if len(prefix) < 16:
                return None
            header_size = struct.unpack("<I", prefix[4:8])[0]
            # Read exact json_size from Chromium Pickle payload length (bytes 12..15)
            json_size = struct.unpack("<I", prefix[12:16])[0]
            max_json_len = min(header_size, max(0, file_size - 16))
            # Fall back to header_size - 8 if json_size is non-standard or corrupt
            if json_size <= 0 or json_size > max_json_len:
                json_size = min(max(0, header_size - 8), max_json_len)
            if json_size <= 0:
                return None
            fdesc.seek(16)
            header_json = json.loads(fdesc.read(json_size).decode("utf-8"))
            return header_json, 8 + header_size
    except (OSError, struct.error, json.JSONDecodeError, UnicodeDecodeError):
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
    except (
        OSError,
        json.JSONDecodeError,
        UnicodeDecodeError,
        KeyError,
        ValueError,
        TypeError,
    ):
        return "0.0.0"


def get_cli_version(cli_binary: str) -> str:
    """Get the current local CLI version by calling the binary."""
    if not os.path.exists(cli_binary):
        return "0.0.0"
    try:
        res = subprocess.run(
            [cli_binary, "--version"],
            capture_output=True,
            text=True,
            check=True,
        )  # nosec B603
        lines = res.stdout.strip().split("\n")
        if lines:
            return lines[0].strip()
        return "0.0.0"
    except (subprocess.SubprocessError, OSError, UnicodeDecodeError):
        return "0.0.0"


def fetch_json(url: str) -> Any:
    """Fetch JSON from a URL with custom user agent headers, retrying on transient failures with backoff and jitter."""
    headers = {"User-Agent": USER_AGENT}
    max_retries = 3
    backoff_factor = 0.5
    last_err: Exception | None = None

    for attempt in range(max_retries + 1):
        try:
            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()
            return response.json()
        except (
            requests.exceptions.ConnectionError,
            requests.exceptions.Timeout,
        ) as err:
            last_err = err
            if attempt < max_retries:
                sleep_delay = min(backoff_factor * (2**attempt) + random.uniform(0.05, 0.25), 5.0)
                time.sleep(sleep_delay)
            continue
        except requests.exceptions.HTTPError as err:
            last_err = err
            if err.response is not None and err.response.status_code in [
                500,
                502,
                503,
                504,
            ]:
                if attempt < max_retries:
                    sleep_delay = min(backoff_factor * (2**attempt) + random.uniform(0.05, 0.25), 5.0)
                    time.sleep(sleep_delay)
                    continue
            raise RuntimeError(f"Failed to query {url}: {err}") from err
        except (requests.exceptions.RequestException, json.JSONDecodeError) as err:
            raise RuntimeError(f"Failed to query {url}: {err}") from err

    raise RuntimeError(f"Failed to query {url}: {last_err}") from last_err


def download_file(url: str, dest_path: str, *, label: str = "Downloading") -> None:
    """Download a file with progress indication, retrying on transient failures with backoff and jitter."""
    headers = {"User-Agent": USER_AGENT}
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
                                progress_bar = "█" * filled_len + "-" * (bar_len - filled_len)
                                current_mb = downloaded / 1024 / 1024
                                total_mb = total_size / 1024 / 1024
                                sys.stdout.write(
                                    f"\r{COLOR_BLUE}⠋{COLOR_ENDC} {label}: [{progress_bar}] {percent}% "
                                    f"({current_mb:.1f}/{total_mb:.1f} MB)"
                                )
                                sys.stdout.flush()
                    sys.stdout.write("\n")
                return
        except (
            requests.exceptions.ConnectionError,
            requests.exceptions.Timeout,
        ) as err:
            last_err = err
            if attempt < max_retries:
                sleep_delay = min(backoff_factor * (2**attempt) + random.uniform(0.05, 0.25), 5.0)
                time.sleep(sleep_delay)
            continue
        except requests.exceptions.HTTPError as err:
            last_err = err
            if err.response is not None and err.response.status_code in [
                500,
                502,
                503,
                504,
            ]:
                if attempt < max_retries:
                    sleep_delay = min(backoff_factor * (2**attempt) + random.uniform(0.05, 0.25), 5.0)
                    time.sleep(sleep_delay)
                    continue
            sys.stdout.write("\n")
            raise RuntimeError(f"Download error from {url}: {err}") from err
        except (requests.exceptions.RequestException, OSError) as err:
            sys.stdout.write("\n")
            raise RuntimeError(f"Download error from {url}: {err}") from err

    sys.stdout.write("\n")
    raise RuntimeError(f"Download error from {url}: {last_err}") from last_err


def compute_sha256(file_path: str) -> str:
    """Compute the SHA256 hash of a file."""
    hasher = hashlib.sha256()
    with open(file_path, "rb") as fdesc:
        while True:
            chunk = fdesc.read(8192)
            if not chunk:
                break
            hasher.update(chunk)
    return hasher.hexdigest()


def compute_sha512(file_path: str) -> str:
    """Compute the SHA512 hash of a file."""
    hasher = hashlib.sha512()
    with open(file_path, "rb") as fdesc:
        while True:
            chunk = fdesc.read(8192)
            if not chunk:
                break
            hasher.update(chunk)
    return hasher.hexdigest()


def update_symlink(target: str, link_name: str) -> bool:
    """Safely create or update a symbolic link (Linux/macOS only). Returns True on success."""
    if OS_NAME == "windows":
        return True
    try:
        if os.path.exists(link_name) or os.path.islink(link_name):
            os.remove(link_name)
        os.makedirs(os.path.dirname(link_name), exist_ok=True)
        os.symlink(target, link_name)
        print_success(f"Linked command: {link_name} -> {target}")
        return True
    except Exception as err:
        print_warning(f"Could not update symbolic link {link_name}: {err}")
        return False


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
    except (OSError, KeyError, ValueError, TypeError):
        return False


def refresh_linux_desktop_caches() -> None:
    """Refresh the desktop database and icon caches on Linux."""
    if OS_NAME != "linux":
        return
    for app_dir in (USER_APPLICATIONS_DIR, SYSTEM_APPLICATIONS_DIR):
        try:
            if os.path.exists(app_dir):
                subprocess.run(
                    ["update-desktop-database", app_dir],
                    capture_output=True,
                    check=False,
                )  # nosec B603, B607
        except (subprocess.SubprocessError, OSError):
            pass
    try:
        icon_parent = os.path.dirname(os.path.dirname(USER_ICONS_DIR))
        if os.path.exists(icon_parent):
            subprocess.run(
                ["gtk-update-icon-cache", "-q", icon_parent],
                capture_output=True,
                check=False,
            )  # nosec B603, B607
    except (subprocess.SubprocessError, OSError):
        pass


def is_apparmor_enabled() -> bool:
    """Check if AppArmor is enabled and active on Linux.

    Only checks on distros in the sandbox allowlist (e.g. Ubuntu).
    Returns False immediately on non-allowlisted distros.
    """
    if OS_NAME != "linux":
        return False
    if not is_ubuntu_sandbox_distro():
        return False

    param_path = "/sys/module/apparmor/parameters/enabled"
    if os.path.exists(param_path):
        try:
            with open(param_path, "r", encoding="utf-8") as fdesc:
                if fdesc.read().strip().upper() == "Y":
                    return True
        except OSError:
            pass

    userns_path = "/proc/sys/kernel/apparmor_restrict_unprivileged_userns"
    if os.path.exists(userns_path):
        try:
            with open(userns_path, "r", encoding="utf-8") as fdesc:
                if fdesc.read().strip() == "1":
                    return True
        except OSError:
            pass

    try:
        res = subprocess.run(
            ["aa-enabled"],
            capture_output=True,
            text=True,
            check=False,
        )  # nosec B603, B607
        if res.returncode == 0:
            return True
    except (subprocess.SubprocessError, OSError):
        pass

    return False


def is_suid_sandbox_configured(sandbox_path: str) -> bool:
    """Return True if chrome-sandbox is owned by root:root with mode 4755."""
    try:
        st = os.stat(sandbox_path)
        uid_ok = st.st_uid == 0
        gid_ok = st.st_gid == 0
        mode_ok = bool(st.st_mode & stat_mod.S_ISUID) and (st.st_mode & 0o777) == 0o755
        return uid_ok and gid_ok and mode_ok
    except OSError:
        return False


def can_fix_suid_sandbox() -> tuple[bool, str]:
    """Preflight check: can we actually fix chrome-sandbox permissions?

    Returns (True, "") if we can, or (False, reason) if we cannot.
    Used to bail out early — before downloading anything — when --suid-sandbox
    is requested but we have no way to set root:root 4755.

    Skips entirely on distros not in the sandbox allowlist.
    """
    if not is_ubuntu_sandbox_distro():
        # Not a distro that needs sandbox fixes — always OK.
        return True, ""

    if not is_apparmor_enabled():
        # No AppArmor means no sandbox fix needed at all — always OK.
        return True, ""

    # Already root — can always chown/chmod directly.
    if hasattr(os, "geteuid") and os.geteuid() == 0:
        return True, ""

    # Non-root: check if sudo is available and usable non-interactively.
    try:
        res = subprocess.run(
            ["sudo", "-n", "true"],
            capture_output=True,
            timeout=5,
            check=False,
        )  # nosec B603, B607
        if res.returncode == 0:
            return True, ""
    except (subprocess.SubprocessError, OSError):
        pass

    return (
        False,
        "AppArmor is active and chrome-sandbox requires root:root 4755 permissions, "
        "but you are not root and sudo is not available non-interactively.\n"
        "  Fix options:\n"
        "    1. Run as root:  sudo antigravity-updater --suid-sandbox\n"
        "    2. Or fix manually after install:\n"
        '       sudo chown root:root "$HOME/opt/Antigravity-IDE/chrome-sandbox" && '
        'sudo chmod 4755 "$HOME/opt/Antigravity-IDE/chrome-sandbox"',
    )


def configure_suid_sandbox(app_dir: str) -> bool:
    """Configure root:root 4755 permissions on chrome-sandbox binary if AppArmor is active.

    Checks the current state first:
    - If already correctly configured (root:root 4755), skips with a success message.
    - If misconfigured, attempts to fix via sudo.
    - If fixing fails (no sudo / wrong permissions), prints a loud error with the manual
      fix command and returns False so callers can signal overall failure.

    Only runs on distros in the sandbox allowlist (e.g. Ubuntu).
    """
    if not is_ubuntu_sandbox_distro():
        print_info("Distro does not require SUID sandbox configuration; skipped.")
        return True

    if not is_apparmor_enabled():
        print_info("AppArmor is not active on this system; SUID sandbox configuration skipped.")
        return True

    sandbox_path = os.path.join(app_dir, "chrome-sandbox")
    if not os.path.exists(sandbox_path):
        print_warning(f"chrome-sandbox binary not found at {sandbox_path}")
        return False

    # Check current state — skip if already correctly configured
    if is_suid_sandbox_configured(sandbox_path):
        print_success(f"SUID sandbox already correctly configured: {sandbox_path}")
        return True

    # Misconfigured — try to fix
    is_root = hasattr(os, "geteuid") and os.geteuid() == 0

    try:
        if is_root:
            os.chown(sandbox_path, 0, 0)
            os.chmod(sandbox_path, 0o4755)  # nosec B103
            print_success(f"Configured root:root 4755 permissions on {sandbox_path}")
        else:
            print_info(f"Root privileges required. Requesting sudo for {sandbox_path}...")
            subprocess.run(
                ["sudo", "chown", "root:root", sandbox_path],
                check=True,
            )  # nosec B603, B607
            subprocess.run(
                ["sudo", "chmod", "4755", sandbox_path],
                check=True,
            )  # nosec B603, B607
            print_success(f"Configured root:root 4755 permissions on {sandbox_path}")
    except (subprocess.SubprocessError, OSError) as err:
        print_error(
            f"Cannot fix SUID sandbox permissions on {sandbox_path}: {err}\n"
            f"  The sandbox binary is misconfigured — the application may crash or refuse input.\n"
            f"  Run the following command manually to fix it:\n"
            f'    sudo chown root:root "{sandbox_path}" && sudo chmod 4755 "{sandbox_path}"'
        )
        return False

    return True
