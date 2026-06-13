#!/usr/bin/env python3
"""
Antigravity Applications Auto-Updater (Cross-Platform)
-----------------------------------------------------
A robust Python utility to check, download, and install updates for the
Antigravity IDE, Antigravity Hub (Agent Desktop), and Antigravity CLI.
Supports Linux, macOS, and Windows.

Author: Antigravity AI Assistant
Date: June 2026
"""

import argparse
import hashlib
import json
import os
import platform
import shutil
import struct
import subprocess
import sys
import tarfile
import tempfile
import urllib.error
import urllib.request
import zipfile
from typing import Any, Optional

# Color output helpers for premium terminal feedback
COLOR_HEADER = "\033[95m"
COLOR_BLUE = "\033[94m"
COLOR_GREEN = "\033[92m"
COLOR_WARNING = "\033[93m"
COLOR_FAIL = "\033[91m"
COLOR_ENDC = "\033[0m"
COLOR_BOLD = "\033[1m"

# Disable colors on Windows command prompt unless supported
if sys.platform == "win32":
    os.system("")  # Enables VT100 colors in modern Windows terminal
    # If still not working or on older Windows, fallback to no colors
    if not sys.stdout.isatty():
        COLOR_HEADER = COLOR_BLUE = COLOR_GREEN = COLOR_WARNING = COLOR_FAIL = COLOR_ENDC = COLOR_BOLD = ""


def print_status(msg: str):
    print(f"{COLOR_BLUE}⠋{COLOR_ENDC} {msg}")


def print_success(msg: str):
    print(f"{COLOR_GREEN}✓{COLOR_ENDC} {msg}")


def print_warning(msg: str):
    print(f"{COLOR_WARNING}⚠{COLOR_ENDC} {COLOR_WARNING}{msg}{COLOR_ENDC}")


def print_error(msg: str):
    print(f"{COLOR_FAIL}✗{COLOR_ENDC} {COLOR_FAIL}{msg}{COLOR_ENDC}")


def print_info(msg: str):
    print(f"  {msg}")


# OS & Architecture detection
OS = sys.platform
if OS.startswith("linux"):
    OS_NAME = "linux"
elif OS == "darwin":
    OS_NAME = "darwin"
elif OS == "win32":
    OS_NAME = "windows"
else:
    OS_NAME = "unknown"

MACHINE = platform.machine().lower()
if MACHINE in ["amd64", "x86_64", "x64"]:
    ARCH_NAME = "x64"
    CLI_ARCH = "amd64"
elif MACHINE in ["arm64", "aarch64"]:
    ARCH_NAME = "arm64"
    CLI_ARCH = "arm64"
else:
    ARCH_NAME = "x64"
    CLI_ARCH = "amd64"

# Default Paths based on OS
HOME = os.path.expanduser("~")

if OS_NAME == "linux":
    OPT_DIR = os.path.join(HOME, "opt")
    BIN_DIR = os.path.join(HOME, ".local", "bin")

    DEFAULT_IDE_DIR = os.path.join(OPT_DIR, "Antigravity IDE")
    DEFAULT_HUB_DIR = os.path.join(OPT_DIR, "Antigravity-x64")
    DEFAULT_CLI_BINARY = os.path.join(BIN_DIR, "agy")
    DEFAULT_IDE_LAUNCHER = os.path.join(BIN_DIR, "antigravity-ide")
    DEFAULT_HUB_LAUNCHER = os.path.join(BIN_DIR, "antigravity")

elif OS_NAME == "darwin":
    DEFAULT_IDE_DIR = "/Applications/Antigravity IDE.app"
    DEFAULT_HUB_DIR = "/Applications/Antigravity.app"
    DEFAULT_CLI_BINARY = os.path.join(HOME, ".local", "bin", "agy")
    DEFAULT_IDE_LAUNCHER = None
    DEFAULT_HUB_LAUNCHER = None

