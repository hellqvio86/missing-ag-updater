import importlib
from unittest.mock import patch

import missing_ag_updater.const


def test_const_darwin() -> None:
    with patch("sys.platform", "darwin"):
        with patch("platform.machine", return_value="arm64"):
            importlib.reload(missing_ag_updater.const)
            assert missing_ag_updater.const.OS_NAME == "darwin"
            assert missing_ag_updater.const.ARCH_NAME == "arm64"


def test_const_windows() -> None:
    with patch("sys.platform", "win32"):
        with patch("platform.machine", return_value="AMD64"):
            with patch.dict("os.environ", {"LOCALAPPDATA": "C:\\Users\\test\\AppData\\Local"}):
                # Also mock stdout isatty to cover color logic
                with patch("sys.stdout.isatty", return_value=False):
                    importlib.reload(missing_ag_updater.const)
                    assert missing_ag_updater.const.OS_NAME == "windows"
                    assert missing_ag_updater.const.ARCH_NAME == "x64"


def test_const_linux() -> None:
    with patch("sys.platform", "linux"):
        with patch("platform.machine", return_value="x86_64"):
            importlib.reload(missing_ag_updater.const)
            assert missing_ag_updater.const.OS_NAME == "linux"
            assert missing_ag_updater.const.ARCH_NAME == "x64"


def test_const_unknown() -> None:
    with patch("sys.platform", "freebsd"):
        with patch("platform.machine", return_value="unknown-arch"):
            importlib.reload(missing_ag_updater.const)
            assert missing_ag_updater.const.OS_NAME == "unknown"
            assert missing_ag_updater.const.ARCH_NAME == "x64"


def teardown_module() -> None:
    # Reload one final time to restore the module constants to the host state
    importlib.reload(missing_ag_updater.const)
