from pathlib import Path

import pytest


@pytest.fixture(autouse=True)
def isolated_cli_self_updater_state(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """Point the official CLI self-updater state dir at an empty temp dir so host state never leaks into tests."""
    state_dir = tmp_path / "agy-updater-state"
    monkeypatch.setattr("missing_ag_updater.discovery.CLI_SELF_UPDATER_STATE_DIR", str(state_dir))
    return state_dir
