"""Update routines for Antigravity IDE, Hub, and CLI."""

import os
import shutil
import subprocess  # nosec B404
import tempfile
from typing import Any, Optional

from .const import (
    ARCH_NAME,
    COLOR_BOLD,
    COLOR_ENDC,
    HUB_DOWNLOAD_BASE_URL,
    IDE_DOWNLOAD_BASE_URL,
    OS_NAME,
    RELEASE_ENDPOINT_ENV_VARS,
    RELEASE_ENDPOINTS,
)
from .desktop import install_hub_desktop, install_ide_desktop
from .discovery import _is_system_path, detect_cli_self_update
from .exceptions import ReleaseEndpointError
from .models import CliManifest, Release, is_trusted_download_url, parse_version_tuple, select_latest_release
from .nautilus import install_ide_nautilus
from .utils import (
    can_fix_suid_sandbox,
    compute_sha256,
    compute_sha512,
    configure_suid_sandbox,
    debug_log,
    download_file,
    fetch_json,
    get_cli_version,
    get_hub_version,
    get_ide_version,
    get_running_pids,
    is_path_writable,
    migrate_legacy_ide_dir,
    print_error,
    print_info,
    print_status,
    print_success,
    print_warning,
    resolve_existing_hub_dir,
    resolve_existing_ide_dir,
    safe_extract_tar,
    safe_extract_zip,
    update_symlink,
)


def get_release_endpoints(component: str) -> list[str]:
    """Return ordered release metadata URLs for a component.

    Environment variables (comma-separated) are prepended so operators can
    point at a mirror or a replacement endpoint without a code change. The
    built-in endpoint remains as a fallback.
    """
    endpoints: list[str] = []
    for env_name in RELEASE_ENDPOINT_ENV_VARS.get(component, ()):
        raw_value = os.environ.get(env_name)
        if not raw_value:
            continue
        for candidate in raw_value.split(","):
            cleaned = candidate.strip()
            if cleaned and cleaned not in endpoints:
                endpoints.append(cleaned)
    for default_url in RELEASE_ENDPOINTS.get(component, ()):
        if default_url not in endpoints:
            endpoints.append(default_url)
    return endpoints


def fetch_release_payload(component: str) -> Any:
    """Fetch release metadata, trying every configured endpoint with clear errors."""
    attempts: list[tuple[str, str]] = []
    for url in get_release_endpoints(component):
        debug_log(f"release endpoint for {component}: {url}")
        try:
            return fetch_json(url)
        except Exception as err:
            attempts.append((url, str(err)))
            debug_log(f"release endpoint failed for {component}: {url}: {err}")
    raise ReleaseEndpointError(component, attempts)


def _select_release_download_url(release: Release) -> str:
    """Return an explicit, trusted download URL supplied by release metadata, if any."""
    for candidate in (release.download_url, release.url):
        if candidate and is_trusted_download_url(candidate):
            debug_log(f"using explicit release download URL: {candidate}")
            return candidate

    if release.downloads:
        platform_arch = "arm" if ARCH_NAME == "arm64" and OS_NAME == "linux" else ARCH_NAME
        keys = (
            f"{OS_NAME}-{ARCH_NAME}",
            f"{OS_NAME}-{platform_arch}",
            OS_NAME,
            "default",
        )
        for key in keys:
            candidate = release.downloads.get(key)
            if candidate and is_trusted_download_url(candidate):
                debug_log(f"using release download URL for '{key}': {candidate}")
                return candidate

    return ""


def get_download_url(component: str, version: str, exec_id: str, release: Optional[Release] = None) -> str:
    """Resolve the official HTTPS Google download URL for an Antigravity artifact.

    Full URLs supplied by the release JSON are preferred; the historical
    hard-coded CDN paths remain as a fallback for older manifests.
    """
    if release is not None:
        explicit_url = _select_release_download_url(release)
        if explicit_url:
            return explicit_url

    arch = "arm" if ARCH_NAME == "arm64" else "x64"

    if component == "ide":
        if OS_NAME == "linux":
            return f"{IDE_DOWNLOAD_BASE_URL}/{version}-{exec_id}/linux-{arch}/Antigravity%20IDE.tar.gz"
        elif OS_NAME == "darwin":
            return f"{IDE_DOWNLOAD_BASE_URL}/{version}-{exec_id}/darwin-{arch}/Antigravity%20IDE.dmg"
        elif OS_NAME == "windows":
            win_arch = "arm64" if ARCH_NAME == "arm64" else "x64"
            return f"{IDE_DOWNLOAD_BASE_URL}/{version}-{exec_id}/windows-{win_arch}/Antigravity%20IDE.exe"

    elif component == "hub":
        if OS_NAME == "linux":
            return f"{HUB_DOWNLOAD_BASE_URL}/{version}-{exec_id}/linux-{arch}/Antigravity.tar.gz"
        elif OS_NAME == "darwin":
            return f"{HUB_DOWNLOAD_BASE_URL}/{version}-{exec_id}/darwin-{arch}/Antigravity.dmg"
        elif OS_NAME == "windows":
            if ARCH_NAME == "arm64":
                return f"{HUB_DOWNLOAD_BASE_URL}/{version}-{exec_id}/windows-arm/Antigravity-arm64.exe"
            return f"{HUB_DOWNLOAD_BASE_URL}/{version}-{exec_id}/windows-x64/Antigravity-x64.exe"

    return ""


