import json
import os
from typing import Any
from unittest.mock import MagicMock, patch

from missing_ag_updater.discovery import (
    _find_binaries_in_path,
    _find_exec_from_desktop,
    _is_system_path,
    clean_duplicate_desktop_entries,
    detect_preferred_cli,
    detect_preferred_hub,
    detect_preferred_ide,
    diagnose_all,
    find_all_cli_installations,
    find_all_hub_installations,
    find_all_ide_installations,
)


def test_is_system_path(monkeypatch: Any) -> None:
    with patch("missing_ag_updater.discovery.OS_NAME", "linux"):
        assert _is_system_path("/opt/antigravity-ide") is True
        assert _is_system_path("/usr/local/bin/antigravity") is True
        assert _is_system_path("/optfoo/bar") is False
        assert _is_system_path("/usrbar/bin") is False
        assert _is_system_path("/home/user/opt/Antigravity-IDE") is False
        assert _is_system_path("") is False

    with patch("missing_ag_updater.discovery.OS_NAME", "darwin"):
        assert _is_system_path("/Applications/Antigravity.app") is True
        assert _is_system_path("/ApplicationsFoo") is False
        assert _is_system_path("/Users/test/Applications/Antigravity.app") is False

    with patch("missing_ag_updater.discovery.OS_NAME", "windows"):
        monkeypatch.setenv("ProgramFiles", "C:\\Program Files")
        assert _is_system_path("C:\\Program Files\\Antigravity") is True
        assert _is_system_path("C:\\Program FilesFoo\\Antigravity") is False
        assert _is_system_path("C:\\Users\\Test\\AppData\\Local\\Programs") is False


def test_find_exec_from_desktop(tmp_path: Any) -> None:
    desktop_file = tmp_path / "test.desktop"
    with open(desktop_file, "w", encoding="utf-8") as fdesc:
        fdesc.write("[Desktop Entry]\nName=Test\nExec=/usr/local/bin/antigravity-ide %F\n")

    cmd = _find_exec_from_desktop(str(desktop_file))
    assert cmd == "/usr/local/bin/antigravity-ide"

    assert _find_exec_from_desktop("/nonexistent/file.desktop") is None


def test_find_binaries_in_path(tmp_path: Any, monkeypatch: Any) -> None:
    bin_dir1 = tmp_path / "bin1"
    bin_dir2 = tmp_path / "bin2"
    os.makedirs(bin_dir1)
    os.makedirs(bin_dir2)

    bin1 = bin_dir1 / "test_bin"
    with open(bin1, "w", encoding="utf-8") as fdesc:
        fdesc.write("#!/bin/sh\n")
    os.chmod(bin1, 0o755)

    monkeypatch.setenv("PATH", f"{bin_dir1}:{bin_dir2}")
    found = _find_binaries_in_path("test_bin")
    assert len(found) == 1
    assert found[0] == str(bin1)


def test_find_all_ide_installations(tmp_path: Any) -> None:
    ide_sys = tmp_path / "opt" / "antigravity-ide" / "Antigravity-IDE"
    os.makedirs(ide_sys / "resources" / "app")
    with open(ide_sys / "resources" / "app" / "product.json", "w", encoding="utf-8") as fdesc:
        json.dump({"ideVersion": "2.5.0"}, fdesc)

    @patch("missing_ag_updater.discovery._find_binaries_in_path", return_value=[])
    @patch("missing_ag_updater.discovery.SYSTEM_IDE_DIR", str(tmp_path / "opt" / "antigravity-ide"))
    @patch("missing_ag_updater.discovery.OS_NAME", "linux")
    def _run_test(mock_bins: MagicMock) -> None:
        installs = find_all_ide_installations()
        assert len(installs) >= 1
        matched = next((inst for inst in installs if inst.version == "2.5.0"), None)
        assert matched is not None
        assert matched.component == "ide"

    _run_test()


def test_find_all_hub_installations(tmp_path: Any) -> None:
    hub_sys = tmp_path / "opt" / "antigravity" / "Antigravity-x64"
    os.makedirs(hub_sys / "resources")
    with open(hub_sys / "resources" / "app.asar", "wb") as fdesc:
        fdesc.write(b"dummy")

    @patch("missing_ag_updater.discovery.get_hub_version", return_value="2.8.0")
    @patch("missing_ag_updater.discovery._find_binaries_in_path", return_value=[])
    @patch("missing_ag_updater.discovery.SYSTEM_HUB_DIR", str(tmp_path / "opt" / "antigravity"))
    @patch("missing_ag_updater.discovery.OS_NAME", "linux")
    def _run_test(mock_bins: MagicMock, mock_ver: MagicMock) -> None:
        installs = find_all_hub_installations()
        assert len(installs) >= 1
        matched = next((inst for inst in installs if inst.version == "2.8.0"), None)
        assert matched is not None
        assert matched.component == "hub"

    _run_test()


