from unittest.mock import ANY, patch

import pytest

from missing_ag_updater.cli import main
from missing_ag_updater.const import DEFAULT_IDE_LAUNCHER


def test_main_unknown_os() -> None:
    # Test that running on unsupported OS fails immediately
    with patch("sys.argv", ["antigravity-updater"]):
        with patch("missing_ag_updater.cli.OS_NAME", "unknown"):
            with patch("sys.exit", side_effect=SystemExit) as mock_exit:
                with pytest.raises(SystemExit):
                    main()
                mock_exit.assert_called_once_with(1)


def test_main_success_all() -> None:
    # Test that running with no args updates all components successfully
    with patch("sys.argv", ["antigravity-updater"]):
        with patch("missing_ag_updater.cli.OS_NAME", "linux"):
            with patch("missing_ag_updater.cli.load_toml_config", return_value={}):
                with patch("missing_ag_updater.cli.update_ide", return_value=True) as mock_ide:
                    with patch("missing_ag_updater.cli.update_hub", return_value=True) as mock_hub:
                        with patch("missing_ag_updater.cli.update_cli", return_value=True) as mock_cli:
                            with patch("sys.exit", side_effect=SystemExit) as mock_exit:
                                with pytest.raises(SystemExit):
                                    main()
                                mock_ide.assert_called_once()
                                mock_hub.assert_called_once()
                                mock_cli.assert_called_once()
                                mock_exit.assert_called_once_with(0)


def test_main_only_ide_fails() -> None:
    # Test that running with --ide only calls update_ide and exits 1 if it fails
    with patch("sys.argv", ["antigravity-updater", "--ide"]):
        with patch("missing_ag_updater.cli.OS_NAME", "linux"):
            with patch("missing_ag_updater.cli.load_toml_config", return_value={}):
                with patch("missing_ag_updater.cli.update_ide", return_value=False) as mock_ide:
                    with patch("missing_ag_updater.cli.update_hub") as mock_hub:
                        with patch("missing_ag_updater.cli.update_cli") as mock_cli:
                            with patch("sys.exit", side_effect=SystemExit) as mock_exit:
                                with pytest.raises(SystemExit):
                                    main()
                                mock_ide.assert_called_once()
                                mock_hub.assert_not_called()
                                mock_cli.assert_not_called()
                                mock_exit.assert_called_once_with(1)


def test_main_force_and_check() -> None:
    # Test args passing down (force, check, paths)
    with patch(
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
    ):
        with patch("missing_ag_updater.cli.OS_NAME", "linux"):
            with patch("missing_ag_updater.cli.load_toml_config", return_value={}):
                with patch("missing_ag_updater.cli.update_ide", return_value=True) as mock_ide:
                    with patch("sys.exit", side_effect=SystemExit) as mock_exit:
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


def test_main_apparmor_sandbox_flag() -> None:
    # Test --apparmor-sandbox flag passes suid_sandbox=True to both update_ide and update_hub
    with patch("sys.argv", ["antigravity-updater", "--apparmor-sandbox"]):
        with patch("missing_ag_updater.cli.OS_NAME", "linux"):
            with patch("missing_ag_updater.cli.load_toml_config", return_value={}):
                with patch("missing_ag_updater.cli.update_ide", return_value=True) as mock_ide:
                    with patch("missing_ag_updater.cli.update_hub", return_value=True) as mock_hub:
                        with patch("missing_ag_updater.cli.update_cli", return_value=True):
                            with patch("sys.exit", side_effect=SystemExit) as mock_exit:
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


def test_main_system_flag() -> None:
    # Test --system flag passes scope='system'; disable auto-detect with --no-apparmor-sandbox
    with patch("sys.argv", ["antigravity-updater", "--ide", "--system", "--no-apparmor-sandbox"]):
        with patch("missing_ag_updater.cli.OS_NAME", "linux"):
            with patch("missing_ag_updater.cli.load_toml_config", return_value={}):
                with patch("missing_ag_updater.cli.update_ide", return_value=True) as mock_ide:
                    with patch("sys.exit", side_effect=SystemExit) as mock_exit:
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


