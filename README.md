# missing-ag-updater

[![CI/CD](https://github.com/hellqvio86/missing-ag-updater/actions/workflows/ci.yml/badge.svg)](https://github.com/hellqvio86/missing-ag-updater/actions/workflows/ci.yml)
[![Coverage](coverage.svg)](https://github.com/hellqvio86/missing-ag-updater/actions)
[![PyPI Version](https://img.shields.io/pypi/v/missing-ag-updater.svg)](https://pypi.org/project/missing-ag-updater/)
[![Python Versions](https://img.shields.io/pypi/pyversions/missing-ag-updater.svg)](https://pypi.org/project/missing-ag-updater/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

> [!IMPORTANT]
> **Disclaimer:** This project is an unofficial, community-maintained utility. It is **NOT** affiliated with, sponsored by, or supported by Google LLC.

> [!WARNING]
> **Alpha Software:** This utility is currently in an early **alpha** stage of development. Features may change without notice, and bugs may occur. Use with caution.

This repository contains a Python utility to check for and apply updates to the Google Antigravity developer suite on Linux, macOS, and Windows.

---

## Why This Project Exists

The Google Antigravity developer suite (incorporating the IDE, Hub, and CLI) is standard tooling for AI agent engineering. However, Google does not provide an official, centralized auto-updater utility to manage upgrades for all three applications under a single interface. 

This leads to several developer pain points that this project solves:
* **Manual Cross-Platform Workflows**: Developers have to manually fetch Linux tarballs, mount macOS `.dmg` bundles, or run Windows installer `.exe` files for each component.
* **Corrupted Active Installs**: Attempting to upgrade files while the IDE or Hub is running in the background causes file corruption and locked processes. This tool checks and warns of active processes before writing files.
* **Lack of Automation for AI Agents**: AI coding agents operating in dev containers or headless environments need a simple CLI command (`antigravity-updater`) to verify and configure their tooling without manual browser navigation.

---

## Features

- **Component Support:** Independently check and upgrade:
  - **Antigravity IDE** (VS Code-based AI Editor)
  - **Antigravity Hub** (Standalone Agent Desktop Application)
  - **Antigravity CLI** (`agy` command line tool)
- **Cross-Platform:** Supports Linux (`.tar.gz`), macOS (`.dmg` mount installation), and Windows (`.exe` silent installation).
- **Safe Installation:** Warns if the target application is running before attempting to overwrite files.
- **Verification:** Downloads the CLI directly and verifies SHA512 checksums prior to installation.
- **Rich Terminal UI:** Displays download progress bars and clear success/warning logs.
- **Dry Run Support:** Check if any updates are available without changing any files.
- **Development Tooling:** Complete with linter, test coverage, and environment creation via `uv`.

## Installation

### For Users (via pipx)

The recommended way to install and run the tool in an isolated environment is via `pipx`:

```bash
# Install the stable release from PyPI (recommended):
pipx install missing-ag-updater

# Alternatively, install the development version directly from GitHub:
pipx install git+https://github.com/hellqvio86/missing-ag-updater.git
```

Once installed, the `antigravity-updater` command will be globally available.

### For Developers

Create the local virtual environment and install development tools (`pytest`, `ruff`) using `uv` and the provided `Makefile`:
```bash
make venv
```

## Usage

Run the package directly to check and update all components:
```bash
python -m missing_ag_updater
# or using the installed entrypoint:
antigravity-updater
```

### Example Output

```text
$ antigravity-updater

=== Unofficial Antigravity Applications Auto-Updater (missing-ag-updater) ===
⚠ This project is a community tool and is NOT affiliated with, sponsored by, or supported by Google.
  Target Platform: linux (x64)

⠋ Checking for Antigravity IDE updates...
  Local IDE Version:  2.0.4
  Latest IDE Version: 2.0.4
✓ Antigravity IDE is up to date.

⠋ Checking for Antigravity Hub updates...
  Local Hub Version:  2.1.4
  Latest Hub Version: 2.1.4
✓ Antigravity Hub is up to date.

⠋ Checking for Antigravity CLI updates...
  Local CLI Version:  1.0.8
  Latest CLI Version: 1.0.8
✓ Antigravity CLI is up to date.

✓ Operation completed successfully.
```

### Options

```text
usage: python -m missing_ag_updater [-h] [--check] [--ide] [--hub] [--cli] [--force]
                 [--dir-ide DIR_IDE] [--dir-hub DIR_HUB] [--path-cli PATH_CLI]

Auto-updater utility for Google Antigravity developer tools (Cross-Platform).

options:
  -h, --help         show this help message and exit
  --check            Check for available updates without installing (dry run)
  --ide              Update only the Antigravity IDE
  --hub              Update only the Antigravity Hub
  --cli              Update only the Antigravity CLI
  --force            Bypass version checks and active process warnings
  --dir-ide DIR_IDE  Override path to Antigravity IDE folder/bundle
  --dir-hub DIR_HUB  Override path to Antigravity Hub folder/bundle
  --path-cli PATH_CLI Override path to Antigravity CLI binary
```

### Examples

- **Dry run check for all tools:**
  ```bash
  python -m missing_ag_updater --check
  ```

- **Force update the Hub application only:**
  ```bash
  python -m missing_ag_updater --hub --force
  ```

- **Update only the CLI tool:**
  ```bash
  python -m missing_ag_updater --cli
  ```

## Default Installation Paths

When running an update, the tool first downloads the application packages (such as `.tar.gz`, `.dmg`, or `.exe` installers) to a **temporary system directory** (e.g. `/tmp` on Linux/macOS, or `%TEMP%` on Windows). Once the extraction and installation are complete, these temporary files are automatically deleted.

After the update finishes, the permanent application files are stored in the following default paths:

| Platform | Antigravity IDE Path | Antigravity Hub Path | Antigravity CLI Path | Launcher/Symlink Path |
| :--- | :--- | :--- | :--- | :--- |
| **Linux** | `~/opt/Antigravity IDE` | `~/opt/Antigravity-x64` | `~/.local/bin/agy` | `~/.local/bin/antigravity-ide`<br>`~/.local/bin/antigravity` |
| **macOS** | `/Applications/Antigravity IDE.app` | `/Applications/Antigravity.app` | `~/.local/bin/agy` | *N/A (installed in Applications)* |
| **Windows** | `%LOCALAPPDATA%\Programs\antigravity-ide` | `%LOCALAPPDATA%\Programs\antigravity` | `%LOCALAPPDATA%\Microsoft\WindowsApps\agy.exe` | *N/A (added to PATH)* |

You can override these default paths at execution time using the `--dir-ide`, `--dir-hub`, and `--path-cli` flags.

---

## Upstream Sources (Where Google Stores the Binaries)

All application packages are fetched directly from official Google distribution servers:

* **Antigravity IDE**: Downloaded from Google's stable release CDN domains (`dl.google.com` and `edgedl.me.gvt1.com`).
* **Antigravity Hub**: Downloaded from Google's public Google Cloud Storage bucket (`storage.googleapis.com/antigravity-public`).
* **Antigravity CLI**: Downloaded from URLs specified in the official updates manifests hosted on Google Cloud.

---

## How It Works

The auto-updater acts as a secure, cross-platform layer to keep your local developer environment up to date:

1. **Update Resolution**:
   Queries the unofficial update API endpoints to parse the latest version info. For the IDE and Hub, this resolves to Google release manifests. For the CLI, it parses the architecture-specific manifest.

2. **Process Integrity Check**:
   Before writing any files, the utility checks if the IDE or Hub is currently running. If active PIDs are detected, the update will abort (unless bypassed with `--force`) to prevent file lockups and corruption.

3. **Secure CLI Checksum Verification**:
   When updating the CLI, the manifest provides a SHA-512 checksum. The tool computes the hash of the downloaded zip or tarball locally and compares them to ensure integrity before extraction.

4. **Platform-Specific Installation**:
   - **Linux**: Extracts the tarball to a temporary directory, replaces the target directory under `~/opt`, and creates/updates symbolic links under `~/.local/bin`.
   - **macOS**: Mounts the downloaded `.dmg` file securely via `hdiutil attach`, replaces the `.app` bundle under `/Applications`, and unmounts the volume.
   - **Windows**: Executes the installer binary with the silent installation flag (`/S`) to perform a background upgrade.

---

## Launching the Applications

Once updated, you can launch the Antigravity tools using their standard terminal commands:

- **Antigravity IDE** (VS Code-based AI Editor):
  ```bash
  antigravity-ide
  ```
- **Antigravity Hub** (Standalone agent desktop application):
  ```bash
  antigravity
  ```
- **Antigravity CLI** (Terminal utility):
  ```bash
  agy
  ```

## Development

The project includes a `Makefile` to simplify development tasks:

- **Lint check (Ruff):**
  ```bash
  make lint
  ```
- **Run unit tests (Pytest):**
  ```bash
  make test
  ```
- **Clean virtual environment & cache:**
  ```bash
  make clean
  ```
## Other update antigravity projects
[https://github.com/opensnap/antigravity| Opensnap Antigravity updater]

## License

This project is licensed under the [MIT License](LICENSE).
