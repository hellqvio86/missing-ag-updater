# Changelog

All notable changes to `missing-ag-updater` are documented in this file.

## [Unreleased]

## [0.8.3] - 2026-11-21

### Bug Fixes

- **Windows IDE Path & Version Detection (`const.py`, `discovery.py`, `utils.py`):** Updated Windows `USER_IDE_DIR` from `%LOCALAPPDATA%\Programs\antigravity-ide` to `%LOCALAPPDATA%\Programs\Antigravity IDE` (matching the official Windows installer's `win32DirName`) with fallback discovery and path resolution for `antigravity-ide`, fixing `Local IDE Version: 0.0.0` false-positive updates on Windows.

## [0.8.1] - 2026-11-21

### Added

- **Outdated Updater Warning (`updater.py`, `cli.py`):** Added a non-blocking, best-effort PyPI version check (`start_updater_version_check()`, `check_for_updater_update()`, `warn_if_updater_outdated()`) running in a daemon thread that warns when a newer release of `missing-ag-updater` is available and fails open when offline.
- **Windows Installer Mode Configuration (`--interactive` / `--silent`):** Added CLI flags (`--interactive`, `--silent`), environment variables (`ANTIGRAVITY_INTERACTIVE`, `AG_INTERACTIVE`), and TOML config key (`interactive`) to choose between silent (default) and interactive Windows installation.

### Bug Fixes

- **Silent Windows Installer Flags (`updater.py`):** Pass both NSIS (`/S`) and Inno Setup (`/VERYSILENT /SUPPRESSMSGBOXES /NORESTART`) flags in `install_windows_exe()` when running in silent mode so Inno Setup-based IDE installers do not open an interactive wizard.

## [0.7.3] - 2026-11-21

### Bug Fixes

- **Windows Missing-Checksum Handling (`updater.py`):** Warn and proceed with the Windows installer instead of failing closed when the IDE or Hub release endpoint omits SHA-512/SHA-256 checksums; explicit checksum mismatches still fail.

## [0.7.2] - 2026-11-16

### Bug Fixes

- **Windows CLI `.exe` Downloads (`updater.py`):** Handle standalone `.exe` downloads in `update_cli()` on Windows instead of attempting `.tar.gz` extraction.
- **Windows Subprocess Encoding (`utils.py`):** Pass `encoding="utf-8"` and `errors="replace"` to `subprocess.run(..., text=True)` calls to prevent `UnicodeDecodeError` in Python 3.15+ when Windows tools (such as `tasklist`) emit non-UTF-8 bytes.

## [0.7.1] - 2026-11-14

### Changed & Improved

- **Centralized Constants (`const.py`):** Consolidated scattered module-level constants (environment variable mappings, fallback CDN base URLs, Linux/macOS discovery roots and candidate paths, AppArmor/OS-release paths, `.desktop`/icon/Nautilus filenames, version regex, and process/parent-directory marker tuples) into `src/missing_ag_updater/const.py`.

## [0.7.0] - 2026-11-13

### Added

- **WSL CLI-Only Default (`config.py`, `cli.py`):** Added `is_wsl()` auto-detection so inside Windows Subsystem for Linux only the CLI is installed/updated by default; explicit `--ide`, `--hub`, or `--cli` flags (or env/TOML equivalents) override this, while `--uninstall` still targets all components.
- **WSL Diagnostics (`--json` / `--diagnose`):** Added `wsl` key to `--json` / `diagnose_all()` output, a WSL status line in `--diagnose`, and `ResolvedConfig.wsl` / `ResolvedConfig.wsl_cli_only` fields.

## [0.6.0] - 2026-11-13

### Added

- **Checksum Opt-Out (`--allow-unverified`):** Added `--allow-unverified`, `ANTIGRAVITY_ALLOW_UNVERIFIED` / `AG_ALLOW_UNVERIFIED`, and TOML `allow_unverified` as an explicit opt-out from mandatory IDE/Hub checksum verification.
- **Machine-Readable Diagnostics (`--json`):** Added `--json` output with stable keys (`updater_version`, `os`, `arch`, `ide_installations`, `hub_installations`, `cli_installations`, `running_processes`, `desktop_files`, `sandbox_status`).
- **Debug Logging (`--debug`):** Added `--debug`, `ANTIGRAVITY_DEBUG`, and TOML `debug` logging for endpoint URLs, checksum outcomes, and process-detection decisions on `stderr`.
- **Release Endpoint Overrides:** Added ordered, comma-separated fallback URL overrides (`ANTIGRAVITY_IDE_RELEASES_URL`, `ANTIGRAVITY_HUB_RELEASES_URL`, `ANTIGRAVITY_CLI_MANIFEST_URL`, plus `AG_*` aliases) and `ReleaseEndpointError` reporting every attempted URL and HTTP status.
- **Explicit Metadata URLs & Legacy Migration:** Preferred release metadata download URLs (`download_url`, `url`, `downloads`) over hard-coded CDN paths after allowlist validation, and added legacy Ubuntu spaced IDE directory migration for default `~/opt` and `/opt` parents.
- **Testing & Release Tooling:** Added platform smoke tests, transactional rollback tests, manual platform test matrix, release process docs, `bin/bump_version.py`, `make version`, and `make release-check`.

### Security & Architecture

- **Fail-Closed Checksums & Process Detection:** Changed IDE/Hub checksum verification to fail closed when release metadata omits SHA-512/SHA-256 (CLI always requires SHA-512); refactored process detection into pure helpers and removed broad `/bin/agy` matching.
- **Single-Source Version & Coverage Gate:** Made `__version__` in `const.py` the single source of truth via Hatchling and enforced `--cov-fail-under=85` in CI.

## [0.5.3] - 2026-11-07

### Changed & Improved

- **Release & Documentation Tooling:** Added `make version` target to `Makefile`, updated funding links to GitHub Sponsors, and added Buy Me a Coffee badge to `README.md`.

## [0.5.2] - 2026-11-01

### Maintenance & Dependencies

- **Dependency Updates:** Updated `pydantic`, `certifi`, `urllib3`, `mypy`, `ruff`, `pytest`, `responses`, and `types-requests`.

## [0.5.1] - 2026-08-24

### Bug Fixes

- **Official Google Release Download URLs (`updater.py`):** Updated IDE and Hub download URL construction to match the latest Google CDN layout.

## [0.5.0] - 2026-08-23

### Added

- **Transactional Updates & Rollback (`updater.py`):** Added atomic backup-and-swap installation with automatic rollback on failure for IDE and Hub updates, plus semantic version selection (`select_latest_release()`).

## [0.4.1] - 2026-08-23

### Bug Fixes

- **Review & Hardening Fixes:** Addressed code-review findings across integrity verification, path handling, and test coverage.

## [0.4.0] - 2026-08-23

### Security & Architecture

- **Security Hardening & Integrity Verification:** Enforced HTTPS Google domain allowlists (`is_trusted_download_url()`), Zip-Slip protection, safe tar extraction (`filter="data"`), and SHA-512/SHA-256 checksum validation.

## [0.3.1] - 2026-08-18

### Bug Fixes

- **Linux Packaging & Desktop Integration:** Backported improvements, official Antigravity IDE branding icon, and desktop entry/icon cache automation.

## [0.3.0] - 2026-08-17

### Added

- **Discovery, Diagnostics & Uninstallation (`discovery.py`, `cli.py`):** Added `--diagnose` / `--uninstall` / `--clean-duplicates`, system and user installation discovery, Hub SUID sandbox support, and Pythonic test suite improvements.

## [0.2.1] - 2026-08-16

### Bug Fixes

- **AppArmor & SUID Sandbox Fixes:** Added `--suid-sandbox` / `--no-apparmor-sandbox` preflight checks, `is_apparmor_enabled()` detection, Ubuntu hyphenated `Antigravity-IDE` path handling to avoid Chromium zygote truncation, and `config.example.toml`.

## [0.2.0] - 2026-07-27

### Bug Fixes

- **ASAR Header & Hub Version Detection (`utils.py`):** Fixed `app.asar` Chromium Pickle header parsing (`_read_asar_header()`) to read exact JSON byte length, resolving `0.0.0` Hub version detection and icon extraction.
- **Compatibility Flags:** Added `--ubuntu` / `--suid-sandbox` support and `make install` target.

## [0.1.9] - 2026-07-26

### Maintenance & Dependencies

- **Toolchain & Dependency Updates:** Updated `ruff`, `mypy`, `pytest`, `responses`, `types-requests`, and `actions/setup-python`.

## [0.1.8] - 2026-06-26

### Added

- **Network Request Retries (`utils.py`):** Implemented automatic retry/backoff logic for release metadata and archive downloads, plus `make run` target.

## [0.1.7] - 2026-06-20

### Maintenance & Dependencies

- **Docs & Dependency Updates:** Enhanced `README.md` badges and updated `pytest`, `ruff`, and `actions/checkout`.

## [0.1.6] - 2026-06-14

### Added

- **TOML Configuration Support (`config.py`):** Added `config.toml` loading (`--config`, `ANTIGRAVITY_CONFIG`, XDG/macOS/Windows default paths) with CLI > env > TOML > default precedence.

## [0.1.5] - 2026-06-13

### Bug Fixes

- **Nautilus 4.1+ & Test Isolation:** Fixed GNOME Nautilus Python extension compatibility for Nautilus 4.1+ and resolved host-state test isolation issues.

## [0.1.4] - 2026-06-13

### Changed & Improved

- **Modular Linux Integrations & Env Fallbacks:** Split desktop entry and Nautilus integrations into `desktop.py` and `nautilus.py`, added environment variable fallbacks, and automated release draft changelog generation.

## [0.1.3] - 2026-06-13

### Changed & Improved

- **Documentation & Project Branding:** Expanded `README.md` with project motivation, disclaimer, badges, and related projects section.

## [0.1.2] - 2026-06-13

### Changed & Improved

- **`requests` Migration & Python 3.14 Compatibility:** Replaced `urllib.request` with `requests` (and `responses` in tests), and resolved Python 3.14 `tarfile` extraction deprecation warnings.

## [0.1.1] - 2026-06-13

### Changed & Improved

- **Modular Refactor & Agent Docs:** Refactored codebase into decoupled modules (`cli.py`, `updater.py`, `utils.py`, `models.py`, `const.py`), rewrote the test suite, and added `AGENTS.md`.

## [0.1.0] - 2026-06-13

### Added

- **Initial Release:** Unofficial auto-updater for Google Antigravity IDE, Hub, and CLI across Linux, macOS, and Windows.

[Unreleased]: https://github.com/hellqvio86/missing-ag-updater/compare/v0.8.3...HEAD
[0.8.3]: https://github.com/hellqvio86/missing-ag-updater/compare/v0.8.1...v0.8.3
[0.8.1]: https://github.com/hellqvio86/missing-ag-updater/compare/v0.7.3...v0.8.1
[0.7.3]: https://github.com/hellqvio86/missing-ag-updater/compare/v0.7.2...v0.7.3
[0.7.2]: https://github.com/hellqvio86/missing-ag-updater/compare/v0.7.1...v0.7.2
[0.7.1]: https://github.com/hellqvio86/missing-ag-updater/compare/v0.7.0...v0.7.1
[0.7.0]: https://github.com/hellqvio86/missing-ag-updater/compare/v0.6.0...v0.7.0
[0.6.0]: https://github.com/hellqvio86/missing-ag-updater/compare/v0.5.3...v0.6.0
[0.5.3]: https://github.com/hellqvio86/missing-ag-updater/compare/v0.5.2...v0.5.3
[0.5.2]: https://github.com/hellqvio86/missing-ag-updater/compare/v0.5.1...v0.5.2
[0.5.1]: https://github.com/hellqvio86/missing-ag-updater/compare/v0.5.0...v0.5.1
[0.5.0]: https://github.com/hellqvio86/missing-ag-updater/compare/v0.4.1...v0.5.0
[0.4.1]: https://github.com/hellqvio86/missing-ag-updater/compare/v0.4.0...v0.4.1
[0.4.0]: https://github.com/hellqvio86/missing-ag-updater/compare/v0.3.1...v0.4.0
[0.3.1]: https://github.com/hellqvio86/missing-ag-updater/compare/v0.3.0...v0.3.1
[0.3.0]: https://github.com/hellqvio86/missing-ag-updater/compare/v0.2.1...v0.3.0
[0.2.1]: https://github.com/hellqvio86/missing-ag-updater/compare/v0.2.0...v0.2.1
[0.2.0]: https://github.com/hellqvio86/missing-ag-updater/compare/v0.1.9...v0.2.0
[0.1.9]: https://github.com/hellqvio86/missing-ag-updater/compare/v0.1.8...v0.1.9
[0.1.8]: https://github.com/hellqvio86/missing-ag-updater/compare/v0.1.7...v0.1.8
[0.1.7]: https://github.com/hellqvio86/missing-ag-updater/compare/v0.1.6...v0.1.7
[0.1.6]: https://github.com/hellqvio86/missing-ag-updater/compare/v0.1.5...v0.1.6
[0.1.5]: https://github.com/hellqvio86/missing-ag-updater/compare/v0.1.4...v0.1.5
[0.1.4]: https://github.com/hellqvio86/missing-ag-updater/compare/v0.1.3...v0.1.4
[0.1.3]: https://github.com/hellqvio86/missing-ag-updater/compare/v0.1.2...v0.1.3
[0.1.2]: https://github.com/hellqvio86/missing-ag-updater/compare/v0.1.1...v0.1.2
[0.1.1]: https://github.com/hellqvio86/missing-ag-updater/compare/v0.1.0...v0.1.1
[0.1.0]: https://github.com/hellqvio86/missing-ag-updater/releases/tag/v0.1.0
