# missing-ag-updater

> [!IMPORTANT]
> **Disclaimer:** This project is an unofficial, community-maintained utility. It is **NOT** affiliated with, sponsored by, or supported by Google LLC.

This repository contains a Python utility to check for and apply updates to the Google Antigravity developer suite on Linux, macOS, and Windows.

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

## Installation & Setup

Create the local virtual environment and install development tools (`pytest`, `ruff`) using `uv` and the provided `Makefile`:
```bash
make venv
```

## Usage

Run the script directly to check and update all components:
```bash
./update.py
```

### Options

```text
usage: update.py [-h] [--check] [--ide] [--hub] [--cli] [--force]
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
  ./update.py --check
  ```

- **Force update the Hub application only:**
  ```bash
  ./update.py --hub --force
  ```

- **Update only the CLI tool:**
  ```bash
  ./update.py --cli
  ```

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

## License

This project is licensed under the [MIT License](LICENSE).
