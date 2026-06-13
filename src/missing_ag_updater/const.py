import os
import platform
import sys
from typing import Optional

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

USER_APPLICATIONS_DIR = os.path.join(HOME, ".local", "share", "applications")
USER_ICONS_DIR = os.path.join(HOME, ".local", "share", "icons", "hicolor", "512x512", "apps")
USER_NAUTILUS_DIR = os.path.join(HOME, ".local", "share", "nautilus-python", "extensions")

DEFAULT_IDE_LAUNCHER: Optional[str] = None
DEFAULT_HUB_LAUNCHER: Optional[str] = None

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

elif OS_NAME == "windows":
    LOCALAPPDATA = os.environ.get("LOCALAPPDATA", os.path.join(HOME, "AppData", "Local"))
    DEFAULT_IDE_DIR = os.path.join(LOCALAPPDATA, "Programs", "antigravity-ide")
    DEFAULT_HUB_DIR = os.path.join(LOCALAPPDATA, "Programs", "antigravity")
    DEFAULT_CLI_BINARY = os.path.join(LOCALAPPDATA, "Microsoft", "WindowsApps", "agy.exe")

else:
    DEFAULT_IDE_DIR = ""
    DEFAULT_HUB_DIR = ""
    DEFAULT_CLI_BINARY = ""

# API URLs
IDE_RELEASES_URL = "https://antigravity-ide-auto-updater-974169037036.us-central1.run.app/releases"
HUB_RELEASES_URL = "https://antigravity-hub-auto-updater-974169037036.us-central1.run.app/releases"
CLI_MANIFEST_URL = (
    f"https://antigravity-cli-auto-updater-974169037036.us-central1.run.app/manifests/{OS_NAME}_{CLI_ARCH}.json"
)
