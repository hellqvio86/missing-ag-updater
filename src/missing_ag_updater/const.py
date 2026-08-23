"""Constants, platform detection, and default paths for missing-ag-updater."""

import os
import platform
import sys
from typing import Optional


def _is_ubuntu_style_distro() -> bool:
    if OS_NAME != "linux":
        return False
    try:
        with open("/etc/os-release", "r", encoding="utf-8") as fdesc:
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


__version__ = "0.4.0"

# Truthy string values for environment variables and config parsing
TRUTHY_VALUES: tuple[str, ...] = ("1", "true", "yes", "on")

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

# API URLs & User Agent
USER_AGENT = f"missing-ag-updater/{__version__}"
IDE_RELEASES_URL = "https://antigravity-ide-auto-updater-974169037036.us-central1.run.app/releases"
HUB_RELEASES_URL = "https://antigravity-hub-auto-updater-974169037036.us-central1.run.app/releases"
CLI_MANIFEST_URL = (
    f"https://antigravity-cli-auto-updater-974169037036.us-central1.run.app/manifests/{OS_NAME}_{CLI_ARCH}.json"
)