def test_main_no_apparmor_sandbox_flag() -> None:
    """--no-apparmor-sandbox disables sandbox fix even if AppArmor is active."""
    with patch("sys.argv", ["antigravity-updater", "--ide", "--no-apparmor-sandbox"]):
        with patch("missing_ag_updater.cli.OS_NAME", "linux"):
            with patch("missing_ag_updater.cli.load_toml_config", return_value={}):
                with patch("missing_ag_updater.cli.is_apparmor_enabled", return_value=True):
                    with patch("missing_ag_updater.cli.update_ide", return_value=True) as mock_ide:
                        with patch("sys.exit", side_effect=SystemExit) as mock_exit:
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


def test_main_auto_detect_apparmor() -> None:
    """Without flags, suid_sandbox auto-detects from is_apparmor_enabled."""
    with patch("sys.argv", ["antigravity-updater", "--ide"]):
        with patch("missing_ag_updater.cli.OS_NAME", "linux"):
            with patch("missing_ag_updater.cli.load_toml_config", return_value={}):
                with patch("missing_ag_updater.cli.is_apparmor_enabled", return_value=True):
                    with patch("missing_ag_updater.cli.update_ide", return_value=True) as mock_ide:
                        with patch("sys.exit", side_effect=SystemExit) as mock_exit:
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


def test_main_auto_detect_no_apparmor() -> None:
    """Without flags and no AppArmor, suid_sandbox defaults to False."""
    with patch("sys.argv", ["antigravity-updater", "--ide"]):
        with patch("missing_ag_updater.cli.OS_NAME", "linux"):
            with patch("missing_ag_updater.cli.load_toml_config", return_value={}):
                with patch("missing_ag_updater.cli.is_apparmor_enabled", return_value=False):
                    with patch("missing_ag_updater.cli.update_ide", return_value=True) as mock_ide:
                        with patch("sys.exit", side_effect=SystemExit) as mock_exit:
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


def test_main_diagnose_flag() -> None:
    with patch("sys.argv", ["antigravity-updater", "--diagnose"]):
        with patch("missing_ag_updater.cli.OS_NAME", "linux"):
            with patch("missing_ag_updater.cli.run_diagnose") as mock_diag:
                with patch("sys.exit", side_effect=SystemExit) as mock_exit:
                    with pytest.raises(SystemExit):
                        main()
                    mock_diag.assert_called_once()
                    mock_exit.assert_called_once_with(0)


def test_main_clean_duplicates_flag() -> None:
    with patch("sys.argv", ["antigravity-updater", "--clean-duplicates", "--system"]):
        with patch("missing_ag_updater.cli.OS_NAME", "linux"):
            with patch(
                "missing_ag_updater.cli.clean_duplicate_desktop_entries",
                return_value=["/test/file.desktop"],
            ) as mock_clean:
                with patch("sys.exit", side_effect=SystemExit) as mock_exit:
                    with pytest.raises(SystemExit):
                        main()
                    mock_clean.assert_called_once_with(keep_scope="system", remove_user_dirs=False)
                    mock_exit.assert_called_once_with(0)


def test_main_uninstall_flag() -> None:
    with patch("sys.argv", ["antigravity-updater", "--uninstall", "--ide"]):
        with patch("missing_ag_updater.cli.OS_NAME", "linux"):
            with patch("missing_ag_updater.cli.load_toml_config", return_value={}):
                with patch("missing_ag_updater.cli.uninstall_ide", return_value=True) as mock_un_ide:
                    with patch("missing_ag_updater.cli.uninstall_hub") as mock_un_hub:
                        with patch("sys.exit", side_effect=SystemExit) as mock_exit:
                            with pytest.raises(SystemExit):
                                main()
                            mock_un_ide.assert_called_once()
                            mock_un_hub.assert_not_called()
                            mock_exit.assert_called_once_with(0)
