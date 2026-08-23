"""Update routines for Antigravity IDE, Hub, and CLI."""

import os
import shutil
import subprocess  # nosec B404
import tarfile
import tempfile
import zipfile
from typing import Optional

from .const import (
    ARCH_NAME,
    CLI_MANIFEST_URL,
    COLOR_BOLD,
    COLOR_ENDC,
    HUB_RELEASES_URL,
    IDE_RELEASES_URL,
    OS_NAME,
)
from .desktop import install_hub_desktop, install_ide_desktop
from .discovery import _is_system_path
from .models import CliManifest, Release
from .nautilus import install_ide_nautilus
from .utils import (
    can_fix_suid_sandbox,
    compute_sha256,
    compute_sha512,
    configure_suid_sandbox,
    download_file,
    fetch_json,
    get_cli_version,
    get_hub_version,
    get_ide_version,
    get_running_pids,
    is_path_writable,
    is_ubuntu_sandbox_distro,
    print_error,
    print_info,
    print_status,
    print_success,
    print_warning,
    resolve_existing_hub_dir,
    resolve_existing_ide_dir,
    update_symlink,
)


def install_macos_dmg(dmg_path: str, dest_app_path: str) -> bool:
    """Mount a DMG file, copy the .app bundle to destination, and unmount on macOS."""
    mountpoint = tempfile.mkdtemp(prefix="antigravity_mount_")
    try:
        # Attach DMG with fixed argv and readonly flag (no shell interpretation)
        cmd = [
            "hdiutil",
            "attach",
            "-nobrowse",
            "-readonly",
            "-mountpoint",
            mountpoint,
            dmg_path,
        ]
        subprocess.run(cmd, check=True, capture_output=True)  # nosec B603, B607

        # Locate .app bundle inside the DMG mountpoint
        apps = [filename for filename in os.listdir(mountpoint) if filename.endswith(".app")]
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
    except Exception as err:
        print_error(f"macOS DMG installation failed: {err}")
        return False
    finally:
        # Detach DMG
        try:
            subprocess.run(
                ["hdiutil", "detach", "-force", mountpoint],
                check=False,
                capture_output=True,
            )  # nosec B603, B607
        except Exception:  # nosec B110
            pass
        if os.path.exists(mountpoint):
            try:
                os.rmdir(mountpoint)
            except OSError:
                pass


def install_windows_exe(exe_path: str) -> bool:
    """Launch standard Windows installer silently using static arguments without shell expansion."""
    try:
        print_status("Running silent installer (/S)...")
        # Fixed argument list with explicit /S switch, no shell invocation (shell=False)
        subprocess.run([exe_path, "/S"], check=True)  # nosec B603
        return True
    except Exception as err:
        print_error(f"Windows EXE installation failed: {err}")
        return False


def get_download_url(app_type: str, version: str, exec_id: str) -> str:
    """Get the download URL based on application type, OS, and Architecture."""
    if app_type == "ide":
        if OS_NAME == "linux":
            return (
                f"https://dl.google.com/release2/j0qc3/antigravity/stable/"
                f"{version}-{exec_id}/linux-x64/Antigravity%20IDE.tar.gz"
            )
        elif OS_NAME == "darwin":
            arch = "arm" if ARCH_NAME == "arm64" else "x64"
            return (
                f"https://edgedl.me.gvt1.com/edgedl/release2/j0qc3/antigravity/stable/"
                f"{version}-{exec_id}/darwin-{arch}/Antigravity%20IDE.dmg"
            )
        elif OS_NAME == "windows":
            return (
                f"https://edgedl.me.gvt1.com/edgedl/release2/j0qc3/antigravity/stable/"
                f"{version}-{exec_id}/windows-x64/Antigravity%20IDE.exe"
            )

    elif app_type == "hub":
        if OS_NAME == "linux":
            return (
                f"https://storage.googleapis.com/antigravity-public/antigravity-hub/"
                f"{version}-{exec_id}/linux-x64/Antigravity.tar.gz"
            )
        elif OS_NAME == "darwin":
            arch = "arm" if ARCH_NAME == "arm64" else "x64"
            return (
                f"https://storage.googleapis.com/antigravity-public/antigravity-hub/"
                f"{version}-{exec_id}/darwin-{arch}/Antigravity.dmg"
            )
        elif OS_NAME == "windows":
            return (
                f"https://storage.googleapis.com/antigravity-public/antigravity-hub/"
                f"{version}-{exec_id}/windows-x64/Antigravity-x64.exe"
            )

    return ""


