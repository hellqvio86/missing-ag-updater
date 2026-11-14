"""Constants, platform detection, and default paths for missing-ag-updater."""

import os
import platform
import re
import sys
from typing import Optional

OS_RELEASE_PATH = "/etc/os-release"


def _is_ubuntu_style_distro() -> bool:
    if OS_NAME != "linux":
        return False
    try:
        with open(OS_RELEASE_PATH, "r", encoding="utf-8") as fdesc:
            for line in fdesc:
                if line.startswith("ID="):
                    distro_id = line.strip().split("=", 1)[1].strip('"').lower()
                    if distro_id == "ubuntu":
                        return True
                elif line.startswith("ID_LIKE="):
                    distro_like = line.strip().split("=", 1)[1].strip('"').lower()
                    if "ubuntu" in distro_like.split():
                        return True
    except OSError:
        pass
    return False


# Single source of truth for the package version. `pyproject.toml` reads this
# value dynamically via Hatchling (`[tool.hatch.version]`), so bump only here.
__version__ = "0.7.1"

# Truthy and falsy string values for environment variables and config parsing
TRUTHY_VALUES: tuple[str, ...] = ("1", "true", "yes", "on")
FALSY_VALUES: tuple[str, ...] = ("0", "false", "no", "off")

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
    os.system("")  # nosec B605, B607 # Enables VT100 colors in modern Windows terminal
    if not sys.stdout.isatty():
        COLOR_HEADER = COLOR_BLUE = COLOR_GREEN = COLOR_WARNING = COLOR_FAIL = COLOR_ENDC = COLOR_BOLD = ""

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

SYSTEM_APPLICATIONS_DIR = "/usr/share/applications"
SYSTEM_ICONS_DIR = "/usr/share/icons/hicolor/512x512/apps"
SYSTEM_NAUTILUS_DIR = "/usr/share/nautilus-python/extensions"
SYSTEM_OPT_DIR = "/opt"
SYSTEM_BIN_DIR = "/usr/local/bin"

USER_APPLICATIONS_DIR = os.path.join(HOME, ".local", "share", "applications")
USER_ICONS_DIR = os.path.join(HOME, ".local", "share", "icons", "hicolor", "512x512", "apps")
USER_NAUTILUS_DIR = os.path.join(HOME, ".local", "share", "nautilus-python", "extensions")
USER_OPT_DIR = os.path.join(HOME, "opt")
USER_BIN_DIR = os.path.join(HOME, ".local", "bin")

SYSTEM_IDE_DIR: str = ""
SYSTEM_HUB_DIR: str = ""
SYSTEM_CLI_BINARY: str = ""
SYSTEM_IDE_LAUNCHER: Optional[str] = None
SYSTEM_HUB_LAUNCHER: Optional[str] = None

USER_IDE_DIR: str = ""
USER_HUB_DIR: str = ""
USER_CLI_BINARY: str = ""
USER_IDE_LAUNCHER: Optional[str] = None
USER_HUB_LAUNCHER: Optional[str] = None

DEFAULT_IDE_LAUNCHER: Optional[str] = None
DEFAULT_HUB_LAUNCHER: Optional[str] = None

if OS_NAME == "linux":
    OPT_DIR = USER_OPT_DIR
    BIN_DIR = USER_BIN_DIR

    IDE_DIR_NAME = "Antigravity-IDE" if _is_ubuntu_style_distro() else "Antigravity IDE"
    USER_IDE_DIR = os.path.join(USER_OPT_DIR, IDE_DIR_NAME)
    USER_HUB_DIR = os.path.join(USER_OPT_DIR, "Antigravity-x64")
    USER_CLI_BINARY = os.path.join(USER_BIN_DIR, "agy")
    USER_IDE_LAUNCHER = os.path.join(USER_BIN_DIR, "antigravity-ide")
    USER_HUB_LAUNCHER = os.path.join(USER_BIN_DIR, "antigravity")

    SYSTEM_IDE_DIR = "/opt/antigravity-ide"
    SYSTEM_HUB_DIR = "/opt/antigravity"
    SYSTEM_CLI_BINARY = "/usr/local/bin/agy"
    SYSTEM_IDE_LAUNCHER = "/usr/local/bin/antigravity-ide"
    SYSTEM_HUB_LAUNCHER = "/usr/local/bin/antigravity"

    DEFAULT_IDE_DIR = USER_IDE_DIR
    DEFAULT_HUB_DIR = USER_HUB_DIR
    DEFAULT_CLI_BINARY = USER_CLI_BINARY
    DEFAULT_IDE_LAUNCHER = USER_IDE_LAUNCHER
    DEFAULT_HUB_LAUNCHER = USER_HUB_LAUNCHER