def test_find_all_cli_installations(tmp_path: Any) -> None:
    cli_bin = tmp_path / "bin" / "agy"
    os.makedirs(tmp_path / "bin")
    with open(cli_bin, "w", encoding="utf-8") as fdesc:
        fdesc.write("#!/bin/sh\n")
    os.chmod(cli_bin, 0o755)

    @patch("missing_ag_updater.discovery.get_cli_version", return_value="1.1.10")
    @patch("missing_ag_updater.discovery._find_binaries_in_path", return_value=[str(cli_bin)])
    @patch("missing_ag_updater.discovery.USER_CLI_BINARY", str(cli_bin))
    @patch("missing_ag_updater.discovery.OS_NAME", "linux")
    def _run_test(mock_bins: MagicMock, mock_ver: MagicMock) -> None:
        installs = find_all_cli_installations()
        assert len(installs) >= 1
        matched = next((inst for inst in installs if inst.version == "1.1.10"), None)
        assert matched is not None
        assert matched.component == "cli"

    _run_test()


@patch("missing_ag_updater.discovery.USER_IDE_DIR", "/home/user/opt/Antigravity-IDE")
@patch("missing_ag_updater.discovery.SYSTEM_IDE_DIR", "/opt/antigravity-ide")
@patch("missing_ag_updater.discovery.find_all_ide_installations", return_value=[])
@patch("missing_ag_updater.discovery.OS_NAME", "linux")
def test_detect_preferred_ide_scopes(mock_find: MagicMock) -> None:
    # Force system
    ide_dir, launcher, scope = detect_preferred_ide(scope="system")
    assert scope == "system"
    assert ide_dir == "/opt/antigravity-ide"

    # Force user
    ide_dir, launcher, scope = detect_preferred_ide(scope="user")
    assert scope == "user"
    assert ide_dir == "/home/user/opt/Antigravity-IDE"


@patch("missing_ag_updater.discovery.USER_HUB_DIR", "/home/user/opt/Antigravity-x64")
@patch("missing_ag_updater.discovery.SYSTEM_HUB_DIR", "/opt/antigravity")
@patch("missing_ag_updater.discovery.find_all_hub_installations", return_value=[])
@patch("missing_ag_updater.discovery.OS_NAME", "linux")
def test_detect_preferred_hub_scopes(mock_find: MagicMock) -> None:
    hub_dir, launcher, scope = detect_preferred_hub(scope="system")
    assert scope == "system"
    assert hub_dir == "/opt/antigravity"

    hub_dir, launcher, scope = detect_preferred_hub(scope="user")
    assert scope == "user"
    assert hub_dir == "/home/user/opt/Antigravity-x64"


@patch("missing_ag_updater.discovery.USER_CLI_BINARY", "/home/user/.local/bin/agy")
@patch("missing_ag_updater.discovery.SYSTEM_CLI_BINARY", "/usr/local/bin/agy")
@patch("missing_ag_updater.discovery.find_all_cli_installations", return_value=[])
@patch("missing_ag_updater.discovery.OS_NAME", "linux")
def test_detect_preferred_cli_scopes(mock_find: MagicMock) -> None:
    cli_path, scope = detect_preferred_cli(scope="system")
    assert scope == "system"
    assert cli_path == "/usr/local/bin/agy"

    cli_path, scope = detect_preferred_cli(scope="user")
    assert scope == "user"
    assert cli_path == "/home/user/.local/bin/agy"


@patch("missing_ag_updater.discovery.get_running_pids", return_value=[])
@patch("missing_ag_updater.discovery.find_all_cli_installations", return_value=[])
@patch("missing_ag_updater.discovery.find_all_hub_installations", return_value=[])
@patch("missing_ag_updater.discovery.find_all_ide_installations", return_value=[])
@patch("missing_ag_updater.discovery.OS_NAME", "linux")
def test_diagnose_all(
    mock_ides: MagicMock,
    mock_hubs: MagicMock,
    mock_clis: MagicMock,
    mock_pids: MagicMock,
) -> None:
    diag = diagnose_all()
    assert diag["os"] == "linux"
    assert "ide_installations" in diag
    assert "hub_installations" in diag
    assert "cli_installations" in diag
    assert "running_processes" in diag


def test_clean_duplicate_desktop_entries(tmp_path: Any) -> None:
    user_app_dir = tmp_path / "applications"
    user_bin_dir = tmp_path / "bin"
    user_icon_dir = tmp_path / "icons"
    user_opt_dir = tmp_path / "opt"

    os.makedirs(user_app_dir)
    os.makedirs(user_bin_dir)
    os.makedirs(user_icon_dir)
    os.makedirs(user_opt_dir / "Antigravity-IDE")

    dt_ide = user_app_dir / "antigravity-ide.desktop"
    dt_hub = user_app_dir / "antigravity.desktop"
    with open(dt_ide, "w", encoding="utf-8") as fdesc:
        fdesc.write("content")
    with open(dt_hub, "w", encoding="utf-8") as fdesc:
        fdesc.write("content")

    sym_ide = user_bin_dir / "antigravity-ide"
    with open(sym_ide, "w", encoding="utf-8") as fdesc:
        fdesc.write("bin")

    @patch("missing_ag_updater.discovery.refresh_linux_desktop_caches")
    @patch("missing_ag_updater.discovery.USER_OPT_DIR", str(user_opt_dir))
    @patch("missing_ag_updater.discovery.USER_ICONS_DIR", str(user_icon_dir))
    @patch("missing_ag_updater.discovery.USER_BIN_DIR", str(user_bin_dir))
    @patch("missing_ag_updater.discovery.USER_APPLICATIONS_DIR", str(user_app_dir))
    @patch("missing_ag_updater.discovery.OS_NAME", "linux")
    def _run_test(mock_refresh: MagicMock) -> None:
        removed = clean_duplicate_desktop_entries(keep_scope="system", remove_user_dirs=True)
        assert str(dt_ide) in removed
        assert str(dt_hub) in removed
        assert str(sym_ide) in removed
        assert str(user_opt_dir / "Antigravity-IDE") in removed
        assert not os.path.exists(dt_ide)
        assert not os.path.exists(sym_ide)

    _run_test()