def update_ide(
    ide_dir: str,
    launcher_path: Optional[str],
    *,
    dry_run: bool = False,
    force: bool = False,
    install_desktop: bool = True,
    install_nautilus: bool = True,
    suid_sandbox: bool = False,
    scope: Optional[str] = None,
) -> bool:
    """Check and execute updates for Antigravity IDE."""
    print_status("Checking for Antigravity IDE updates...")
    target_ide_dir = resolve_existing_ide_dir(ide_dir)
    current_ver = get_ide_version(target_ide_dir)
    effective_scope = scope or ("system" if _is_system_path(target_ide_dir) else "user")

    try:
        releases_json = fetch_json(IDE_RELEASES_URL)
        if not releases_json:
            print_error("No IDE releases found from update server.")
            return False

        releases = [Release.model_validate(release_dict) for release_dict in releases_json]
        latest = releases[0]
        latest_ver = latest.version
        exec_id = latest.execution_id
    except Exception as err:
        print_error(f"Failed to check IDE updates: {err}")
        return False

    print_info(f"Target IDE Path:    {COLOR_BOLD}{target_ide_dir}{COLOR_ENDC} ({effective_scope})")
    print_info(f"Local IDE Version:  {COLOR_BOLD}{current_ver}{COLOR_ENDC}")
    print_info(f"Latest IDE Version: {COLOR_BOLD}{latest_ver}{COLOR_ENDC}")

    if current_ver == latest_ver and not force:
        print_success("Antigravity IDE is up to date.")
        if suid_sandbox and OS_NAME == "linux":
            if not configure_suid_sandbox(target_ide_dir):
                return False
        return True

    if dry_run:
        print_warning(f"Update available to version {latest_ver} (Dry Run: skipping installation).")
        return True

    # Process safety checks
    running_pids = get_running_pids("Antigravity IDE") or get_running_pids("antigravity-ide")
    if running_pids:
        pids_str = ", ".join(running_pids)
        print_warning(f"Antigravity IDE process is currently running (PID: {pids_str}).")
        if not force:
            print_error("Aborting IDE upgrade. Please close the IDE or run with --force.")
            return False
        print_warning("Proceeding anyway due to --force.")

    # Permission check
    if not is_path_writable(target_ide_dir):
        print_error(
            f"Permission denied: Target directory '{target_ide_dir}' is not writable.\n"
            f"  To update a system-wide installation in /opt, please run with sudo:\n"
            f"    sudo antigravity-updater\n"
            f"  Or to install a user-level copy in your home directory, run:\n"
            f"    antigravity-updater --user"
        )
        return False

    # Sandbox preflight: fail early before downloading if we cannot fix permissions.
    if suid_sandbox and OS_NAME == "linux":
        ok, reason = can_fix_suid_sandbox()
        if not ok:
            print_error(f"Cannot proceed with --suid-sandbox: {reason}")
            return False

    download_url = get_download_url("ide", latest_ver, exec_id)
    if not download_url:
        print_error(f"No IDE download URL resolved for current platform ({OS_NAME}).")
        return False

    with tempfile.TemporaryDirectory() as tmpdir:
        filename = "ide.dmg" if OS_NAME == "darwin" else ("ide.exe" if OS_NAME == "windows" else "ide.tar.gz")
        archive_path = os.path.join(tmpdir, filename)

        try:
            download_file(download_url, archive_path, label="Downloading Antigravity IDE")

            # Checksum integrity verification when provided by release server
            if latest.sha512:
                print_status("Verifying SHA-512 checksum...")
                actual_sha512 = compute_sha512(archive_path)
                if actual_sha512.lower() != latest.sha512.lower():
                    print_error("Security Check Failure: Checksum mismatch on IDE download archive.")
                    return False
                print_success("Checksum verified.")
            elif latest.sha256:
                print_status("Verifying SHA-256 checksum...")
                actual_sha256 = compute_sha256(archive_path)
                if actual_sha256.lower() != latest.sha256.lower():
                    print_error("Security Check Failure: Checksum mismatch on IDE download archive.")
                    return False
                print_success("Checksum verified.")

            if OS_NAME == "darwin":
                # macOS dmg installation
                res = install_macos_dmg(archive_path, target_ide_dir)
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
                    tar.extractall(path=tmpdir, filter="data")  # nosec B202

                extracted_folder = os.path.join(tmpdir, "Antigravity IDE")
                if not os.path.exists(extracted_folder):
                    extracted_folder = os.path.join(tmpdir, "Antigravity-IDE")
                if not os.path.exists(extracted_folder):
                    subdirs = [subdir for subdir in os.listdir(tmpdir) if os.path.isdir(os.path.join(tmpdir, subdir))]
                    if len(subdirs) == 1:
                        extracted_folder = os.path.join(tmpdir, subdirs[0])
                    else:
                        print_error("Failed to find IDE directory inside the archive.")
                        return False

                print_status("Installing IDE...")
                os.makedirs(os.path.dirname(target_ide_dir), exist_ok=True)
                if os.path.exists(target_ide_dir):
                    shutil.rmtree(target_ide_dir)
                shutil.move(extracted_folder, target_ide_dir)

                # Migrate: remove legacy spaced directory only on Ubuntu-style
                # distros, where the Chromium zygote / SUID sandbox can be
                # affected by stale paths.
                if OS_NAME == "linux" and is_ubuntu_sandbox_distro():
                    legacy_ide_dir = os.path.join(os.path.dirname(target_ide_dir), "Antigravity IDE")
                    if legacy_ide_dir != target_ide_dir and os.path.exists(legacy_ide_dir):
                        print_status("Removing legacy 'Antigravity IDE' directory (migrating to hyphenated path)...")
                        shutil.rmtree(legacy_ide_dir)
                        print_success("Removed legacy directory: " + legacy_ide_dir)

                # Update launchers
                if launcher_path:
                    target_launcher = os.path.join(target_ide_dir, "bin", "antigravity-ide")
                    if os.path.exists(target_launcher):
                        update_symlink(target_launcher, launcher_path)

                if install_desktop and OS_NAME == "linux":
                    install_ide_desktop(
                        ide_dir=target_ide_dir,
                        launcher_path=launcher_path,
                        scope=effective_scope,
                    )

                if install_nautilus and OS_NAME == "linux":
                    install_ide_nautilus(
                        ide_dir=target_ide_dir,
                        launcher_path=launcher_path,
                        scope=effective_scope,
                    )

                if suid_sandbox and OS_NAME == "linux":
                    if not configure_suid_sandbox(target_ide_dir):
                        return False

            print_success(f"Antigravity IDE successfully upgraded to version {latest_ver}!")
            return True
        except Exception as err:
            print_error(f"Failed to upgrade IDE: {err}")
            return False