elif OS_NAME == "darwin":
    SYSTEM_IDE_DIR = "/Applications/Antigravity IDE.app"
    SYSTEM_HUB_DIR = "/Applications/Antigravity.app"
    SYSTEM_CLI_BINARY = "/usr/local/bin/agy"
    SYSTEM_IDE_LAUNCHER = "/usr/local/bin/antigravity-ide"
    SYSTEM_HUB_LAUNCHER = "/usr/local/bin/antigravity"

    USER_IDE_DIR = os.path.join(HOME, "Applications", "Antigravity IDE.app")
    USER_HUB_DIR = os.path.join(HOME, "Applications", "Antigravity.app")
    USER_CLI_BINARY = os.path.join(HOME, ".local", "bin", "agy")
    USER_IDE_LAUNCHER = os.path.join(HOME, ".local", "bin", "antigravity-ide")
    USER_HUB_LAUNCHER = os.path.join(HOME, ".local", "bin", "antigravity")

    DEFAULT_IDE_DIR = SYSTEM_IDE_DIR
    DEFAULT_HUB_DIR = SYSTEM_HUB_DIR
    DEFAULT_CLI_BINARY = USER_CLI_BINARY
    DEFAULT_IDE_LAUNCHER = USER_IDE_LAUNCHER
    DEFAULT_HUB_LAUNCHER = USER_HUB_LAUNCHER

elif OS_NAME == "windows":
    LOCALAPPDATA = os.environ.get("LOCALAPPDATA", os.path.join(HOME, "AppData", "Local"))
    PROGRAMFILES = os.environ.get("ProgramFiles", "C:\\Program Files")

    USER_IDE_DIR = os.path.join(LOCALAPPDATA, "Programs", "antigravity-ide")
    USER_HUB_DIR = os.path.join(LOCALAPPDATA, "Programs", "antigravity")
    USER_CLI_BINARY = os.path.join(LOCALAPPDATA, "Microsoft", "WindowsApps", "agy.exe")

    SYSTEM_IDE_DIR = os.path.join(PROGRAMFILES, "Antigravity IDE")
    SYSTEM_HUB_DIR = os.path.join(PROGRAMFILES, "Antigravity")
    SYSTEM_CLI_BINARY = os.path.join(PROGRAMFILES, "Antigravity", "agy.exe")

    DEFAULT_IDE_DIR = USER_IDE_DIR
    DEFAULT_HUB_DIR = USER_HUB_DIR
    DEFAULT_CLI_BINARY = USER_CLI_BINARY

else:
    DEFAULT_IDE_DIR = ""
    DEFAULT_HUB_DIR = ""
    DEFAULT_CLI_BINARY = ""

# State directory written by the official `agy` self-updater (contains update.lock / update_status.json)
CLI_SELF_UPDATER_STATE_DIR = os.path.join(HOME, ".gemini", "antigravity-cli", "updater")
CLI_SELF_UPDATER_MARKERS = ("update_status.json", "update.lock")

