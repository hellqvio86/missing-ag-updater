#!/usr/bin/env python3
"""
Antigravity Applications Auto-Updater
-------------------------------------
A robust Python utility to check, download, and install updates for the
Antigravity IDE, Antigravity Hub (Agent Desktop), and Antigravity CLI.

Author: Antigravity AI Assistant
Date: June 2026
"""

import os
import sys
import json
import urllib.request
import urllib.error
import shutil
import tarfile
import struct
import hashlib
import argparse
import subprocess
import tempfile
from typing import Optional, Dict, Any, Tuple

# Color output helpers for premium terminal feedback
COLOR_HEADER = '\033[95m'
COLOR_BLUE = '\033[94m'
COLOR_GREEN = '\033[92m'
COLOR_WARNING = '\033[93m'
COLOR_FAIL = '\033[91m'
COLOR_ENDC = '\033[0m'
COLOR_BOLD = '\033[1m'

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

# Paths configuration
HOME = os.path.expanduser("~")
OPT_DIR = os.path.join(HOME, "opt")
BIN_DIR = os.path.join(HOME, ".local", "bin")

IDE_DIR = os.path.join(OPT_DIR, "Antigravity IDE")
IDE_LAUNCHER = os.path.join(BIN_DIR, "antigravity-ide")
IDE_RELEASES_URL = "https://antigravity-ide-auto-updater-974169037036.us-central1.run.app/releases"

HUB_DIR = os.path.join(OPT_DIR, "Antigravity-x64")
HUB_LAUNCHER = os.path.join(BIN_DIR, "antigravity")
HUB_RELEASES_URL = "https://antigravity-hub-auto-updater-974169037036.us-central1.run.app/releases"

CLI_BINARY = os.path.join(BIN_DIR, "agy")
CLI_MANIFEST_URL = "https://antigravity-cli-auto-updater-974169037036.us-central1.run.app/manifests/linux_amd64.json"
CLI_RELEASES_URL = "https://antigravity-cli-auto-updater-974169037036.us-central1.run.app/releases"


def is_app_running(keyword: str) -> bool:
    """Check if any running processes match the specified keyword."""
    try:
        res = subprocess.run(["pgrep", "-f", keyword], capture_output=True)
        return res.returncode == 0
    except Exception:
        return False


def get_ide_version() -> str:
    """Read the current local IDE version from product.json."""
    product_json_path = os.path.join(IDE_DIR, "resources", "app", "product.json")
    if not os.path.exists(product_json_path):
        return "0.0.0"
    try:
        with open(product_json_path, 'r', encoding='utf-8') as f:
            product_json = json.load(f)
            return product_json.get("ideVersion", "0.0.0")
    except Exception:
        return "0.0.0"


def get_hub_version() -> str:
    """Read the current local Hub version by parsing app.asar package.json."""
    asar_path = os.path.join(HUB_DIR, "resources", "app.asar")
    if not os.path.exists(asar_path):
        return "0.0.0"
    try:
        with open(asar_path, 'rb') as f:
            header_size_data = f.read(8)
            if len(header_size_data) < 8:
                return "0.0.0"
            header_size = struct.unpack('<I', header_size_data[4:8])[0]
            f.seek(16)
            header_json_data = f.read(header_size - 8)
            header_json = json.loads(header_json_data.decode('utf-8'))
            files = header_json.get('files', {})
            package_json_info = files.get('package.json', {})
            if not package_json_info:
                return "0.0.0"
            offset = int(package_json_info.get('offset'))
            size = int(package_json_info.get('size'))
            data_start_offset = 8 + header_size
            f.seek(data_start_offset + offset)
            pkg_json = json.loads(f.read(size).decode('utf-8'))
            return pkg_json.get('version', "0.0.0")
    except Exception:
        return "0.0.0"


def get_cli_version() -> str:
    """Get the current local CLI version by calling the binary."""
    if not os.path.exists(CLI_BINARY):
        return "0.0.0"
    try:
        res = subprocess.run([CLI_BINARY, "--version"], capture_output=True, text=True, check=True)
        lines = res.stdout.strip().split("\n")
        if lines:
            return lines[0].strip()
        return "0.0.0"
    except Exception:
        return "0.0.0"


