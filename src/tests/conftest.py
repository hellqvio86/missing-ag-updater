from pathlib import Path

import pytest


@pytest.fixture(autouse=True)
def isolated_cli_self_updater_state(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """Point the official CLI self-updater state dir at an empty temp dir so host state never leaks into tests."""
    state_dir = tmp_path / "agy-updater-state"
    monkeypatch.setattr("missing_ag_updater.discovery.CLI_SELF_UPDATER_STATE_DIR", str(state_dir))
    return state_dir


@pytest.fixture(autouse=True)
def isolated_wsl_detection(monkeypatch: pytest.MonkeyPatch) -> None:
    """Make WSL detection report 'not WSL' by default so tests behave the same on WSL hosts."""
    monkeypatch.delenv("WSL_DISTRO_NAME", raising=False)
    monkeypatch.delenv("WSL_INTEROP", raising=False)
    monkeypatch.setattr("missing_ag_updater.utils.WSL_KERNEL_RELEASE_FILES", ())


@pytest.fixture(autouse=True)
def isolated_updater_version_check(monkeypatch: pytest.MonkeyPatch) -> None:
    """Prevent CLI tests from hitting PyPI during the startup version check."""
    monkeypatch.setattr("missing_ag_updater.cli.warn_if_updater_outdated", lambda: None)