def install_windows_exe(exe_path: str) -> bool:
    """Run Windows silent installer executable with fixed argument vector."""
    print_status("Running Windows installer silently...")
    try:
        # Structured argv execution without shell interpretation prevents shell injection attacks.
        # Fixed arguments execute the verified installer binary directly in silent mode.
        subprocess.run([exe_path, "/S"], check=True)  # nosec B603
        print_success("Windows installer completed.")
        return True
    except (subprocess.SubprocessError, OSError, Exception) as err:
        print_error(f"Windows installer failed: {err}")
        return False


def install_macos_dmg(dmg_path: str, target_app_dir: str) -> bool:
    """Mount macOS DMG, copy .app bundle to target location, and unmount."""
    print_status("Mounting DMG image...")
    mount_point = tempfile.mkdtemp(prefix="antigravity_mount_")
    try:
        cmd = ["hdiutil", "attach", dmg_path, "-mountpoint", mount_point, "-nobrowse", "-quiet"]
        subprocess.run(cmd, check=True)  # nosec B603
    except Exception as err:
        print_error(f"Failed to mount DMG: {err}")
        try:
            os.rmdir(mount_point)
        except OSError:
            pass
        return False

    try:
        app_bundles = [d for d in os.listdir(mount_point) if d.endswith(".app")]
        if not app_bundles:
            print_error("No .app bundle found inside mounted DMG.")
            return False

        source_app = os.path.join(mount_point, app_bundles[0])
        print_status(f"Installing {app_bundles[0]} -> {target_app_dir}...")

        if os.path.exists(target_app_dir):
            shutil.rmtree(target_app_dir)

        shutil.copytree(source_app, target_app_dir, symlinks=True)
        print_success(f"Copied application bundle to {target_app_dir}")
        return True
    except Exception as err:
        print_error(f"Failed to copy application from DMG: {err}")
        return False
    finally:
        print_status("Unmounting DMG image...")
        subprocess.run(["hdiutil", "detach", mount_point, "-quiet"], check=False)  # nosec B603
        try:
            os.rmdir(mount_point)
        except OSError:
            pass


