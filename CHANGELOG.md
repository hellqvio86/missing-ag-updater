# Changelog

All notable changes to `missing-ag-updater` are documented here.
The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and the project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.7.0] - 2026-11-13

### Added

- WSL auto-detection (`is_wsl()`): inside Windows Subsystem for Linux only the CLI is installed/updated by default. Explicit `--ide` / `--hub` / `--cli` (or env/TOML equivalents) override this; `--uninstall` still targets all components.
- `wsl` key in `--json` / `diagnose_all()` output, and a WSL line in `--diagnose`.
- `ResolvedConfig.wsl` and `ResolvedConfig.wsl_cli_only` fields.

## [0.6.0] - 2026-11-13

### Added

- `--allow-unverified` / `ANTIGRAVITY_ALLOW_UNVERIFIED` / TOML `allow_unverified` as an explicit opt-out from mandatory IDE/Hub checksum verification.
- `--json` diagnostics output with stable keys: `updater_version`, `os`, `arch`, `ide_installations`, `hub_installations`, `cli_installations`, `running_processes`, `desktop_files`, and `sandbox_status`.
- `--debug` / `ANTIGRAVITY_DEBUG` / TOML `debug` logging for endpoint URLs, checksum outcomes, and process-detection decisions (stderr only).
- Release endpoint overrides with ordered, comma-separated fallbacks:
  - `ANTIGRAVITY_IDE_RELEASES_URL` / `AG_IDE_RELEASES_URL`
  - `ANTIGRAVITY_HUB_RELEASES_URL` / `AG_HUB_RELEASES_URL`
  - `ANTIGRAVITY_CLI_MANIFEST_URL` / `AG_CLI_MANIFEST_URL`
- `ReleaseEndpointError`, which reports every attempted URL and HTTP status.
- Release metadata download URLs (`download_url`, `url`, and `downloads` maps) are now preferred over hard-coded CDN path construction, after allowlist validation.
- Legacy Ubuntu spaced IDE directory migration for default `~/opt` and `/opt` parents.
- Platform smoke tests for macOS DMG, Windows EXE, and unverified-archive refusal.
- Transparent rollback tests for IDE and Hub installs.
- Manual platform test matrix and release process documentation.
- `bin/bump_version.py`, `make version`, and `make release-check`.

### Changed

- The package version now has a single source of truth: `__version__` in `src/missing_ag_updater/const.py`. `pyproject.toml` reads it dynamically through Hatchling.
- IDE and Hub checksum verification now **fails closed** when release metadata supplies no SHA-512/SHA-256. CLI archives still always require SHA-512.
- Process detection was refactored into pure, testable helpers with reduced false positives.
- CI enforces a minimum test coverage of 85% (`--cov-fail-under=85`).
- README, agent instructions, advanced usage, and Linux troubleshooting docs cover the new flags, endpoint overrides, JSON output, and process-detection limits.

### Removed

- Automatic post-install deletion of legacy IDE directories. Migration now only renames a default-parent legacy folder; custom paths are left untouched.
- Broad `/bin/agy` process matching that could block unrelated binaries.

### Security

- Additional tests cover uninstall parent-directory safeguards, domain allowlisting, and checksum refusal paths.
- No `shell=True` usage was introduced; subprocess calls remain structured argv lists.

## [0.5.3] - Previous release

See the GitHub releases page for changes before 0.6.0.

[Unreleased]: https://github.com/hellqvio86/missing-ag-updater/compare/v0.7.0...HEAD
[0.7.0]: https://github.com/hellqvio86/missing-ag-updater/compare/v0.6.0...v0.7.0
[0.6.0]: https://github.com/hellqvio86/missing-ag-updater/compare/v0.5.3...v0.6.0