def update_hub(
    hub_dir: str,
    launcher_path: Optional[str],
    *,
    dry_run: bool = False,
    force: bool = False,
    install_desktop: bool = True,
    suid_sandbox: bool = False,
    scope: Optional[str] = None,
) -> bool:
    """Check and execute updates for Antigravity Hub."""
    print_status("Checking for Antigravity Hub updates...")
    target_hub_dir = resolve_existing_hub_dir(hub_dir)
    current_ver = get_hub_version(target_hub_dir)
    effective_scope = scope or ("system" if _is_system_path(target_hub_dir) else "user")

    try:
        releases_json = fetch_json(HUB_RELEASES_URL)
        if not releases_json:
            print_error("No Hub releases found from update server.")
            return False

        releases = [Release.model_validate(release_dict) for release_dict in releases_json]
        latest = releases[0]
        latest_ver = latest.version
        exec_id = latest.execution_id
    except Exception as err:
        print_error(f"Failed to check Hub updates: {err}")
        return False

    print_info(f"Target Hub Path:   {COLOR_BOLD}{target_hub_dir}{COLOR_ENDC} ({effective_scope})")
    print_info(f"Local Hub Version:  {COLOR_BOLD}{current_ver}{COLOR_ENDC}")
    print_info(f"Latest Hub Version: {COLOR_BOLD}{latest_ver}{COLOR_ENDC}")

    if current_ver == latest_ver and not force:
        print_success("Antigravity Hub is up to date.")
        if suid_sandbox and OS_NAME == "linux":
            if not configure_suid_sandbox(target_hub_dir):
                return False
        return True

    if dry_run:
        print_warning(f"Update available to version {latest_ver} (Dry Run: skipping installation).")
        return True

    # Process safety checks
    running_pids = get_running_pids("Antigravity") or get_running_pids("antigravity")
    if running_pids:
        pids_str = ", ".join(running_pids)
        print_warning(f"Antigravity Hub process is currently running (PID: {pids_str}).")
        if not force:
            print_error("Aborting Hub upgrade. Please close the Hub desktop app or run with --force.")
            return False
        print_warning("Proceeding anyway due to --force.")

    # Permission check
    if not is_path_writable(target_hub_dir):
        print_error(
            f"Permission denied: Target directory '{target_hub_dir}' is not writable.\n"
            f"  To update a system-wide installation in /opt, please run with sudo:\n"
            f"    sudo antigravity-updater\n"
            f"  Or to install a user-level copy in your home directory, run:\n"
            f"    antigravity-updater --user"
        )
        return False

    # Sandbox preflight: fail early before downloading if we cannot fix permissions.
    if suid_sandbox and OS_NAME == "linux":
        ok, reason = can_fix_suid_sandbox()
        if not ok:
            print_error(f"Cannot proceed with sandbox fix: {reason}")
            return False

    download_url = get_download_url("hub", latest_ver, exec_id)
    if not download_url:
        print_error(f"No Hub download URL resolved for current platform ({OS_NAME}).")
        return False

    with tempfile.TemporaryDirectory() as tmpdir:
        filename = "hub.dmg" if OS_NAME == "darwin" else ("hub.exe" if OS_NAME == "windows" else "hub.tar.gz")
        archive_path = os.path.join(tmpdir, filename)

        try:
            download_file(download_url, archive_path, label="Downloading Antigravity Hub")

            # Checksum integrity verification when provided by release server
            if latest.sha512:
                print_status("Verifying SHA-512 checksum...")
                actual_sha512 = compute_sha512(archive_path)
                if actual_sha512.lower() != latest.sha512.lower():
                    print_error("Security Check Failure: Checksum mismatch on Hub download archive.")
                    return False
                print_success("Checksum verified.")
            elif latest.sha256:
                print_status("Verifying SHA-256 checksum...")
                actual_sha256 = compute_sha256(archive_path)
                if actual_sha256.lower() != latest.sha256.lower():
                    print_error("Security Check Failure: Checksum mismatch on Hub download archive.")
                    return False
                print_success("Checksum verified.")

            if OS_NAME == "darwin":
                # macOS dmg installation
                res = install_macos_dmg(archive_path, target_hub_dir)
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
                    tar.extractall(path=tmpdir, filter="data")  # nosec B202

                extracted_folder = os.path.join(tmpdir, "Antigravity-x64")
                if not os.path.exists(extracted_folder):
                    print_error("Failed to find 'Antigravity-x64' directory inside the archive.")
                    return False

                print_status("Installing Hub...")
                os.makedirs(os.path.dirname(target_hub_dir), exist_ok=True)
                if os.path.exists(target_hub_dir):
                    shutil.rmtree(target_hub_dir)
                shutil.move(extracted_folder, target_hub_dir)

                # Update launchers
                if launcher_path:
                    target_launcher = os.path.join(target_hub_dir, "antigravity")
                    if os.path.exists(target_launcher):
                        update_symlink(target_launcher, launcher_path)

                if install_desktop and OS_NAME == "linux":
                    install_hub_desktop(
                        hub_dir=target_hub_dir,
                        launcher_path=launcher_path,
                        scope=effective_scope,
                    )

                if suid_sandbox and OS_NAME == "linux":
                    if not configure_suid_sandbox(target_hub_dir):
                        return False

            print_success(f"Antigravity Hub successfully upgraded to version {latest_ver}!")
            return True
        except Exception as err:
            print_error(f"Failed to upgrade Hub: {err}")
            return False


