from typing import Any
from unittest.mock import ANY, MagicMock, patch

import pytest

from missing_ag_updater.cli import main, run_diagnose
from missing_ag_updater.const import DEFAULT_IDE_LAUNCHER


@patch("sys.exit", side_effect=SystemExit)
@patch("missing_ag_updater.cli.OS_NAME", "unknown")
@patch("sys.argv", ["antigravity-updater"])
def test_main_unknown_os(mock_exit: MagicMock) -> None:
    with pytest.raises(SystemExit):
        main()
    mock_exit.assert_called_once_with(1)


@patch("sys.exit", side_effect=SystemExit)
@patch("missing_ag_updater.cli.update_cli", return_value=True)
@patch("missing_ag_updater.cli.update_hub", return_value=True)
@patch("missing_ag_updater.cli.update_ide", return_value=True)
@patch("missing_ag_updater.config.load_toml_config", return_value={})
@patch("missing_ag_updater.cli.OS_NAME", "linux")
@patch("sys.argv", ["antigravity-updater"])
def test_main_success_all(
    mock_toml: MagicMock,
    mock_ide: MagicMock,
    mock_hub: MagicMock,
    mock_cli: MagicMock,
    mock_exit: MagicMock,
) -> None:
    with pytest.raises(SystemExit):
        main()
    mock_ide.assert_called_once()
    mock_hub.assert_called_once()
    mock_cli.assert_called_once()
    mock_exit.assert_called_once_with(0)


@patch("sys.exit", side_effect=SystemExit)
@patch("missing_ag_updater.cli.update_cli")
@patch("missing_ag_updater.cli.update_hub")
@patch("missing_ag_updater.cli.update_ide", return_value=False)
@patch("missing_ag_updater.config.load_toml_config", return_value={})
@patch("missing_ag_updater.cli.OS_NAME", "linux")
@patch("sys.argv", ["antigravity-updater", "--ide"])
def test_main_only_ide_fails(
    mock_toml: MagicMock,
    mock_ide: MagicMock,
    mock_hub: MagicMock,
    mock_cli: MagicMock,
    mock_exit: MagicMock,
) -> None:
    with pytest.raises(SystemExit):
        main()
    mock_ide.assert_called_once()
    mock_hub.assert_not_called()
    mock_cli.assert_not_called()
    mock_exit.assert_called_once_with(1)


@patch("sys.exit", side_effect=SystemExit)
@patch("missing_ag_updater.cli.update_ide", return_value=True)
@patch("missing_ag_updater.config.load_toml_config", return_value={})
@patch("missing_ag_updater.cli.OS_NAME", "linux")
@patch(
    "sys.argv",
    [
        "antigravity-updater",
        "--ide",
        "--force",
        "--check",
        "--dir-ide",
        "/custom/ide/path",
        "--no-apparmor-sandbox",
    ],
)
def test_main_force_and_check(
    mock_toml: MagicMock,
    mock_ide: MagicMock,
    mock_exit: MagicMock,
) -> None:
    with pytest.raises(SystemExit):
        main()
    mock_ide.assert_called_once_with(
        "/custom/ide/path",
        DEFAULT_IDE_LAUNCHER,
        dry_run=True,
        force=True,
        install_desktop=True,
        install_nautilus=True,
        suid_sandbox=False,
        scope=None,
    )
    mock_exit.assert_called_once_with(0)