elif OS_NAME == "windows":
    LOCALAPPDATA = os.environ.get("LOCALAPPDATA", os.path.join(HOME, "AppData", "Local"))
    DEFAULT_IDE_DIR = os.path.join(LOCALAPPDATA, "Programs", "antigravity-ide")
    DEFAULT_HUB_DIR = os.path.join(LOCALAPPDATA, "Programs", "antigravity")
    DEFAULT_CLI_BINARY = os.path.join(LOCALAPPDATA, "Microsoft", "WindowsApps", "agy.exe")
    DEFAULT_IDE_LAUNCHER = None
    DEFAULT_HUB_LAUNCHER = None

else:
    DEFAULT_IDE_DIR = ""
    DEFAULT_HUB_DIR = ""
    DEFAULT_CLI_BINARY = ""
    DEFAULT_IDE_LAUNCHER = None
    DEFAULT_HUB_LAUNCHER = None

# API URLs
IDE_RELEASES_URL = "https://antigravity-ide-auto-updater-974169037036.us-central1.run.app/releases"
HUB_RELEASES_URL = "https://antigravity-hub-auto-updater-974169037036.us-central1.run.app/releases"
CLI_MANIFEST_URL = (
    f"https://antigravity-cli-auto-updater-974169037036.us-central1.run.app/manifests/{OS_NAME}_{CLI_ARCH}.json"
)


def is_app_running(keyword: str) -> bool:
    """Check if any running processes match the specified keyword."""
    if OS_NAME == "windows":
        try:
            res = subprocess.run(["tasklist"], capture_output=True, text=True)
            return keyword.lower() in res.stdout.lower()
        except Exception:
            return False
    else:
        try:
            res = subprocess.run(["pgrep", "-f", keyword], capture_output=True)
            return res.returncode == 0
        except Exception:
            return False


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


def download_file(url: str, dest_path: str, label: str = "Downloading"):
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


def update_symlink(target: str, link_name: str):
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


def install_macos_dmg(dmg_path: str, dest_app_path: str) -> bool:
    """Mount a DMG file, copy the .app bundle to destination, and unmount on macOS."""
    mountpoint = tempfile.mkdtemp(prefix="antigravity_mount_")
    try:
        # Attach DMG
        cmd = ["hdiutil", "attach", "-nobrowse", "-readonly", "-mountpoint", mountpoint, dmg_path]
        subprocess.run(cmd, check=True, capture_output=True)

        # Locate .app bundle inside the DMG mountpoint
        apps = [f for f in os.listdir(mountpoint) if f.endswith(".app")]
        if not apps:
            print_error("No .app bundle found in the mounted DMG.")
            return False

        source_app = os.path.join(mountpoint, apps[0])
        print_status(f"Installing {apps[0]} to {dest_app_path}...")

        # Replace existing app bundle
        if os.path.exists(dest_app_path):
            shutil.rmtree(dest_app_path)

        shutil.copytree(source_app, dest_app_path, symlinks=True)
        return True
    except Exception as e:
        print_error(f"macOS DMG installation failed: {e}")
        return False
    finally:
        # Detach DMG
        try:
            subprocess.run(["hdiutil", "detach", "-force", mountpoint], capture_output=True)
        except Exception:
            pass
        if os.path.exists(mountpoint):
            os.rmdir(mountpoint)


def install_windows_exe(exe_path: str) -> bool:
    """Launch standard Windows installer silently."""
    try:
        print_status("Running silent installer (/S)...")
        subprocess.run([exe_path, "/S"], check=True)
        return True
    except Exception as e:
        print_error(f"Windows EXE installation failed: {e}")
        return False


def get_download_url(app_type: str, version: str, exec_id: str) -> str:
    """Get the download URL based on application type, OS, and Architecture."""
    if app_type == "ide":
        if OS_NAME == "linux":
            return f"https://dl.google.com/release2/j0qc3/antigravity/stable/{version}-{exec_id}/linux-x64/Antigravity%20IDE.tar.gz"
        elif OS_NAME == "darwin":
            arch = "arm" if ARCH_NAME == "arm64" else "x64"
            return f"https://edgedl.me.gvt1.com/edgedl/release2/j0qc3/antigravity/stable/{version}-{exec_id}/darwin-{arch}/Antigravity%20IDE.dmg"
        elif OS_NAME == "windows":
            return f"https://edgedl.me.gvt1.com/edgedl/release2/j0qc3/antigravity/stable/{version}-{exec_id}/windows-x64/Antigravity%20IDE.exe"

    elif app_type == "hub":
        if OS_NAME == "linux":
            return f"https://storage.googleapis.com/antigravity-public/antigravity-hub/{version}-{exec_id}/linux-x64/Antigravity.tar.gz"
        elif OS_NAME == "darwin":
            arch = "arm" if ARCH_NAME == "arm64" else "x64"
            return f"https://storage.googleapis.com/antigravity-public/antigravity-hub/{version}-{exec_id}/darwin-{arch}/Antigravity.dmg"
        elif OS_NAME == "windows":
            return f"https://storage.googleapis.com/antigravity-public/antigravity-hub/{version}-{exec_id}/windows-x64/Antigravity-x64.exe"

    return ""


