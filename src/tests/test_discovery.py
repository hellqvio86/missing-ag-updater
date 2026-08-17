import json
import os
from unittest.mock import patch

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


def test_is_system_path() -> None:
    with patch("missing_ag_updater.discovery.OS_NAME", "linux"):
        assert _is_system_path("/opt/antigravity-ide") is True
        assert _is_system_path("/usr/local/bin/antigravity") is True
        assert _is_system_path("/home/user/opt/Antigravity-IDE") is False
        assert _is_system_path("") is False

    with patch("missing_ag_updater.discovery.OS_NAME", "darwin"):
        assert _is_system_path("/Applications/Antigravity.app") is True
        assert _is_system_path("/Users/test/Applications/Antigravity.app") is False

    with patch("missing_ag_updater.discovery.OS_NAME", "windows"):
        with patch.dict("os.environ", {"ProgramFiles": "C:\\Program Files"}):
            assert _is_system_path("C:\\Program Files\\Antigravity") is True
            assert _is_system_path("C:\\Users\\Test\\AppData\\Local\\Programs") is False


def test_find_exec_from_desktop(tmp_path) -> None:
    desktop_file = tmp_path / "test.desktop"
    with open(desktop_file, "w") as f:
        f.write("[Desktop Entry]\nName=Test\nExec=/usr/local/bin/antigravity-ide %F\n")

    cmd = _find_exec_from_desktop(str(desktop_file))
    assert cmd == "/usr/local/bin/antigravity-ide"

    assert _find_exec_from_desktop("/nonexistent/file.desktop") is None


def test_find_binaries_in_path(tmp_path) -> None:
    bin_dir1 = tmp_path / "bin1"
    bin_dir2 = tmp_path / "bin2"
    os.makedirs(bin_dir1)
    os.makedirs(bin_dir2)

    bin1 = bin_dir1 / "test_bin"
    with open(bin1, "w") as f:
        f.write("#!/bin/sh\n")
    os.chmod(bin1, 0o755)

    with patch.dict("os.environ", {"PATH": f"{bin_dir1}:{bin_dir2}"}):
        found = _find_binaries_in_path("test_bin")
        assert len(found) == 1
        assert found[0] == str(bin1)


def test_find_all_ide_installations(tmp_path) -> None:
    ide_sys = tmp_path / "opt" / "antigravity-ide" / "Antigravity-IDE"
    os.makedirs(ide_sys / "resources" / "app")
    with open(ide_sys / "resources" / "app" / "product.json", "w") as f:
        json.dump({"ideVersion": "2.5.0"}, f)

    with patch("missing_ag_updater.discovery.OS_NAME", "linux"):
        with patch("missing_ag_updater.discovery.SYSTEM_IDE_DIR", str(tmp_path / "opt" / "antigravity-ide")):
            with patch("missing_ag_updater.discovery._find_binaries_in_path", return_value=[]):
                installs = find_all_ide_installations()
                assert len(installs) >= 1
                matched = next((i for i in installs if i.version == "2.5.0"), None)
                assert matched is not None
                assert matched.component == "ide"


def test_find_all_hub_installations(tmp_path) -> None:
    hub_sys = tmp_path / "opt" / "antigravity" / "Antigravity-x64"
    os.makedirs(hub_sys / "resources")
    with open(hub_sys / "resources" / "app.asar", "wb") as f:
        f.write(b"dummy")

    with patch("missing_ag_updater.discovery.OS_NAME", "linux"):
        with patch("missing_ag_updater.discovery.SYSTEM_HUB_DIR", str(tmp_path / "opt" / "antigravity")):
            with patch("missing_ag_updater.discovery._find_binaries_in_path", return_value=[]):
                with patch("missing_ag_updater.discovery.get_hub_version", return_value="2.8.0"):
                    installs = find_all_hub_installations()
                    assert len(installs) >= 1
                    matched = next((i for i in installs if i.version == "2.8.0"), None)
                    assert matched is not None
                    assert matched.component == "hub"


def test_find_all_cli_installations(tmp_path) -> None:
    cli_bin = tmp_path / "bin" / "agy"
    os.makedirs(tmp_path / "bin")
    with open(cli_bin, "w") as f:
        f.write("#!/bin/sh\n")
    os.chmod(cli_bin, 0o755)

    with patch("missing_ag_updater.discovery.OS_NAME", "linux"):
        with patch("missing_ag_updater.discovery.USER_CLI_BINARY", str(cli_bin)):
            with patch("missing_ag_updater.discovery._find_binaries_in_path", return_value=[str(cli_bin)]):
                with patch("missing_ag_updater.discovery.get_cli_version", return_value="1.1.10"):
                    installs = find_all_cli_installations()
                    assert len(installs) >= 1
                    matched = next((i for i in installs if i.version == "1.1.10"), None)
                    assert matched is not None
                    assert matched.component == "cli"


