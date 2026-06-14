import os
from pathlib import Path
from unittest.mock import ANY, patch

import pytest

from missing_ag_updater.cli import main
from missing_ag_updater.config import get_default_config_path, load_toml_config


def test_get_default_config_path_linux() -> None:
    with patch("missing_ag_updater.config.OS_NAME", "linux"):
        with patch.dict(os.environ, {"XDG_CONFIG_HOME": "/custom/xdg"}, clear=True):
            path = get_default_config_path()
            assert path == Path("/custom/xdg/missing-ag-updater/config.toml")

        with patch.dict(os.environ, {}, clear=True):
            with patch("missing_ag_updater.config.HOME", "/home/user"):
                path = get_default_config_path()
                assert path == Path("/home/user/.config/missing-ag-updater/config.toml")


def test_get_default_config_path_mac() -> None:
    with patch("missing_ag_updater.config.OS_NAME", "darwin"):
        with patch("missing_ag_updater.config.HOME", "/Users/user"):
            path = get_default_config_path()
            assert path == Path("/Users/user/Library/Application Support/missing-ag-updater/config.toml")


def test_get_default_config_path_windows() -> None:
    with patch("missing_ag_updater.config.OS_NAME", "windows"):
        with patch.dict(os.environ, {"APPDATA": "C:\\Users\\user\\AppData\\Roaming"}, clear=True):
            path = get_default_config_path()
            expected = Path("C:\\Users\\user\\AppData\\Roaming") / "missing-ag-updater" / "config.toml"
            assert path == expected

        with patch.dict(os.environ, {}, clear=True):
            with patch("missing_ag_updater.config.HOME", "C:\\Users\\user"):
                path = get_default_config_path()
                expected = Path("C:\\Users\\user") / "AppData" / "Roaming" / "missing-ag-updater" / "config.toml"
                assert path == expected


def test_get_default_config_path_other() -> None:
    with patch("missing_ag_updater.config.OS_NAME", "unknown"):
        with patch("missing_ag_updater.config.HOME", "/home/user"):
            path = get_default_config_path()
            assert path == Path("/home/user/.missing-ag-updater.toml")


def test_load_toml_config_missing(tmp_path) -> None:
    non_existent = str(tmp_path / "missing.toml")
    # Non-explicit should return empty dict
    assert load_toml_config(non_existent, explicit=False) == {}

    # Explicit should raise FileNotFoundError
    with pytest.raises(FileNotFoundError):
        load_toml_config(non_existent, explicit=True)


def test_load_toml_config_corrupt(tmp_path) -> None:
    corrupt_file = tmp_path / "corrupt.toml"
    with open(corrupt_file, "w") as f:
        f.write("this is not valid toml = {")

    # Non-explicit should return empty dict and print warning
    with patch("missing_ag_updater.utils.print_warning") as mock_warn:
        assert load_toml_config(str(corrupt_file), explicit=False) == {}
        mock_warn.assert_called_once()

    # Explicit should raise ValueError
    with pytest.raises(ValueError):
        load_toml_config(str(corrupt_file), explicit=True)


def test_load_toml_config_valid(tmp_path) -> None:
    valid_file = tmp_path / "valid.toml"
    with open(valid_file, "w") as f:
        f.write('force = true\ndir_ide = "/custom/ide"\n')

    data = load_toml_config(str(valid_file))
    assert data == {"force": True, "dir_ide": "/custom/ide"}


def test_cli_config_integration(tmp_path) -> None:
    config_file = tmp_path / "cli_config.toml"
    with open(config_file, "w") as f:
        # We can configure force = true, desktop = false, nautilus = false
        f.write("force = true\ndesktop = false\nnautilus = false\n")

    # Test that config file propagates to main updater logic
    with patch("sys.argv", ["antigravity-updater", "--ide", "--config", str(config_file)]):
        with patch("missing_ag_updater.cli.OS_NAME", "linux"):
            with patch("missing_ag_updater.cli.update_ide", return_value=True) as mock_ide:
                with patch("sys.exit", side_effect=SystemExit) as mock_exit:
                    with pytest.raises(SystemExit):
                        main()
                    mock_ide.assert_called_once_with(
                        ANY,  # ide_dir
                        ANY,  # DEFAULT_IDE_LAUNCHER
                        dry_run=False,
                        force=True,  # loaded from TOML
                        install_desktop=False,  # loaded from TOML
                        install_nautilus=False,  # loaded from TOML
                    )
                    mock_exit.assert_called_once_with(0)


def test_cli_config_nonexistent_fails() -> None:
    with patch("sys.argv", ["antigravity-updater", "--config", "/nonexistent/config.toml"]):
        with patch("missing_ag_updater.cli.OS_NAME", "linux"):
            with patch("missing_ag_updater.cli.print_error") as mock_print_err:
                with patch("sys.exit", side_effect=SystemExit) as mock_exit:
                    with pytest.raises(SystemExit):
                        main()
                    mock_print_err.assert_called_once_with("Configuration file not found: /nonexistent/config.toml")
                    mock_exit.assert_called_once_with(1)