def update_ide(ide_dir: str, launcher_path: Optional[str], dry_run: bool = False, force: bool = False) -> bool:
    """Check and execute updates for Antigravity IDE."""
    print_status("Checking for Antigravity IDE updates...")
    current_ver = get_ide_version(ide_dir)

    try:
        releases = fetch_json(IDE_RELEASES_URL)
        if not releases:
            print_error("No IDE releases found from update server.")
            return False

        latest = releases[0]
        latest_ver = latest["version"]
        exec_id = latest["execution_id"]
    except Exception as e:
        print_error(f"Failed to check IDE updates: {e}")
        return False

    print_info(f"Local IDE Version:  {COLOR_BOLD}{current_ver}{COLOR_ENDC}")
    print_info(f"Latest IDE Version: {COLOR_BOLD}{latest_ver}{COLOR_ENDC}")

    if current_ver == latest_ver and not force:
        print_success("Antigravity IDE is up to date.")
        return True

    if dry_run:
        print_warning(f"Update available to version {latest_ver} (Dry Run: skipping installation).")
        return True

    # Process safety checks
    if is_app_running("Antigravity IDE") or is_app_running("antigravity-ide"):
        print_warning("Antigravity IDE process is currently running.")
        if not force:
            print_error("Aborting IDE upgrade. Please close the IDE or run with --force.")
            return False
        print_warning("Proceeding anyway due to --force.")

    download_url = get_download_url("ide", latest_ver, exec_id)
    if not download_url:
        print_error(f"No IDE download URL resolved for current platform ({OS_NAME}).")
        return False

    with tempfile.TemporaryDirectory() as tmpdir:
        filename = "ide.dmg" if OS_NAME == "darwin" else ("ide.exe" if OS_NAME == "windows" else "ide.tar.gz")
        archive_path = os.path.join(tmpdir, filename)

        try:
            download_file(download_url, archive_path, label="Downloading Antigravity IDE")

            if OS_NAME == "darwin":
                # macOS dmg installation
                res = install_macos_dmg(archive_path, ide_dir)
                if not res:
                    return False
            elif OS_NAME == "windows":
                # Windows exe installation
                res = install_windows_exe(archive_path)
                if not res:
                    return False
            else:
                # Linux tarball installation
                print_status("Extracting archive...")
                with tarfile.open(archive_path, "r:gz") as tar:
                    tar.extractall(path=tmpdir)

                extracted_folder = os.path.join(tmpdir, "Antigravity IDE")
                if not os.path.exists(extracted_folder):
                    print_error("Failed to find 'Antigravity IDE' directory inside the archive.")
                    return False

                print_status("Installing IDE...")
                os.makedirs(os.path.dirname(ide_dir), exist_ok=True)
                if os.path.exists(ide_dir):
                    shutil.rmtree(ide_dir)
                shutil.move(extracted_folder, ide_dir)

                # Update launchers
                if launcher_path:
                    target_launcher = os.path.join(ide_dir, "bin", "antigravity-ide")
                    if os.path.exists(target_launcher):
                        update_symlink(target_launcher, launcher_path)

            print_success(f"Antigravity IDE successfully upgraded to version {latest_ver}!")
            return True
        except Exception as e:
            print_error(f"Failed to upgrade IDE: {e}")
            return False