# API URLs & User Agent
#
# WARNING: These are unofficial, reverse-engineered Google Cloud Run endpoints
# used by the Antigravity desktop clients. They are not documented or supported
# by Google and may move or disappear without notice. Each endpoint can be
# overridden with an environment variable (comma-separated for fallbacks); see
# RELEASE_ENDPOINT_ENV_VARS. The updater reports the attempted URLs and HTTP
# status codes when every endpoint fails.
USER_AGENT = f"missing-ag-updater/{__version__}"
IDE_RELEASES_URL = "https://antigravity-ide-auto-updater-974169037036.us-central1.run.app/releases"
HUB_RELEASES_URL = "https://antigravity-hub-auto-updater-974169037036.us-central1.run.app/releases"
CLI_MANIFEST_URL = (
    f"https://antigravity-cli-auto-updater-974169037036.us-central1.run.app/manifests/{OS_NAME}_{CLI_ARCH}.json"
)

# Ordered release metadata endpoints per component. Environment overrides are
# prepended at runtime by `updater.get_release_endpoints()`.
RELEASE_ENDPOINTS: dict[str, tuple[str, ...]] = {
    "ide": (IDE_RELEASES_URL,),
    "hub": (HUB_RELEASES_URL,),
    "cli": (CLI_MANIFEST_URL,),
}

RELEASE_ENDPOINT_ENV_VARS: dict[str, tuple[str, ...]] = {
    "ide": ("ANTIGRAVITY_IDE_RELEASES_URL", "AG_IDE_RELEASES_URL"),
    "hub": ("ANTIGRAVITY_HUB_RELEASES_URL", "AG_HUB_RELEASES_URL"),
    "cli": ("ANTIGRAVITY_CLI_MANIFEST_URL", "AG_CLI_MANIFEST_URL"),
}

# Download domain allowlist (HTTPS only), enforced by models.is_trusted_download_url()
ALLOWED_HOSTS: frozenset[str] = frozenset(
    {
        "dl.google.com",
        "edgedl.me.gvt1.com",
        "storage.googleapis.com",
    }
)

ALLOWED_HOST_SUFFIXES: tuple[str, ...] = (
    ".google.com",
    ".googleapis.com",
    ".gvt1.com",
    ".googleusercontent.com",
)

HEX_64_PATTERN = re.compile(r"^[0-9a-fA-F]{64}$")
HEX_128_PATTERN = re.compile(r"^[0-9a-fA-F]{128}$")

# Distro allowlist for sandbox features (opt-in per distro)
SANDBOX_DISTROS: frozenset[str] = frozenset({"ubuntu"})

# WSL detection: environment markers and kernel release files containing "microsoft"
WSL_ENV_MARKERS: tuple[str, ...] = ("WSL_DISTRO_NAME", "WSL_INTEROP")
WSL_KERNEL_RELEASE_FILES: tuple[str, ...] = ("/proc/sys/kernel/osrelease", "/proc/version")

# Command lines that belong to the updater itself, test runners, or agent
# daemons. These are never the user-facing application we are about to replace.
IGNORED_PROCESS_SUBSTRINGS: tuple[str, ...] = (
    "missing_ag_updater",
    "missing-ag-updater",
    "antigravity-updater",
    "antigravity-cli",
    "antigravity_daemon",
    ".gemini/antigravity",
    "pytest",
)

# Legacy CDN download base URLs (fallback when release JSON omits explicit URLs)
IDE_DOWNLOAD_BASE_URL = "https://edgedl.me.gvt1.com/edgedl/release2/j0qc3/antigravity/stable"
HUB_DOWNLOAD_BASE_URL = "https://storage.googleapis.com/antigravity-public/antigravity-hub"

# Version parsing pattern
VERSION_DIGITS_PATTERN = re.compile(r"\d+")

# Configuration paths & environment variable mappings
APP_CONFIG_DIR_NAME = "missing-ag-updater"
CONFIG_FILE_NAME = "config.toml"
FALLBACK_CONFIG_FILE_NAME = ".missing-ag-updater.toml"

