"""Unit tests for platform detection, path resolution, and global constants."""

import importlib
from typing import Generator
from unittest.mock import MagicMock, mock_open, patch

import pytest

import missing_ag_updater.const as constants


@pytest.fixture(autouse=True)
def restore_constants_after_test() -> Generator[None, None, None]:
    """Ensure module-level constants are restored to the host system state after every test."""
    yield
    importlib.reload(constants)


@patch("platform.machine", return_value="arm64")
@patch("sys.platform", "darwin")
def test_constants_darwin_arm64(mock_machine: MagicMock) -> None:
    """macOS ARM64 should detect darwin OS, arm64 architecture, and macOS application bundles."""
    importlib.reload(constants)
    assert constants.OS_NAME == "darwin"
    assert constants.ARCH_NAME == "arm64"
    assert constants.DEFAULT_IDE_DIR == "/Applications/Antigravity IDE.app"
    assert constants.DEFAULT_HUB_DIR == "/Applications/Antigravity.app"


@patch("sys.stdout.isatty", return_value=False)
@patch("platform.machine", return_value="AMD64")
@patch("sys.platform", "win32")
def test_constants_windows_x64(
    mock_isatty: MagicMock,
    mock_machine: MagicMock,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Windows x64 should detect win32 platform, disabled terminal colors when not a TTY, and Windows paths."""
    monkeypatch.setenv("LOCALAPPDATA", "C:\\Users\\test\\AppData\\Local")
    importlib.reload(constants)
    assert constants.OS_NAME == "windows"
    assert constants.ARCH_NAME == "x64"
    assert constants.COLOR_BOLD == ""


@patch("platform.machine", return_value="x86_64")
@patch("sys.platform", "linux")
def test_constants_linux_x64(mock_machine: MagicMock) -> None:
    """Standard Linux x64 platform detection."""
    importlib.reload(constants)
    assert constants.OS_NAME == "linux"
    assert constants.ARCH_NAME == "x64"


@patch("builtins.open", mock_open(read_data='NAME="Ubuntu"\nID=ubuntu\n'))
@patch("os.path.expanduser", return_value="/home/test")
@patch("platform.machine", return_value="x86_64")
@patch("sys.platform", "linux")
def test_constants_linux_ubuntu_hyphenated_directory(
    mock_expand: MagicMock,
    mock_machine: MagicMock,
) -> None:
    """Ubuntu distributions should use hyphenated directory names (Antigravity-IDE)."""
    importlib.reload(constants)
    assert constants.DEFAULT_IDE_DIR == "/home/test/opt/Antigravity-IDE"


@patch("builtins.open", mock_open(read_data='NAME="Fedora Linux"\nID=fedora\n'))
@patch("os.path.expanduser", return_value="/home/test")
@patch("platform.machine", return_value="x86_64")
@patch("sys.platform", "linux")
def test_constants_linux_fedora_spaced_directory(
    mock_expand: MagicMock,
    mock_machine: MagicMock,
) -> None:
    """Non-Ubuntu Linux distributions should use standard spaced directory names."""
    importlib.reload(constants)
    assert constants.DEFAULT_IDE_DIR == "/home/test/opt/Antigravity IDE"


@patch("platform.machine", return_value="unknown-arch")
@patch("sys.platform", "freebsd")
def test_constants_unknown_os_fallback(mock_machine: MagicMock) -> None:
    """Unsupported platforms should cleanly fall back to unknown OS and empty paths."""
    importlib.reload(constants)
    assert constants.OS_NAME == "unknown"
    assert constants.DEFAULT_IDE_DIR == ""
    assert constants.DEFAULT_HUB_DIR == ""


def test_truthy_values_tuple() -> None:
    """Truthy and falsy constants should include standard representations."""
    assert constants.TRUTHY_VALUES == ("1", "true", "yes", "on")
    assert constants.FALSY_VALUES == ("0", "false", "no", "off")


def test_version_constant() -> None:
    """Version constant should match 0.5.1."""
    assert constants.__version__ == "0.5.1"


def test_user_agent_header() -> None:
    """User agent constant should identify the updater honestly."""
    assert constants.USER_AGENT == f"missing-ag-updater/{constants.__version__}"