def update_ide(
    ide_dir: str,
    launcher_path: Optional[str],
    *,
    dry_run: bool = False,
    force: bool = False,
    install_desktop: bool = True,
    install_nautilus: bool = True,
    suid_sandbox: bool = False,
    allow_unverified: bool = False,
    scope: Optional[str] = None,
) -> bool:
    """Check and execute updates for Antigravity IDE."""
    print_status("Checking for Antigravity IDE updates...")
    target_ide_dir = migrate_legacy_ide_dir(resolve_existing_ide_dir(ide_dir))
    current_ver = get_ide_version(target_ide_dir)
    effective_scope = scope or ("system" if _is_system_path(target_ide_dir) else "user")
    debug_log(f"IDE target={target_ide_dir} current={current_ver} scope={effective_scope}")

    try:
        releases_json = fetch_release_payload("ide")
        if not releases_json:
            print_error("No IDE releases found from update server.")
            return False

        releases = [Release.model_validate(release_dict) for release_dict in releases_json]
        latest = select_latest_release(releases)
        if not latest:
            print_error("No valid IDE release versions discovered.")
            return False
        latest_ver = latest.version
        exec_id = latest.execution_id
    except Exception as err:
        print_error(f"Failed to check IDE updates: {err}")
        return False

    print_info(f"Target IDE Path:    {COLOR_BOLD}{target_ide_dir}{COLOR_ENDC} ({effective_scope})")
    print_info(f"Local IDE Version:  {COLOR_BOLD}{current_ver}{COLOR_ENDC}")
    print_info(f"Latest IDE Version: {COLOR_BOLD}{latest_ver}{COLOR_ENDC}")

    parsed_current = parse_version_tuple(current_ver)
    parsed_latest = parse_version_tuple(latest_ver)

    if not force and parsed_latest <= parsed_current and current_ver != "0.0.0":
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

    download_url = get_download_url("ide", latest_ver, exec_id, latest)
    if not download_url:
        print_error(f"No IDE download URL resolved for current platform ({OS_NAME}).")
        return False

    with tempfile.TemporaryDirectory() as tmpdir:
        filename = "ide.dmg" if OS_NAME == "darwin" else ("ide.exe" if OS_NAME == "windows" else "ide.tar.gz")
        archive_path = os.path.join(tmpdir, filename)

        try:
            download_file(download_url, archive_path, label="Downloading Antigravity IDE")

            # Checksum integrity verification: fail closed unless explicitly overridden.
            if latest.sha512:
                print_status("Verifying SHA-512 checksum...")
                actual_sha512 = compute_sha512(archive_path)
                debug_log(f"IDE SHA-512 expected={latest.sha512} actual={actual_sha512}")
                if actual_sha512.lower() != latest.sha512.lower():
                    print_error("Security Check Failure: Checksum mismatch on IDE download archive.")
                    return False
                print_success("Checksum verified.")
            elif latest.sha256:
                print_status("Verifying SHA-256 checksum...")
                actual_sha256 = compute_sha256(archive_path)
                debug_log(f"IDE SHA-256 expected={latest.sha256} actual={actual_sha256}")
                if actual_sha256.lower() != latest.sha256.lower():
                    print_error("Security Check Failure: Checksum mismatch on IDE download archive.")
                    return False
                print_success("Checksum verified.")
            elif not allow_unverified:
                print_error(
                    "Security Check Failure: the IDE release server supplied no SHA-512 or SHA-256 checksum.\n"
                    "  Refusing to install an unverified archive. Re-run with --allow-unverified only if you\n"
                    "  understand and accept the risk."
                )
                return False
            else:
                print_warning(
                    "No integrity checksum provided by release server — installing unverified archive "
                    "because --allow-unverified was set."
                )

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
                if not safe_extract_tar(archive_path, tmpdir):
                    return False

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

                # Transactional installation with rollback guard
                backup_dir: Optional[str] = None
                if os.path.exists(target_ide_dir):
                    backup_dir = f"{target_ide_dir}.backup.{os.getpid()}"
                    if os.path.exists(backup_dir):
                        shutil.rmtree(backup_dir)
                    debug_log(f"IDE install: moving existing install to backup {backup_dir}")
                    os.rename(target_ide_dir, backup_dir)

                try:
                    shutil.move(extracted_folder, target_ide_dir)
                    if not os.path.exists(target_ide_dir):
                        raise RuntimeError("Failed to commit new IDE installation directory.")
                    if backup_dir and os.path.exists(backup_dir):
                        debug_log(f"IDE install: commit succeeded, removing backup {backup_dir}")
                        shutil.rmtree(backup_dir)
                except Exception as install_err:
                    if backup_dir and os.path.exists(backup_dir):
                        print_warning(f"Installation failed ({install_err}); rolling back previous installation...")
                        debug_log(f"IDE install: rollback from {backup_dir}")
                        if os.path.exists(target_ide_dir):
                            shutil.rmtree(target_ide_dir)
                        os.rename(backup_dir, target_ide_dir)
                    raise install_err

                # Update launchers
                if launcher_path:
                    target_launcher = os.path.join(target_ide_dir, "bin", "antigravity-ide")
                    if os.path.exists(target_launcher):
                        if not update_symlink(target_launcher, launcher_path):
                            return False

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
    allow_unverified: bool = False,
    scope: Optional[str] = None,
) -> bool:
    """Check and execute updates for Antigravity Hub."""
    print_status("Checking for Antigravity Hub updates...")
    target_hub_dir = resolve_existing_hub_dir(hub_dir)
    current_ver = get_hub_version(target_hub_dir)
    effective_scope = scope or ("system" if _is_system_path(target_hub_dir) else "user")
    debug_log(f"Hub target={target_hub_dir} current={current_ver} scope={effective_scope}")

    try:
        releases_json = fetch_release_payload("hub")
        if not releases_json:
            print_error("No Hub releases found from update server.")
            return False

        releases = [Release.model_validate(release_dict) for release_dict in releases_json]
        latest = select_latest_release(releases)
        if not latest:
            print_error("No valid Hub release versions discovered.")
            return False
        latest_ver = latest.version
        exec_id = latest.execution_id
    except Exception as err:
        print_error(f"Failed to check Hub updates: {err}")
        return False

    print_info(f"Target Hub Path:    {COLOR_BOLD}{target_hub_dir}{COLOR_ENDC} ({effective_scope})")
    print_info(f"Local Hub Version:  {COLOR_BOLD}{current_ver}{COLOR_ENDC}")
    print_info(f"Latest Hub Version: {COLOR_BOLD}{latest_ver}{COLOR_ENDC}")

    parsed_current = parse_version_tuple(current_ver)
    parsed_latest = parse_version_tuple(latest_ver)

    if not force and parsed_latest <= parsed_current and current_ver != "0.0.0":
        print_success("Antigravity Hub is up to date.")
        if suid_sandbox and OS_NAME == "linux":
            if not configure_suid_sandbox(target_hub_dir):
                return False
        return True

    if dry_run:
        print_warning(f"Update available to version {latest_ver} (Dry Run: skipping installation).")
        return True

    # Process safety checks
    running_pids = get_running_pids("antigravity-hub") or get_running_pids("antigravity")
    if running_pids:
        pids_str = ", ".join(running_pids)
        print_warning(f"Antigravity Hub process is currently running (PID: {pids_str}).")
        if not force:
            print_error("Aborting Hub upgrade. Please close the Hub or run with --force.")
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

    # Sandbox preflight
    if suid_sandbox and OS_NAME == "linux":
        ok, reason = can_fix_suid_sandbox()
        if not ok:
            print_error(f"Cannot proceed with --suid-sandbox: {reason}")
            return False

    download_url = get_download_url("hub", latest_ver, exec_id, latest)
    if not download_url:
        print_error(f"No Hub download URL resolved for current platform ({OS_NAME}).")
        return False

    with tempfile.TemporaryDirectory() as tmpdir:
        filename = "hub.dmg" if OS_NAME == "darwin" else ("hub.exe" if OS_NAME == "windows" else "hub.tar.gz")
        archive_path = os.path.join(tmpdir, filename)

        try:
            download_file(download_url, archive_path, label="Downloading Antigravity Hub")

            # Checksum integrity verification: fail closed unless explicitly overridden.
            if latest.sha512:
                print_status("Verifying SHA-512 checksum...")
                actual_sha512 = compute_sha512(archive_path)
                debug_log(f"Hub SHA-512 expected={latest.sha512} actual={actual_sha512}")
                if actual_sha512.lower() != latest.sha512.lower():
                    print_error("Security Check Failure: Checksum mismatch on Hub download archive.")
                    return False
                print_success("Checksum verified.")
            elif latest.sha256:
                print_status("Verifying SHA-256 checksum...")
                actual_sha256 = compute_sha256(archive_path)
                debug_log(f"Hub SHA-256 expected={latest.sha256} actual={actual_sha256}")
                if actual_sha256.lower() != latest.sha256.lower():
                    print_error("Security Check Failure: Checksum mismatch on Hub download archive.")
                    return False
                print_success("Checksum verified.")
            elif not allow_unverified:
                print_error(
                    "Security Check Failure: the Hub release server supplied no SHA-512 or SHA-256 checksum.\n"
                    "  Refusing to install an unverified archive. Re-run with --allow-unverified only if you\n"
                    "  understand and accept the risk."
                )
                return False
            else:
                print_warning(
                    "No integrity checksum provided by release server — installing unverified archive "
                    "because --allow-unverified was set."
                )

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
                if not safe_extract_tar(archive_path, tmpdir):
                    return False

                extracted_folder = os.path.join(tmpdir, "Antigravity-x64")
                if not os.path.exists(extracted_folder):
                    extracted_folder = os.path.join(tmpdir, "Antigravity")
                if not os.path.exists(extracted_folder):
                    subdirs = [subdir for subdir in os.listdir(tmpdir) if os.path.isdir(os.path.join(tmpdir, subdir))]
                    if len(subdirs) == 1:
                        extracted_folder = os.path.join(tmpdir, subdirs[0])
                    else:
                        print_error("Failed to find Hub directory inside the archive.")
                        return False

                print_status("Installing Hub...")
                os.makedirs(os.path.dirname(target_hub_dir), exist_ok=True)

                # Transactional installation with rollback guard
                backup_dir = None
                if os.path.exists(target_hub_dir):
                    backup_dir = f"{target_hub_dir}.backup.{os.getpid()}"
                    if os.path.exists(backup_dir):
                        shutil.rmtree(backup_dir)
                    os.rename(target_hub_dir, backup_dir)

                try:
                    shutil.move(extracted_folder, target_hub_dir)
                    if not os.path.exists(target_hub_dir):
                        raise RuntimeError("Failed to commit new Hub installation directory.")
                    if backup_dir and os.path.exists(backup_dir):
                        shutil.rmtree(backup_dir)
                except Exception as install_err:
                    if backup_dir and os.path.exists(backup_dir):
                        print_warning(f"Installation failed ({install_err}); rolling back previous installation...")
                        if os.path.exists(target_hub_dir):
                            shutil.rmtree(target_hub_dir)
                        os.rename(backup_dir, target_hub_dir)
                    raise install_err

                # Update launchers
                if launcher_path:
                    target_launcher = os.path.join(target_hub_dir, "antigravity")
                    if os.path.exists(target_launcher):
                        if not update_symlink(target_launcher, launcher_path):
                            return False

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
    ignore_self_update: bool = False,
) -> bool:
    """Check and execute updates for Antigravity CLI.

    When the official `agy` self-updater is detected as managing the binary, the update is skipped
    to avoid fighting it, unless `force` or `ignore_self_update` is set.
    """
    print_status("Checking for Antigravity CLI updates...")
    current_ver = get_cli_version(cli_binary)
    effective_scope = scope or ("system" if _is_system_path(cli_binary) else "user")
    debug_log(f"CLI target={cli_binary} current={current_ver} scope={effective_scope}")

    try:
        manifest_json = fetch_release_payload("cli")
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

    parsed_current = parse_version_tuple(current_ver)
    parsed_latest = parse_version_tuple(latest_ver)

    if not force and parsed_latest <= parsed_current and current_ver != "0.0.0":
        print_success("Antigravity CLI is up to date.")
        return True

    self_update_reason = detect_cli_self_update(cli_binary)
    if self_update_reason:
        if force or ignore_self_update:
            override_flag = "--force" if force else "--ignore-self-update"
            print_warning(
                f"Official CLI self-updater detected ({self_update_reason}); overriding due to {override_flag}."
            )
        else:
            print_info(f"Official CLI self-updater detected ({self_update_reason}).")
            print_warning(
                f"Skipping CLI update to {latest_ver} to avoid conflicting with the official self-updater.\n"
                "  Run 'agy update' to update via the official channel, or force it anyway with:\n"
                "    antigravity-updater --cli --ignore-self-update"
            )
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
            debug_log(f"CLI SHA-512 expected={expected_sha512} actual={actual_sha512}")
            if actual_sha512.lower() != expected_sha512.lower():
                print_error("Security Check Failure: Checksum mismatch on CLI download archive.")
                return False
            print_success("Checksum verified.")

            print_status("Extracting archive...")

            binary_name = "agy.exe" if OS_NAME == "windows" else "antigravity"
            extracted_binary = os.path.join(tmpdir, binary_name)

            # Handle Windows .zip vs Unix .tar.gz
            if download_url.endswith(".zip"):
                if not safe_extract_zip(archive_path, tmpdir):
                    return False
            else:
                if not safe_extract_tar(archive_path, tmpdir):
                    return False

            if not os.path.exists(extracted_binary):
                # Search for known exact binary candidate names
                known_candidates = (
                    "agy.exe",
                    "antigravity.exe",
                    "agy",
                    "antigravity",
                    "bin/agy",
                    "bin/antigravity",
                )
                found = None
                for candidate in known_candidates:
                    candidate_path = os.path.join(tmpdir, candidate)
                    if os.path.exists(candidate_path) and os.path.isfile(candidate_path):
                        found = candidate_path
                        break
                if found:
                    extracted_binary = found
                else:
                    print_error("Failed to find executable binary inside the archive.")
                    return False

            print_status("Installing CLI...")
            target_parent_dir = os.path.dirname(cli_binary)
            os.makedirs(target_parent_dir, exist_ok=True)

            # Atomic staged replacement
            staged_cli_path = os.path.join(
                target_parent_dir,
                f".{os.path.basename(cli_binary)}.tmp.{os.getpid()}",
            )
            shutil.copy2(extracted_binary, staged_cli_path)

            if OS_NAME != "windows":
                os.chmod(staged_cli_path, 0o755)  # nosec B103

            # Atomic rename / replace
            os.replace(staged_cli_path, cli_binary)

            print_success(f"Antigravity CLI successfully upgraded to version {latest_ver}!")
            return True
        except Exception as err:
            print_error(f"Failed to upgrade CLI: {err}")
            return False
