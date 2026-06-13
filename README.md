# Antigravity Tools Updater

This repository contains a Python utility to check for and apply updates to the Google Antigravity developer suite on Linux.

## Features

- **Component Support:** Independently check and upgrade:
  - **Antigravity IDE** (VS Code-based AI Editor)
  - **Antigravity Hub** (Standalone Agent Desktop Application)
  - **Antigravity CLI** (`agy` command line tool)
- **Safe Installation:** Warns if the target application is running before attempting to overwrite files.
- **Verification:** Downloads the CLI directly and verifies SHA512 checksums prior to installation.
- **Rich Terminal UI:** Displays download progress bars and clear success/warning logs.
- **Dry Run Support:** Check if any updates are available without changing any files.

## Usage

Run the script to update all components:
```bash
./update.py
```

### Options

```text
usage: update.py [-h] [--check] [--ide] [--hub] [--cli] [--force]

Auto-updater utility for Google Antigravity developer tools.

options:
  -h, --help  show this help message and exit
  --check     Check for available updates without installing (dry run)
  --ide       Update only the Antigravity IDE
  --hub       Update only the Antigravity Hub
  --cli       Update only the Antigravity CLI
  --force     Bypass version checks and active process warnings
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
