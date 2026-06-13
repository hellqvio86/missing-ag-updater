import os
from unittest.mock import ANY, patch

import pytest

from missing_ag_updater.cli import main
from missing_ag_updater.const import DEFAULT_IDE_LAUNCHER
from missing_ag_updater.desktop import install_hub_desktop, install_ide_desktop
from missing_ag_updater.nautilus import install_ide_nautilus


def test_install_ide_desktop(tmp_path) -> None:
    # Set up mock directories
    user_app_dir = str(tmp_path / "apps")
    user_icons_dir = str(tmp_path / "icons")
    ide_dir = str(tmp_path / "ide")
    launcher_path = str(tmp_path / "launcher")

    # Create dummy source icon file
    os.makedirs(os.path.join(ide_dir, "resources", "app", "resources", "linux"), exist_ok=True)
    icon_source = os.path.join(ide_dir, "resources", "app", "resources", "linux", "code.png")
    with open(icon_source, "w") as f:
        f.write("icon-data")

    with patch("missing_ag_updater.desktop.USER_APPLICATIONS_DIR", user_app_dir):
        with patch("missing_ag_updater.desktop.USER_ICONS_DIR", user_icons_dir):
            with patch("missing_ag_updater.desktop.refresh_linux_desktop_caches") as mock_refresh:
                install_ide_desktop(ide_dir=ide_dir, launcher_path=launcher_path)

                # Verify desktop entry was written
                desktop_file = os.path.join(user_app_dir, "antigravity-ide.desktop")
                assert os.path.exists(desktop_file)
                with open(desktop_file, "r") as f:
                    content = f.read()
                    assert "Exec=" + launcher_path in content
                    assert "Icon=antigravity-ide" in content

                # Verify icon was copied
                dest_icon = os.path.join(user_icons_dir, "antigravity-ide.png")
                assert os.path.exists(dest_icon)
                with open(dest_icon, "r") as f:
                    assert f.read() == "icon-data"

                mock_refresh.assert_called_once()


def test_install_hub_desktop(tmp_path) -> None:
    user_app_dir = str(tmp_path / "apps")
    user_icons_dir = str(tmp_path / "icons")
    hub_dir = str(tmp_path / "hub")
    launcher_path = str(tmp_path / "launcher")

    # Create dummy app.asar file to pass the existence check
    os.makedirs(os.path.join(hub_dir, "resources"), exist_ok=True)
    asar_path = os.path.join(hub_dir, "resources", "app.asar")
    with open(asar_path, "w") as f:
        f.write("asar-data")

    with patch("missing_ag_updater.desktop.USER_APPLICATIONS_DIR", user_app_dir):
        with patch("missing_ag_updater.desktop.USER_ICONS_DIR", user_icons_dir):
            with patch("missing_ag_updater.desktop.extract_asar_icon", return_value=True) as mock_extract:
                with patch("missing_ag_updater.desktop.refresh_linux_desktop_caches") as mock_refresh:
                    install_hub_desktop(hub_dir=hub_dir, launcher_path=launcher_path)

                    desktop_file = os.path.join(user_app_dir, "antigravity.desktop")
                    assert os.path.exists(desktop_file)
                    with open(desktop_file, "r") as f:
                        content = f.read()
                        assert "Exec=" + launcher_path in content
                        assert "Icon=antigravity" in content

                    mock_extract.assert_called_once_with(asar_path, os.path.join(user_icons_dir, "antigravity.png"))
                    mock_refresh.assert_called_once()


def test_install_ide_nautilus(tmp_path) -> None:
    user_nautilus_dir = str(tmp_path / "nautilus")
    ide_dir = str(tmp_path / "ide")
    launcher_path = str(tmp_path / "launcher")

    with patch("missing_ag_updater.nautilus.USER_NAUTILUS_DIR", user_nautilus_dir):
        with patch("missing_ag_updater.nautilus.refresh_linux_desktop_caches") as mock_refresh:
            install_ide_nautilus(ide_dir=ide_dir, launcher_path=launcher_path)

            nautilus_file = os.path.join(user_nautilus_dir, "open-in-antigravity-ide.py")
            assert os.path.exists(nautilus_file)
            with open(nautilus_file, "r") as f:
                content = f.read()
                assert "class OpenInAntigravityIDE" in content
                assert launcher_path in content

            mock_refresh.assert_called_once()