CONFIG_ENV_VARS: dict[str, tuple[str, ...]] = {
    "config": ("ANTIGRAVITY_CONFIG", "AG_CONFIG"),
    "system": ("ANTIGRAVITY_SYSTEM", "AG_SYSTEM"),
    "user": ("ANTIGRAVITY_USER", "AG_USER"),
    "check": ("ANTIGRAVITY_CHECK", "AG_CHECK"),
    "ide": ("ANTIGRAVITY_IDE", "AG_IDE"),
    "hub": ("ANTIGRAVITY_HUB", "AG_HUB"),
    "cli": ("ANTIGRAVITY_CLI", "AG_CLI"),
    "force": ("ANTIGRAVITY_FORCE", "AG_FORCE"),
    "ignore_self_update": ("ANTIGRAVITY_IGNORE_SELF_UPDATE", "AG_IGNORE_SELF_UPDATE"),
    "allow_unverified": ("ANTIGRAVITY_ALLOW_UNVERIFIED", "AG_ALLOW_UNVERIFIED"),
    "debug": ("ANTIGRAVITY_DEBUG", "AG_DEBUG"),
    "apparmor_sandbox": ("ANTIGRAVITY_APPARMOR_SANDBOX", "AG_APPARMOR_SANDBOX"),
    "dir_ide": ("ANTIGRAVITY_DIR_IDE", "AG_DIR_IDE"),
    "dir_hub": ("ANTIGRAVITY_DIR_HUB", "AG_DIR_HUB"),
    "path_cli": ("ANTIGRAVITY_PATH_CLI", "AG_PATH_CLI"),
    "no_desktop": ("ANTIGRAVITY_NO_DESKTOP", "AG_NO_DESKTOP"),
    "desktop": ("ANTIGRAVITY_DESKTOP", "AG_DESKTOP"),
    "no_nautilus": ("ANTIGRAVITY_NO_NAUTILUS", "AG_NO_NAUTILUS"),
    "nautilus": ("ANTIGRAVITY_NAUTILUS", "AG_NAUTILUS"),
}

# Linux AppArmor sysfs/procfs paths
APPARMOR_ENABLED_PATH = "/sys/module/apparmor/parameters/enabled"
APPARMOR_USERNS_PATH = "/proc/sys/kernel/apparmor_restrict_unprivileged_userns"

# Discovery roots & candidate paths
LINUX_SYSTEM_PATH_ROOTS: tuple[str, ...] = ("/opt", "/usr", "/etc", "/var")
DARWIN_SYSTEM_PATH_ROOTS: tuple[str, ...] = ("/Applications", "/Library", "/usr", "/System")
LINUX_IDE_SYSTEM_CANDIDATES: tuple[str, ...] = (
    "/opt/antigravity-ide/Antigravity-IDE",
    "/opt/Antigravity-IDE",
    "/opt/Antigravity IDE",
    "/usr/lib/antigravity-ide",
    "/usr/share/antigravity-ide",
)
LINUX_HUB_SYSTEM_CANDIDATES: tuple[str, ...] = (
    "/opt/antigravity/Antigravity-x64",
    "/opt/Antigravity-x64",
    "/opt/Antigravity Hub",
    "/usr/lib/antigravity",
)
LINUX_CLI_SYSTEM_CANDIDATES: tuple[str, ...] = ("/usr/bin/agy",)
CLI_SELF_UPDATER_BACKUP_SUFFIX = ".old"

# Desktop, icon, Nautilus, and uninstall naming constants
IDE_DESKTOP_FILENAME = "antigravity-ide.desktop"
HUB_DESKTOP_FILENAME = "antigravity.desktop"
ICON_FILENAME = "antigravity.png"
IDE_ICON_FILENAME = "antigravity-ide.png"
NAUTILUS_EXTENSION_FILENAME = "open-in-antigravity-ide.py"

IDE_PARENT_DIR_NAMES: tuple[str, ...] = ("antigravity-ide", "Antigravity-IDE")
HUB_PARENT_DIR_NAMES: tuple[str, ...] = ("antigravity", "Antigravity")

# Process matching executable name markers
HUB_PROCESS_NAMES: tuple[str, ...] = ("antigravity", "antigravity-hub")
IDE_PROCESS_NAMES: tuple[str, ...] = ("antigravity-ide", "antigravity ide", "code")
