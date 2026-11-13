#!/usr/bin/env python3
"""Bump the single-source package version in const.py.

Usage:
    python bin/bump_version.py patch
    python bin/bump_version.py minor
    python bin/bump_version.py major
    python bin/bump_version.py 0.7.0
"""

import argparse
import re
import sys
from pathlib import Path

VERSION_PATTERN = re.compile(r'^(?P<prefix>__version__ = ")(?P<version>\d+\.\d+\.\d+)(?P<suffix>")$', re.MULTILINE)
CONST_PATH = Path(__file__).resolve().parents[1] / "src" / "missing_ag_updater" / "const.py"


def read_version() -> str:
    content = CONST_PATH.read_text(encoding="utf-8")
    match = VERSION_PATTERN.search(content)
    if match is None:
        raise RuntimeError(f"Could not find __version__ in {CONST_PATH}")
    return match.group("version")


def next_version(current: str, bump: str) -> str:
    if re.fullmatch(r"\d+\.\d+\.\d+", bump):
        return bump
    major, minor, patch = (int(part) for part in current.split("."))
    if bump == "major":
        return f"{major + 1}.0.0"
    if bump == "minor":
        return f"{major}.{minor + 1}.0"
    if bump == "patch":
        return f"{major}.{minor}.{patch + 1}"
    raise ValueError(f"Unsupported bump '{bump}'. Use major, minor, patch, or an explicit X.Y.Z version.")


def main() -> int:
    parser = argparse.ArgumentParser(description="Bump the package version in const.py")
    parser.add_argument("bump", help="major, minor, patch, or an explicit X.Y.Z version")
    args = parser.parse_args()

    current = read_version()
    new_version = next_version(current, args.bump)
    content = CONST_PATH.read_text(encoding="utf-8")
    updated = VERSION_PATTERN.sub(
        lambda match: f"{match.group('prefix')}{new_version}{match.group('suffix')}",
        content,
        count=1,
    )
    CONST_PATH.write_text(updated, encoding="utf-8")
    print(f"Bumped version {current} -> {new_version} in {CONST_PATH}")
    print("Next: update CHANGELOG.md, then run 'make release-check'.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
