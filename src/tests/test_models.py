"""Unit tests for Release and CliManifest data models and validation."""

import pytest
from pydantic import ValidationError

from missing_ag_updater.models import CliManifest, Release

SAMPLE_SHA512 = "a" * 128
SAMPLE_SHA256 = "b" * 64


def test_release_validation_success() -> None:
    # Valid release payload without hashes
    valid_data = {"version": "2.0.4", "execution_id": "exec-123"}
    release = Release.model_validate(valid_data)
    assert release.version == "2.0.4"
    assert release.execution_id == "exec-123"
    assert release.sha512 is None
    assert release.sha256 is None

    # Valid release payload with sha512 and sha256
    valid_with_hashes = {
        "version": "2.0.4",
        "execution_id": "exec-123",
        "sha512": SAMPLE_SHA512.upper(),
        "sha256": SAMPLE_SHA256.upper(),
    }
    release_with_hashes = Release.model_validate(valid_with_hashes)
    assert release_with_hashes.sha512 == SAMPLE_SHA512.lower()
    assert release_with_hashes.sha256 == SAMPLE_SHA256.lower()


def test_release_validation_failure() -> None:
    # Missing required field execution_id
    with pytest.raises(ValidationError):
        Release.model_validate({"version": "2.0.4"})

    # Invalid sha512 length/format
    with pytest.raises(ValidationError):
        Release.model_validate({"version": "2.0.4", "execution_id": "123", "sha512": "invalid_hash"})

    # Invalid sha256 length/format
    with pytest.raises(ValidationError):
        Release.model_validate({"version": "2.0.4", "execution_id": "123", "sha256": "not_64_chars"})


def test_cli_manifest_validation_success() -> None:
    # Valid CLI manifest from trusted Google domains
    trusted_urls = [
        "https://dl.google.com/release2/antigravity/agy.tar.gz",
        "https://edgedl.me.gvt1.com/edgedl/release2/agy.tar.gz",
        "https://storage.googleapis.com/antigravity-public/agy.tar.gz",
    ]
    for url in trusted_urls:
        manifest = CliManifest.model_validate(
            {
                "version": "1.0.8",
                "url": url,
                "sha512": SAMPLE_SHA512,
            }
        )
        assert manifest.version == "1.0.8"
        assert manifest.url == url
        assert manifest.sha512 == SAMPLE_SHA512


def test_cli_manifest_validation_untrusted_domain_rejected() -> None:
    # Untrusted domain must be rejected
    untrusted_urls = [
        "https://example.com/agy.tar.gz",
        "https://malicious-site.org/payload.exe",
        "http://dl.google.com/insecure.tar.gz",  # non-HTTPS
    ]
    for url in untrusted_urls:
        with pytest.raises(ValidationError):
            CliManifest.model_validate(
                {
                    "version": "1.0.8",
                    "url": url,
                    "sha512": SAMPLE_SHA512,
                }
            )


def test_cli_manifest_validation_invalid_sha512_rejected() -> None:
    # Invalid sha512 checksum format must be rejected
    with pytest.raises(ValidationError):
        CliManifest.model_validate(
            {
                "version": "1.0.8",
                "url": "https://dl.google.com/agy.tar.gz",
                "sha512": "not_a_valid_128_hex_string",
            }
        )