@patch("sys.exit", side_effect=SystemExit)
@patch("missing_ag_updater.cli.update_cli", return_value=True)
@patch("missing_ag_updater.cli.update_hub", return_value=True)
@patch("missing_ag_updater.cli.update_ide", return_value=True)
@patch("missing_ag_updater.config.load_toml_config", return_value={})
@patch("missing_ag_updater.cli.OS_NAME", "linux")
@patch("sys.argv", ["antigravity-updater", "--apparmor-sandbox"])
def test_main_apparmor_sandbox_flag(
    mock_toml: MagicMock,
    mock_ide: MagicMock,
    mock_hub: MagicMock,
    mock_cli: MagicMock,
    mock_exit: MagicMock,
) -> None:
    with pytest.raises(SystemExit):
        main()
    mock_ide.assert_called_once_with(
        ANY,
        ANY,
        dry_run=False,
        force=False,
        install_desktop=True,
        install_nautilus=True,
        suid_sandbox=True,
        scope=None,
    )
    mock_hub.assert_called_once_with(
        ANY,
        ANY,
        dry_run=False,
        force=False,
        install_desktop=True,
        suid_sandbox=True,
        scope=None,
    )
    mock_exit.assert_called_once_with(0)


@patch("sys.exit", side_effect=SystemExit)
@patch("missing_ag_updater.cli.update_ide", return_value=True)
@patch("missing_ag_updater.config.load_toml_config", return_value={})
@patch("missing_ag_updater.cli.OS_NAME", "linux")
@patch("sys.argv", ["antigravity-updater", "--ide", "--system", "--no-apparmor-sandbox"])
def test_main_system_flag(
    mock_toml: MagicMock,
    mock_ide: MagicMock,
    mock_exit: MagicMock,
) -> None:
    with pytest.raises(SystemExit):
        main()
    mock_ide.assert_called_once_with(
        ANY,
        ANY,
        dry_run=False,
        force=False,
        install_desktop=True,
        install_nautilus=True,
        suid_sandbox=False,
        scope="system",
    )
    mock_exit.assert_called_once_with(0)


@patch("sys.exit", side_effect=SystemExit)
@patch("missing_ag_updater.cli.update_ide", return_value=True)
@patch("missing_ag_updater.config.is_apparmor_enabled", return_value=True)
@patch("missing_ag_updater.config.load_toml_config", return_value={})
@patch("missing_ag_updater.cli.OS_NAME", "linux")
@patch("sys.argv", ["antigravity-updater", "--ide", "--no-apparmor-sandbox"])
def test_main_no_apparmor_sandbox_flag(
    mock_toml: MagicMock,
    mock_apparmor: MagicMock,
    mock_ide: MagicMock,
    mock_exit: MagicMock,
) -> None:
    with pytest.raises(SystemExit):
        main()
    mock_ide.assert_called_once_with(
        ANY,
        ANY,
        dry_run=False,
        force=False,
        install_desktop=True,
        install_nautilus=True,
        suid_sandbox=False,
        scope=None,
    )
    mock_exit.assert_called_once_with(0)


@patch("sys.exit", side_effect=SystemExit)
@patch("missing_ag_updater.cli.update_ide", return_value=True)
@patch("missing_ag_updater.config.is_apparmor_enabled", return_value=True)
@patch("missing_ag_updater.config.load_toml_config", return_value={})
@patch("missing_ag_updater.cli.OS_NAME", "linux")
@patch("sys.argv", ["antigravity-updater", "--ide"])
def test_main_auto_detect_apparmor(
    mock_toml: MagicMock,
    mock_apparmor: MagicMock,
    mock_ide: MagicMock,
    mock_exit: MagicMock,
) -> None:
    with pytest.raises(SystemExit):
        main()
    mock_ide.assert_called_once_with(
        ANY,
        ANY,
        dry_run=False,
        force=False,
        install_desktop=True,
        install_nautilus=True,
        suid_sandbox=True,
        scope=None,
    )
    mock_exit.assert_called_once_with(0)


@patch("sys.exit", side_effect=SystemExit)
@patch("missing_ag_updater.cli.update_ide", return_value=True)
@patch("missing_ag_updater.config.is_apparmor_enabled", return_value=False)
@patch("missing_ag_updater.config.load_toml_config", return_value={})
@patch("missing_ag_updater.cli.OS_NAME", "linux")
@patch("sys.argv", ["antigravity-updater", "--ide"])
def test_main_auto_detect_no_apparmor(
    mock_toml: MagicMock,
    mock_apparmor: MagicMock,
    mock_ide: MagicMock,
    mock_exit: MagicMock,
) -> None:
    with pytest.raises(SystemExit):
        main()
    mock_ide.assert_called_once_with(
        ANY,
        ANY,
        dry_run=False,
        force=False,
        install_desktop=True,
        install_nautilus=True,
        suid_sandbox=False,
        scope=None,
    )
    mock_exit.assert_called_once_with(0)