def update_cli(
    cli_binary: str,
    *,
    dry_run: bool = False,
    force: bool = False,
    scope: Optional[str] = None,
) -> bool:
    """Check and execute updates for Antigravity CLI."""
    print_status("Checking for Antigravity CLI updates...")
    current_ver = get_cli_version(cli_binary)
    effective_scope = scope or ("system" if _is_system_path(cli_binary) else "user")

    try:
        manifest_json = fetch_json(CLI_MANIFEST_URL)
        manifest = CliManifest.model_validate(manifest_json)
        latest_ver = manifest.version
        download_url = manifest.url
        expected_sha512 = manifest.sha512
    except Exception as err:
        print_error(f"Failed to check CLI updates: {err}")
        return False

    print_info(f"Target CLI Path:   {COLOR_BOLD}{cli_binary}{COLOR_ENDC} ({effective_scope})")
    print_info(f"Local CLI Version:  {COLOR_BOLD}{current_ver}{COLOR_ENDC}")
    print_info(f"Latest CLI Version: {COLOR_BOLD}{latest_ver}{COLOR_ENDC}")

    if current_ver == latest_ver and not force:
        print_success("Antigravity CLI is up to date.")
        return True

    if dry_run:
        print_warning(f"Update available to version {latest_ver} (Dry Run: skipping installation).")
        return True

    # Permission check
    if not is_path_writable(cli_binary):
        print_error(
            f"Permission denied: Target CLI path '{cli_binary}' is not writable.\n"
            f"  To update a system-wide binary in /usr/local/bin, please run with sudo:\n"
            f"    sudo antigravity-updater\n"
            f"  Or to install to user ~/.local/bin, run:\n"
            f"    antigravity-updater --user"
        )
        return False

    if not expected_sha512:
        print_error("Security Check Failure: CLI manifest does not provide an integrity checksum (sha512).")
        return False

    with tempfile.TemporaryDirectory() as tmpdir:
        archive_path = os.path.join(tmpdir, "cli_archive")
        try:
            download_file(download_url, archive_path, label="Downloading Antigravity CLI")

            # Checksum Verification
            print_status("Verifying checksum...")
            actual_sha512 = compute_sha512(archive_path)
            if actual_sha512.lower() != expected_sha512.lower():
                print_error("Security Check Failure: Checksum mismatch on CLI download archive.")
                return False
            print_success("Checksum verified.")

            print_status("Extracting archive...")

            binary_name = "agy.exe" if OS_NAME == "windows" else "antigravity"
            extracted_binary = os.path.join(tmpdir, binary_name)

            # Handle Windows .zip vs Unix .tar.gz
            if download_url.endswith(".zip"):
                with zipfile.ZipFile(archive_path, "r") as zip_ref:
                    for member in zip_ref.infolist():
                        # Prevent path traversal
                        target_path = os.path.abspath(os.path.join(tmpdir, member.filename))
                        if not target_path.startswith(
                            os.path.abspath(tmpdir) + os.sep
                        ) and target_path != os.path.abspath(tmpdir):
                            print_error(f"Unsafe path in zip archive: {member.filename}")
                            return False
                    zip_ref.extractall(tmpdir)  # nosec B202
            else:
                with tarfile.open(archive_path, "r:gz") as tar:
                    tar.extractall(path=tmpdir, filter="data")  # nosec B202

            if not os.path.exists(extracted_binary):
                # Try finding any file that matches 'antigravity' or 'agy' in the directory
                potential = [
                    os.path.join(tmpdir, filename)
                    for filename in os.listdir(tmpdir)
                    if filename.startswith("antigravity") or filename.startswith("agy")
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
                os.chmod(cli_binary, 0o755)  # nosec B103

            print_success(f"Antigravity CLI successfully upgraded to version {latest_ver}!")
            return True
        except Exception as err:
            print_error(f"Failed to upgrade CLI: {err}")
            return False