def update_hub(hub_dir: str, launcher_path: Optional[str], dry_run: bool = False, force: bool = False) -> bool:
    """Check and execute updates for Antigravity Hub."""
    print_status("Checking for Antigravity Hub updates...")
    current_ver = get_hub_version(hub_dir)

    try:
        releases = fetch_json(HUB_RELEASES_URL)
        if not releases:
            print_error("No Hub releases found from update server.")
            return False

        latest = releases[0]
        latest_ver = latest["version"]
        exec_id = latest["execution_id"]
    except Exception as e:
        print_error(f"Failed to check Hub updates: {e}")
        return False

    print_info(f"Local Hub Version:  {COLOR_BOLD}{current_ver}{COLOR_ENDC}")
    print_info(f"Latest Hub Version: {COLOR_BOLD}{latest_ver}{COLOR_ENDC}")

    if current_ver == latest_ver and not force:
        print_success("Antigravity Hub is up to date.")
        return True

    if dry_run:
        print_warning(f"Update available to version {latest_ver} (Dry Run: skipping installation).")
        return True

    # Process safety checks
    if is_app_running("Antigravity") or is_app_running("antigravity"):
        print_warning("Antigravity Hub process is currently running.")
        if not force:
            print_error("Aborting Hub upgrade. Please close the Hub desktop app or run with --force.")
            return False
        print_warning("Proceeding anyway due to --force.")

    download_url = get_download_url("hub", latest_ver, exec_id)
    if not download_url:
        print_error(f"No Hub download URL resolved for current platform ({OS_NAME}).")
        return False

    with tempfile.TemporaryDirectory() as tmpdir:
        filename = "hub.dmg" if OS_NAME == "darwin" else ("hub.exe" if OS_NAME == "windows" else "hub.tar.gz")
        archive_path = os.path.join(tmpdir, filename)

        try:
            download_file(download_url, archive_path, label="Downloading Antigravity Hub")

            if OS_NAME == "darwin":
                # macOS dmg installation
                res = install_macos_dmg(archive_path, hub_dir)
                if not res:
                    return False
            elif OS_NAME == "windows":
                # Windows exe installation
                res = install_windows_exe(archive_path)
                if not res:
                    return False
            else:
                # Linux tarball installation
                print_status("Extracting archive...")
                with tarfile.open(archive_path, "r:gz") as tar:
                    tar.extractall(path=tmpdir)

                extracted_folder = os.path.join(tmpdir, "Antigravity-x64")
                if not os.path.exists(extracted_folder):
                    print_error("Failed to find 'Antigravity-x64' directory inside the archive.")
                    return False

                print_status("Installing Hub...")
                os.makedirs(os.path.dirname(hub_dir), exist_ok=True)
                if os.path.exists(hub_dir):
                    shutil.rmtree(hub_dir)
                shutil.move(extracted_folder, hub_dir)

                # Update launchers
                if launcher_path:
                    target_launcher = os.path.join(hub_dir, "antigravity")
                    if os.path.exists(target_launcher):
                        update_symlink(target_launcher, launcher_path)

            print_success(f"Antigravity Hub successfully upgraded to version {latest_ver}!")
            return True
        except Exception as e:
            print_error(f"Failed to upgrade Hub: {e}")
            return False