def fetch_json(url: str) -> Any:
    """Fetch JSON from a URL with custom user agent headers."""
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0 (AntigravityUpdater)'})
    try:
        with urllib.request.urlopen(req, timeout=10) as response:
            return json.loads(response.read().decode('utf-8'))
    except Exception as e:
        raise RuntimeError(f"Failed to query {url}: {e}")


def download_file(url: str, dest_path: str, label: str = "Downloading"):
    """Download a file with a visually appealing text progress bar."""
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0 (AntigravityUpdater)'})
    try:
        with urllib.request.urlopen(req, timeout=60) as response:
            total_size = int(response.headers.get('content-length', 0))
            block_size = 1024 * 64
            downloaded = 0
            
            with open(dest_path, 'wb') as f:
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
                        bar = '█' * filled_len + '-' * (bar_len - filled_len)
                        sys.stdout.write(f"\r{COLOR_BLUE}⠋{COLOR_ENDC} {label}: [{bar}] {percent}% ({downloaded / 1024 / 1024:.1f}/{total_size / 1024 / 1024:.1f} MB)")
                        sys.stdout.flush()
                sys.stdout.write("\n")
    except Exception as e:
        sys.stdout.write("\n")
        raise RuntimeError(f"Download error from {url}: {e}")


def compute_sha512(file_path: str) -> str:
    """Compute the SHA512 hash of a file."""
    h = hashlib.sha512()
    with open(file_path, 'rb') as f:
        while True:
            chunk = f.read(8192)
            if not chunk:
                break
            h.update(chunk)
    return h.hexdigest()


def update_symlink(target: str, link_name: str):
    """Safely create or update a symbolic link."""
    try:
        if os.path.exists(link_name) or os.path.islink(link_name):
            os.remove(link_name)
        os.makedirs(os.path.dirname(link_name), exist_ok=True)
        os.symlink(target, link_name)
        print_success(f"Linked command: {link_name} -> {target}")
    except Exception as e:
        print_warning(f"Could not update symbolic link {link_name}: {e}")


def update_ide(dry_run: bool = False, force: bool = False) -> bool:
    """Check and execute updates for Antigravity IDE."""
    print_status("Checking for Antigravity IDE updates...")
    current_ver = get_ide_version()
    
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

    download_url = f"https://dl.google.com/release2/j0qc3/antigravity/stable/{latest_ver}-{exec_id}/linux-x64/Antigravity%20IDE.tar.gz"
    
    with tempfile.TemporaryDirectory() as tmpdir:
        archive_path = os.path.join(tmpdir, "ide.tar.gz")
        try:
            download_file(download_url, archive_path, label="Downloading Antigravity IDE")
            print_status("Extracting archive...")
            
            with tarfile.open(archive_path, 'r:gz') as tar:
                tar.extractall(path=tmpdir)
            
            extracted_folder = os.path.join(tmpdir, "Antigravity IDE")
            if not os.path.exists(extracted_folder):
                print_error("Failed to find 'Antigravity IDE' directory inside the archive.")
                return False

            print_status("Installing IDE...")
            os.makedirs(OPT_DIR, exist_ok=True)
            
            # Remove existing IDE directory safely
            if os.path.exists(IDE_DIR):
                shutil.rmtree(IDE_DIR)
                
            shutil.move(extracted_folder, IDE_DIR)
            
            # Ensure symlink in local bin is active
            target_launcher = os.path.join(IDE_DIR, "bin", "antigravity-ide")
            if os.path.exists(target_launcher):
                update_symlink(target_launcher, IDE_LAUNCHER)
                
            print_success(f"Antigravity IDE successfully upgraded to version {latest_ver}!")
            return True
        except Exception as e:
            print_error(f"Failed to upgrade IDE: {e}")
            return False