def test_cli_no_desktop_no_nautilus() -> None:
    # Test that --no-desktop and --no-nautilus propagate correctly to update_ide
    with patch(
        "sys.argv",
        [
            "antigravity-updater",
            "--ide",
            "--no-desktop",
            "--no-nautilus",
        ],
    ):
        with patch("missing_ag_updater.cli.OS_NAME", "linux"):
            with patch("missing_ag_updater.cli.update_ide", return_value=True) as mock_ide:
                with patch("sys.exit", side_effect=SystemExit) as mock_exit:
                    with pytest.raises(SystemExit):
                        main()
                    mock_ide.assert_called_once_with(
                        ANY,  # ide_dir
                        DEFAULT_IDE_LAUNCHER,
                        dry_run=False,
                        force=False,
                        install_desktop=False,
                        install_nautilus=False,
                    )
                    mock_exit.assert_called_once_with(0)


def test_cli_no_desktop_hub() -> None:
    # Test that --no-desktop propagates correctly to update_hub
    with patch(
        "sys.argv",
        [
            "antigravity-updater",
            "--hub",
            "--no-desktop",
        ],
    ):
        with patch("missing_ag_updater.cli.OS_NAME", "linux"):
            with patch("missing_ag_updater.cli.update_hub", return_value=True) as mock_hub:
                with patch("sys.exit", side_effect=SystemExit) as mock_exit:
                    with pytest.raises(SystemExit):
                        main()
                    mock_hub.assert_called_once_with(
                        ANY,  # hub_dir
                        ANY,  # DEFAULT_HUB_LAUNCHER
                        dry_run=False,
                        force=False,
                        install_desktop=False,
                    )
                    mock_exit.assert_called_once_with(0)


def test_cli_env_variables() -> None:
    # Test env variables for check, force, and paths
    with patch("sys.argv", ["antigravity-updater", "--ide"]):
        with patch.dict(
            "os.environ",
            {
                "ANTIGRAVITY_CHECK": "true",
                "ANTIGRAVITY_FORCE": "yes",
                "ANTIGRAVITY_DIR_IDE": "/env/ide/path",
                "ANTIGRAVITY_NO_DESKTOP": "1",
                "ANTIGRAVITY_NO_NAUTILUS": "true",
            },
        ):
            with patch("missing_ag_updater.cli.OS_NAME", "linux"):
                with patch("missing_ag_updater.cli.update_ide", return_value=True) as mock_ide:
                    with patch("sys.exit", side_effect=SystemExit) as mock_exit:
                        with pytest.raises(SystemExit):
                            main()
                        mock_ide.assert_called_once_with(
                            "/env/ide/path",
                            DEFAULT_IDE_LAUNCHER,
                            dry_run=True,
                            force=True,
                            install_desktop=False,
                            install_nautilus=False,
                        )
                        mock_exit.assert_called_once_with(0)


def test_cli_env_variables_alt_prefix() -> None:
    # Test AG_ prefix env variables
    with patch("sys.argv", ["antigravity-updater", "--hub"]):
        with patch.dict(
            "os.environ",
            {
                "AG_CHECK": "1",
                "AG_FORCE": "true",
                "AG_DIR_HUB": "/env/hub/path",
                "AG_DESKTOP": "false",
            },
        ):
            with patch("missing_ag_updater.cli.OS_NAME", "linux"):
                with patch("missing_ag_updater.cli.update_hub", return_value=True) as mock_hub:
                    with patch("sys.exit", side_effect=SystemExit) as mock_exit:
                        with pytest.raises(SystemExit):
                            main()
                        mock_hub.assert_called_once_with(
                            "/env/hub/path",
                            ANY,
                            dry_run=True,
                            force=True,
                            install_desktop=False,
                        )
                        mock_exit.assert_called_once_with(0)


def test_cli_override_env_variables() -> None:
    # Test CLI overrides env variables
    with patch("sys.argv", ["antigravity-updater", "--ide", "--no-desktop"]):
        with patch.dict(
            "os.environ",
            {
                "ANTIGRAVITY_DESKTOP": "true",
                "ANTIGRAVITY_NAUTILUS": "false",
            },
        ):
            with patch("missing_ag_updater.cli.OS_NAME", "linux"):
                with patch("missing_ag_updater.cli.update_ide", return_value=True) as mock_ide:
                    with patch("sys.exit", side_effect=SystemExit) as mock_exit:
                        with pytest.raises(SystemExit):
                            main()
                        mock_ide.assert_called_once_with(
                            ANY,
                            DEFAULT_IDE_LAUNCHER,
                            dry_run=False,
                            force=False,
                            install_desktop=False,
                            install_nautilus=False,
                        )
                        mock_exit.assert_called_once_with(0)
