from unittest.mock import patch

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
        ],
    ):
        with patch("missing_ag_updater.cli.OS_NAME", "linux"):
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
                    )
                    mock_exit.assert_called_once_with(0)