def test_detect_preferred_ide_scopes() -> None:
    with patch("missing_ag_updater.discovery.OS_NAME", "linux"):
        with patch("missing_ag_updater.discovery.find_all_ide_installations", return_value=[]):
            with patch("missing_ag_updater.discovery.SYSTEM_IDE_DIR", "/opt/antigravity-ide"):
                with patch("missing_ag_updater.discovery.USER_IDE_DIR", "/home/user/opt/Antigravity-IDE"):
                    # Force system
                    d, launcher, s = detect_preferred_ide(scope="system")
                    assert s == "system"
                    assert d == "/opt/antigravity-ide"

                    # Force user
                    d, launcher, s = detect_preferred_ide(scope="user")
                    assert s == "user"
                    assert d == "/home/user/opt/Antigravity-IDE"


def test_detect_preferred_hub_scopes() -> None:
    with patch("missing_ag_updater.discovery.OS_NAME", "linux"):
        with patch("missing_ag_updater.discovery.find_all_hub_installations", return_value=[]):
            with patch("missing_ag_updater.discovery.SYSTEM_HUB_DIR", "/opt/antigravity"):
                with patch("missing_ag_updater.discovery.USER_HUB_DIR", "/home/user/opt/Antigravity-x64"):
                    d, launcher, s = detect_preferred_hub(scope="system")
                    assert s == "system"
                    assert d == "/opt/antigravity"

                    d, launcher, s = detect_preferred_hub(scope="user")
                    assert s == "user"
                    assert d == "/home/user/opt/Antigravity-x64"


def test_detect_preferred_cli_scopes() -> None:
    with patch("missing_ag_updater.discovery.OS_NAME", "linux"):
        with patch("missing_ag_updater.discovery.find_all_cli_installations", return_value=[]):
            with patch("missing_ag_updater.discovery.SYSTEM_CLI_BINARY", "/usr/local/bin/agy"):
                with patch("missing_ag_updater.discovery.USER_CLI_BINARY", "/home/user/.local/bin/agy"):
                    p, s = detect_preferred_cli(scope="system")
                    assert s == "system"
                    assert p == "/usr/local/bin/agy"

                    p, s = detect_preferred_cli(scope="user")
                    assert s == "user"
                    assert p == "/home/user/.local/bin/agy"


def test_diagnose_all() -> None:
    with patch("missing_ag_updater.discovery.OS_NAME", "linux"):
        with patch("missing_ag_updater.discovery.find_all_ide_installations", return_value=[]):
            with patch("missing_ag_updater.discovery.find_all_hub_installations", return_value=[]):
                with patch("missing_ag_updater.discovery.find_all_cli_installations", return_value=[]):
                    with patch("missing_ag_updater.discovery.get_running_pids", return_value=[]):
                        diag = diagnose_all()
                        assert diag["os"] == "linux"
                        assert "ide_installations" in diag
                        assert "hub_installations" in diag
                        assert "cli_installations" in diag
                        assert "running_processes" in diag


def test_clean_duplicate_desktop_entries(tmp_path) -> None:
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
    with open(dt_ide, "w") as f:
        f.write("content")
    with open(dt_hub, "w") as f:
        f.write("content")

    sym_ide = user_bin_dir / "antigravity-ide"
    with open(sym_ide, "w") as f:
        f.write("bin")

    with patch("missing_ag_updater.discovery.OS_NAME", "linux"):
        with patch("missing_ag_updater.discovery.USER_APPLICATIONS_DIR", str(user_app_dir)):
            with patch("missing_ag_updater.discovery.USER_BIN_DIR", str(user_bin_dir)):
                with patch("missing_ag_updater.discovery.USER_ICONS_DIR", str(user_icon_dir)):
                    with patch("missing_ag_updater.discovery.USER_OPT_DIR", str(user_opt_dir)):
                        with patch("missing_ag_updater.discovery.refresh_linux_desktop_caches"):
                            removed = clean_duplicate_desktop_entries(keep_scope="system", remove_user_dirs=True)
                            assert str(dt_ide) in removed
                            assert str(dt_hub) in removed
                            assert str(sym_ide) in removed
                            assert str(user_opt_dir / "Antigravity-IDE") in removed
                            assert not os.path.exists(dt_ide)
                            assert not os.path.exists(sym_ide)