def test_is_system_path_all_platforms(monkeypatch: Any) -> None:
    assert _is_system_path("") is False

    with patch("missing_ag_updater.discovery.OS_NAME", "linux"):
        assert _is_system_path("/opt/antigravity") is True
        assert _is_system_path("/usr/bin/agy") is True
        assert _is_system_path("/etc/antigravity") is True
        assert _is_system_path("/home/user/opt") is False

    with patch("missing_ag_updater.discovery.OS_NAME", "darwin"):
        assert _is_system_path("/Applications/Antigravity.app") is True
        assert _is_system_path("/Library/Application Support") is True
        assert _is_system_path("/Users/user/Applications") is False

    with patch("missing_ag_updater.discovery.OS_NAME", "windows"):
        monkeypatch.setenv("ProgramFiles", "C:\\Program Files")
        assert _is_system_path("C:\\Program Files\\Antigravity") is True
        assert _is_system_path("C:\\Users\\user\\AppData") is False


def test_find_exec_from_desktop_error(tmp_path: Any) -> None:
    assert _find_exec_from_desktop("/nonexistent/file.desktop") is None

    dummy = tmp_path / "test.desktop"
    with open(dummy, "w", encoding="utf-8") as fdesc:
        fdesc.write("Exec=test %U\n")
    with patch("builtins.open", side_effect=OSError("Read error")):
        assert _find_exec_from_desktop(str(dummy)) is None


@patch("missing_ag_updater.discovery._find_binaries_in_path", return_value=[])
@patch("missing_ag_updater.discovery.get_cli_version", return_value="1.0.0")
@patch("missing_ag_updater.discovery.get_hub_version", return_value="2.0.0")
@patch("missing_ag_updater.discovery.get_ide_version", return_value="2.0.0")
def test_find_all_darwin_and_windows(
    mock_ide_ver: MagicMock,
    mock_hub_ver: MagicMock,
    mock_cli_ver: MagicMock,
    mock_bins: MagicMock,
    tmp_path: Any,
) -> None:
    # Darwin IDE & Hub
    with patch("missing_ag_updater.discovery.OS_NAME", "darwin"):
        ides = find_all_ide_installations()
        hubs = find_all_hub_installations()
        clis = find_all_cli_installations()
        assert len(ides) >= 1
        assert len(hubs) >= 1
        assert len(clis) >= 1

    # Windows IDE & Hub
    with patch("missing_ag_updater.discovery.OS_NAME", "windows"):
        ides = find_all_ide_installations()
        hubs = find_all_hub_installations()
        clis = find_all_cli_installations()
        assert len(ides) >= 1
        assert len(hubs) >= 1
        assert len(clis) >= 1


@patch("missing_ag_updater.discovery.find_all_cli_installations", return_value=[])
@patch("missing_ag_updater.discovery.find_all_hub_installations", return_value=[])
@patch("missing_ag_updater.discovery.find_all_ide_installations", return_value=[])
@patch("missing_ag_updater.discovery.SYSTEM_CLI_BINARY", "/usr/bin/agy")
@patch("missing_ag_updater.discovery.SYSTEM_HUB_DIR", "/opt/hub")
@patch("missing_ag_updater.discovery.SYSTEM_IDE_DIR", "/opt/ide")
@patch("os.geteuid", return_value=0)
def test_detect_preferred_root_and_auto(
    mock_euid: MagicMock,
    mock_ides: MagicMock,
    mock_hubs: MagicMock,
    mock_clis: MagicMock,
) -> None:
    ide_dir, _, scope = detect_preferred_ide()
    assert scope == "system"
    assert ide_dir == "/opt/ide"

    hub_dir, _, hub_scope = detect_preferred_hub()
    assert hub_scope == "system"
    assert hub_dir == "/opt/hub"

    cli_path, cli_scope = detect_preferred_cli()
    assert cli_scope == "system"
    assert cli_path == "/usr/bin/agy"


@patch("missing_ag_updater.discovery.OS_NAME", "darwin")
def test_clean_duplicate_desktop_entries_non_linux() -> None:
    assert clean_duplicate_desktop_entries() == []