def update_hub(dry_run: bool = False, force: bool = False) -> bool:
    """Check and execute updates for Antigravity Hub."""
    print_status("Checking for Antigravity Hub updates...")
    current_ver = get_hub_version()
    
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
    if is_app_running("Antigravity-x64/antigravity") or is_app_running("opt/Antigravity-x64"):
        print_warning("Antigravity Hub process is currently running.")
        if not force:
            print_error("Aborting Hub upgrade. Please close the Hub desktop app or run with --force.")
            return False
        print_warning("Proceeding anyway due to --force.")

    download_url = f"https://storage.googleapis.com/antigravity-public/antigravity-hub/{latest_ver}-{exec_id}/linux-x64/Antigravity.tar.gz"
    
    with tempfile.TemporaryDirectory() as tmpdir:
        archive_path = os.path.join(tmpdir, "hub.tar.gz")
        try:
            download_file(download_url, archive_path, label="Downloading Antigravity Hub")
            print_status("Extracting archive...")
            
            with tarfile.open(archive_path, 'r:gz') as tar:
                tar.extractall(path=tmpdir)
            
            extracted_folder = os.path.join(tmpdir, "Antigravity-x64")
            if not os.path.exists(extracted_folder):
                print_error("Failed to find 'Antigravity-x64' directory inside the archive.")
                return False

            print_status("Installing Hub...")
            os.makedirs(OPT_DIR, exist_ok=True)
            
            # Remove existing Hub directory safely
            if os.path.exists(HUB_DIR):
                shutil.rmtree(HUB_DIR)
                
            shutil.move(extracted_folder, HUB_DIR)
            
            # Ensure symlink in local bin is active
            target_launcher = os.path.join(HUB_DIR, "antigravity")
            if os.path.exists(target_launcher):
                update_symlink(target_launcher, HUB_LAUNCHER)
                
            print_success(f"Antigravity Hub successfully upgraded to version {latest_ver}!")
            return True
        except Exception as e:
            print_error(f"Failed to upgrade Hub: {e}")
            return False


def update_cli(dry_run: bool = False, force: bool = False) -> bool:
    """Check and execute updates for Antigravity CLI."""
    print_status("Checking for Antigravity CLI updates...")
    current_ver = get_cli_version()
    
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
        archive_path = os.path.join(tmpdir, "cli.tar.gz")
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
            with tarfile.open(archive_path, 'r:gz') as tar:
                tar.extractall(path=tmpdir)
            
            extracted_binary = os.path.join(tmpdir, "antigravity")
            if not os.path.exists(extracted_binary):
                print_error("Failed to find 'antigravity' binary inside the archive.")
                return False

            print_status("Installing CLI...")
            os.makedirs(BIN_DIR, exist_ok=True)
            
            # Replace local binary
            if os.path.exists(CLI_BINARY):
                os.remove(CLI_BINARY)
                
            shutil.move(extracted_binary, CLI_BINARY)
            os.chmod(CLI_BINARY, 0o755)
            
            print_success(f"Antigravity CLI successfully upgraded to version {latest_ver}!")
            return True
        except Exception as e:
            print_error(f"Failed to upgrade CLI: {e}")
            return False


def main():
    parser = argparse.ArgumentParser(
        description="Auto-updater utility for Google Antigravity developer tools.",
        formatter_class=argparse.RawTextHelpFormatter
    )
    parser.add_argument("--check", action="store_true", help="Check for available updates without installing")
    parser.add_argument("--ide", action="store_true", help="Update only the Antigravity IDE")
    parser.add_argument("--hub", action="store_true", help="Update only the Antigravity Hub")
    parser.add_argument("--cli", action="store_true", help="Update only the Antigravity CLI")
    parser.add_argument("--force", action="store_true", help="Bypass version checks and active process warnings")
    
    args = parser.parse_args()
    
    # If no specific component is selected, default to all components
    update_all = not (args.ide or args.hub or args.cli)
    
    print(f"\n{COLOR_HEADER}{COLOR_BOLD}=== Antigravity Applications Auto-Updater ==={COLOR_ENDC}\n")
    
    success = True
    
    if args.ide or update_all:
        res = update_ide(dry_run=args.check, force=args.force)
        success = success and res
        print()
        
    if args.hub or update_all:
        res = update_hub(dry_run=args.check, force=args.force)
        success = success and res
        print()
        
    if args.cli or update_all:
        res = update_cli(dry_run=args.check, force=args.force)
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