@patch("sys.exit", side_effect=SystemExit)
@patch("missing_ag_updater.cli.run_diagnose")
@patch("missing_ag_updater.cli.OS_NAME", "linux")
@patch("sys.argv", ["antigravity-updater", "--diagnose"])
def test_main_diagnose_flag(mock_diag: MagicMock, mock_exit: MagicMock) -> None:
    with pytest.raises(SystemExit):
        main()
    mock_diag.assert_called_once()
    mock_exit.assert_called_once_with(0)


@patch("sys.exit", side_effect=SystemExit)
@patch(
    "missing_ag_updater.cli.clean_duplicate_desktop_entries",
    return_value=["/test/file.desktop"],
)
@patch("missing_ag_updater.cli.OS_NAME", "linux")
@patch("sys.argv", ["antigravity-updater", "--clean-duplicates", "--system"])
def test_main_clean_duplicates_flag(mock_clean: MagicMock, mock_exit: MagicMock) -> None:
    with pytest.raises(SystemExit):
        main()
    mock_clean.assert_called_once_with(keep_scope="system", remove_user_dirs=False)
    mock_exit.assert_called_once_with(0)


@patch("sys.exit", side_effect=SystemExit)
@patch("missing_ag_updater.cli.clean_duplicate_desktop_entries", return_value=[])
@patch("missing_ag_updater.cli.OS_NAME", "linux")
@patch("sys.argv", ["antigravity-updater", "--clean-duplicates"])
def test_main_clean_duplicates_no_files_removed(mock_clean: MagicMock, mock_exit: MagicMock) -> None:
    with pytest.raises(SystemExit):
        main()
    mock_clean.assert_called_once_with(keep_scope="system", remove_user_dirs=False)
    mock_exit.assert_called_once_with(0)


@patch("sys.exit", side_effect=SystemExit)
@patch(
    "missing_ag_updater.cli.clean_duplicate_desktop_entries",
    return_value=["/opt/test", "~/.local/share/applications/antigravity.desktop"],
)
@patch("missing_ag_updater.cli.OS_NAME", "linux")
@patch("sys.argv", ["antigravity-updater", "--clean-duplicates", "--user", "--remove-user-dirs"])
def test_main_clean_duplicates_with_remove_user_dirs(mock_clean: MagicMock, mock_exit: MagicMock) -> None:
    with pytest.raises(SystemExit):
        main()
    mock_clean.assert_called_once_with(keep_scope="user", remove_user_dirs=True)
    mock_exit.assert_called_once_with(0)


@patch("sys.exit", side_effect=SystemExit)
@patch("missing_ag_updater.cli.uninstall_hub")
@patch("missing_ag_updater.cli.uninstall_ide", return_value=True)
@patch("missing_ag_updater.config.load_toml_config", return_value={})
@patch("missing_ag_updater.cli.OS_NAME", "linux")
@patch("sys.argv", ["antigravity-updater", "--uninstall", "--ide"])
def test_main_uninstall_flag(
    mock_toml: MagicMock,
    mock_un_ide: MagicMock,
    mock_un_hub: MagicMock,
    mock_exit: MagicMock,
) -> None:
    with pytest.raises(SystemExit):
        main()
    mock_un_ide.assert_called_once()
    mock_un_hub.assert_not_called()
    mock_exit.assert_called_once_with(0)