def update_cli(cli_binary: str, dry_run: bool = False, force: bool = False) -> bool:
    """Check and execute updates for Antigravity CLI."""
    print_status("Checking for Antigravity CLI updates...")
    current_ver = get_cli_version(cli_binary)

    try:
        manifest = fetch_json(CLI_MANIFEST_URL)
        latest_ver = manifest["version"]
        download_url = manifest["url"]
        expected_sha512 = manifest.get("sha512")
    except Exception as e:
        print_error(f"Failed to check CLI updates: {e}")
        return False

    print_info(f"Local CLI Version:  {COLOR_BOLD}{current_ver}{COLOR_ENDC}")
    print_info(f"Latest CLI Version: {COLOR_BOLD}{latest_ver}{COLOR_ENDC}")

    if current_ver == latest_ver and not force:
        print_success("Antigravity CLI is up to date.")
        return True

    if dry_run:
        print_warning(f"Update available to version {latest_ver} (Dry Run: skipping installation).")
        return True

    with tempfile.TemporaryDirectory() as tmpdir:
        archive_path = os.path.join(tmpdir, "cli_archive")
        try:
            download_file(download_url, archive_path, label="Downloading Antigravity CLI")

            # Checksum Verification
            if expected_sha512:
                print_status("Verifying checksum...")
                actual_sha512 = compute_sha512(archive_path)
                if actual_sha512 != expected_sha512:
                    print_error("Security Check Failure: Checksum mismatch on CLI download archive.")
                    return False
                print_success("Checksum verified.")

            print_status("Extracting archive...")

            binary_name = "agy.exe" if OS_NAME == "windows" else "antigravity"
            extracted_binary = os.path.join(tmpdir, binary_name)

            # Handle Windows .zip vs Unix .tar.gz
            if download_url.endswith(".zip"):
                with zipfile.ZipFile(archive_path, "r") as zip_ref:
                    zip_ref.extractall(tmpdir)
            else:
                with tarfile.open(archive_path, "r:gz") as tar:
                    tar.extractall(path=tmpdir)

            if not os.path.exists(extracted_binary):
                # Try finding any file that matches 'antigravity' or 'agy' in the directory
                potential = [
                    os.path.join(tmpdir, f)
                    for f in os.listdir(tmpdir)
                    if f.startswith("antigravity") or f.startswith("agy")
                ]
                if potential:
                    extracted_binary = potential[0]
                else:
                    print_error("Failed to find executable binary inside the archive.")
                    return False

            print_status("Installing CLI...")
            os.makedirs(os.path.dirname(cli_binary), exist_ok=True)

            # Replace local binary
            if os.path.exists(cli_binary):
                os.remove(cli_binary)

            shutil.move(extracted_binary, cli_binary)

            if OS_NAME != "windows":
                os.chmod(cli_binary, 0o755)

            print_success(f"Antigravity CLI successfully upgraded to version {latest_ver}!")
            return True
        except Exception as e:
            print_error(f"Failed to upgrade CLI: {e}")
            return False


def main():
    parser = argparse.ArgumentParser(
        description="Auto-updater utility for Google Antigravity developer tools (Cross-Platform).",
        formatter_class=argparse.RawTextHelpFormatter,
    )
    parser.add_argument("--check", action="store_true", help="Check for available updates without installing")
    parser.add_argument("--ide", action="store_true", help="Update only the Antigravity IDE")
    parser.add_argument("--hub", action="store_true", help="Update only the Antigravity Hub")
    parser.add_argument("--cli", action="store_true", help="Update only the Antigravity CLI")
    parser.add_argument("--force", action="store_true", help="Bypass version checks and active process warnings")
    parser.add_argument(
        "--dir-ide", type=str, default=DEFAULT_IDE_DIR, help="Override path to Antigravity IDE folder/bundle"
    )
    parser.add_argument(
        "--dir-hub", type=str, default=DEFAULT_HUB_DIR, help="Override path to Antigravity Hub folder/bundle"
    )
    parser.add_argument(
        "--path-cli", type=str, default=DEFAULT_CLI_BINARY, help="Override path to Antigravity CLI binary"
    )

    args = parser.parse_args()

    if OS_NAME == "unknown":
        print_error("Unsupported operating system.")
        sys.exit(1)

    # If no specific component is selected, default to all components
    update_all = not (args.ide or args.hub or args.cli)

    print(f"\n{COLOR_HEADER}{COLOR_BOLD}=== Antigravity Applications Auto-Updater ==={COLOR_ENDC}")
    print_info(f"Target Platform: {COLOR_BOLD}{OS_NAME} ({ARCH_NAME}){COLOR_ENDC}\n")

    success = True

    if args.ide or update_all:
        res = update_ide(args.dir_ide, DEFAULT_IDE_LAUNCHER, dry_run=args.check, force=args.force)
        success = success and res
        print()

    if args.hub or update_all:
        res = update_hub(args.dir_hub, DEFAULT_HUB_LAUNCHER, dry_run=args.check, force=args.force)
        success = success and res
        print()

    if args.cli or update_all:
        res = update_cli(args.path_cli, dry_run=args.check, force=args.force)
        success = success and res
        print()

    if success:
        print_success("Operation completed successfully.")
        sys.exit(0)
    else:
        print_error("One or more update operations failed.")
        sys.exit(1)


if __name__ == "__main__":
    main()
