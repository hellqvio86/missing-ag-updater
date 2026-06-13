import pytest
from pydantic import ValidationError

from missing_ag_updater.models import CliManifest, Release


def test_release_validation() -> None:
    # Valid release payload
    valid_data = {"version": "2.0.4", "execution_id": "exec-123"}
    release = Release.model_validate(valid_data)
    assert release.version == "2.0.4"
    assert release.execution_id == "exec-123"

    # Missing field
    invalid_data = {"version": "2.0.4"}
    with pytest.raises(ValidationError):
        Release.model_validate(invalid_data)


def test_cli_manifest_validation() -> None:
    # Valid CLI manifest with optional sha512
    valid_data_with_sha = {
        "version": "1.0.8",
        "url": "https://example.com/agy.tar.gz",
        "sha512": "abc123hash",
    }
    manifest = CliManifest.model_validate(valid_data_with_sha)
    assert manifest.version == "1.0.8"
    assert manifest.url == "https://example.com/agy.tar.gz"
    assert manifest.sha512 == "abc123hash"

    # Valid CLI manifest without optional sha512
    valid_data_no_sha = {
        "version": "1.0.8",
        "url": "https://example.com/agy.tar.gz",
    }
    manifest_no_sha = CliManifest.model_validate(valid_data_no_sha)
    assert manifest_no_sha.version == "1.0.8"
    assert manifest_no_sha.url == "https://example.com/agy.tar.gz"
    assert manifest_no_sha.sha512 is None

    # Missing required field
    invalid_data = {"version": "1.0.8"}
    with pytest.raises(ValidationError):
        CliManifest.model_validate(invalid_data)