@patch("sys.exit", side_effect=SystemExit)
@patch("missing_ag_updater.cli.uninstall_cli", return_value=False)
@patch("missing_ag_updater.cli.uninstall_hub", return_value=True)
@patch("missing_ag_updater.cli.uninstall_ide", return_value=True)
@patch("missing_ag_updater.config.load_toml_config", return_value={})
@patch("missing_ag_updater.cli.OS_NAME", "linux")
@patch("sys.argv", ["antigravity-updater", "--uninstall"])
def test_main_uninstall_all_components_and_failure(
    mock_toml: MagicMock,
    mock_un_ide: MagicMock,
    mock_un_hub: MagicMock,
    mock_un_cli: MagicMock,
    mock_exit: MagicMock,
) -> None:
    with pytest.raises(SystemExit):
        main()
    mock_un_ide.assert_called_once()
    mock_un_hub.assert_called_once()
    mock_un_cli.assert_called_once()
    mock_exit.assert_called_once_with(1)


@patch("sys.exit", side_effect=SystemExit)
@patch("missing_ag_updater.cli.resolve_config", side_effect=RuntimeError("Config error"))
@patch("missing_ag_updater.cli.OS_NAME", "linux")
@patch("sys.argv", ["antigravity-updater"])
def test_main_resolve_config_error(mock_resolve: MagicMock, mock_exit: MagicMock) -> None:
    with pytest.raises(SystemExit):
        main()
    mock_exit.assert_called_once_with(1)


@patch("missing_ag_updater.cli.diagnose_all")
def test_run_diagnose_full(mock_diag_all: MagicMock, capsys: Any) -> None:
    fake_data = {
        "os": "linux",
        "ide_installations": [
            {
                "version": "2.0.4",
                "scope": "system",
                "is_writable": False,
                "install_dir": "/opt/antigravity-ide",
                "launcher_path": "/usr/local/bin/antigravity-ide",
                "desktop_entry": "/usr/share/applications/antigravity-ide.desktop",
            }
        ],
        "hub_installations": [
            {
                "version": "2.1.4",
                "scope": "user",
                "is_writable": True,
                "install_dir": "/home/user/opt/Antigravity-x64",
                "launcher_path": "/home/user/.local/bin/antigravity",
                "desktop_entry": "/home/user/.local/share/applications/antigravity.desktop",
            }
        ],
        "cli_installations": [
            {
                "version": "1.0.8",
                "scope": "user",
                "is_writable": True,
                "launcher_path": "/home/user/.local/bin/agy",
            }
        ],
        "desktop_files": [
            {
                "scope": "system",
                "component": "IDE",
                "path": "/usr/share/applications/antigravity-ide.desktop",
                "exec": "/usr/local/bin/antigravity-ide",
            }
        ],
        "running_processes": {
            "ide_pids": ["12345"],
            "hub_pids": ["67890"],
        },
        "sandbox_status": {
            "distro_ubuntu_style": True,
            "apparmor_active": True,
        },
    }
    mock_diag_all.return_value = fake_data
    run_diagnose()
    captured = capsys.readouterr().out
    assert "Antigravity System Diagnostics" in captured
    assert "2.0.4" in captured
    assert "2.1.4" in captured
    assert "1.0.8" in captured
    assert "IDE PIDs: 12345" in captured
    assert "Hub PIDs: 67890" in captured


@patch("missing_ag_updater.cli.diagnose_all")
def test_run_diagnose_empty(mock_diag_all: MagicMock, capsys: Any) -> None:
    empty_data = {
        "os": "darwin",
        "ide_installations": [],
        "hub_installations": [],
        "cli_installations": [],
        "desktop_files": [],
        "running_processes": {},
        "sandbox_status": {},
    }
    mock_diag_all.return_value = empty_data
    run_diagnose()
    captured = capsys.readouterr().out
    assert "No IDE installations detected." in captured
    assert "No Hub installations detected." in captured
    assert "No CLI installations detected." in captured


@patch("sys.argv", ["antigravity-updater", "--version"])
def test_cli_version_flag(capsys: Any) -> None:
    with pytest.raises(SystemExit) as excinfo:
        main()
    assert excinfo.value.code == 0
    captured = capsys.readouterr().out
    assert "0.3.1" in captured
