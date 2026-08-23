"""Data models for releases and CLI manifest metadata."""

import re
from typing import Optional
from urllib.parse import urlparse

from pydantic import BaseModel, field_validator

ALLOWED_HOSTS: frozenset[str] = frozenset(
    {
        "dl.google.com",
        "edgedl.me.gvt1.com",
        "storage.googleapis.com",
    }
)

ALLOWED_HOST_SUFFIXES: tuple[str, ...] = (
    ".google.com",
    ".googleapis.com",
    ".gvt1.com",
    ".googleusercontent.com",
)

HEX_64_PATTERN = re.compile(r"^[0-9a-fA-F]{64}$")
HEX_128_PATTERN = re.compile(r"^[0-9a-fA-F]{128}$")


def is_trusted_download_url(url: str) -> bool:
    """Verify that a URL uses HTTPS and points to an authorized Google download domain."""
    try:
        parsed = urlparse(url)
        if parsed.scheme != "https":
            return False
        hostname = (parsed.hostname or "").lower()
        if not hostname:
            return False
        if hostname in ALLOWED_HOSTS:
            return True
        if any(hostname.endswith(suffix) for suffix in ALLOWED_HOST_SUFFIXES):
            return True
        return False
    except Exception:
        return False


class Release(BaseModel):
    """Release metadata for Antigravity IDE and Hub."""

    version: str
    execution_id: str
    sha512: Optional[str] = None
    sha256: Optional[str] = None

    @field_validator("sha512")
    @classmethod
    def validate_sha512(cls, value: Optional[str]) -> Optional[str]:
        if value is not None:
            cleaned = value.strip()
            if not HEX_128_PATTERN.match(cleaned):
                raise ValueError("sha512 checksum must be a 128-character hexadecimal string")
            return cleaned.lower()
        return None

    @field_validator("sha256")
    @classmethod
    def validate_sha256(cls, value: Optional[str]) -> Optional[str]:
        if value is not None:
            cleaned = value.strip()
            if not HEX_64_PATTERN.match(cleaned):
                raise ValueError("sha256 checksum must be a 64-character hexadecimal string")
            return cleaned.lower()
        return None


class CliManifest(BaseModel):
    """Manifest metadata for Antigravity CLI binary distributions."""

    version: str
    url: str
    sha512: Optional[str] = None

    @field_validator("url")
    @classmethod
    def validate_url(cls, value: str) -> str:
        cleaned = value.strip()
        if not is_trusted_download_url(cleaned):
            raise ValueError(f"Download URL '{cleaned}' is not an authorized HTTPS Google download source.")
        return cleaned

    @field_validator("sha512")
    @classmethod
    def validate_sha512(cls, value: Optional[str]) -> Optional[str]:
        if value is not None:
            cleaned = value.strip()
            if not HEX_128_PATTERN.match(cleaned):
                raise ValueError("sha512 checksum must be a 128-character hexadecimal string")
            return cleaned.lower()
        return None
