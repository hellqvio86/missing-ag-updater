# Missing-AG-Updater

[![CI/CD](https://github.com/hellqvio86/missing-ag-updater/actions/workflows/ci.yml/badge.svg)](https://github.com/hellqvio86/missing-ag-updater/actions/workflows/ci.yml)
[![Coverage](coverage.svg)](https://github.com/hellqvio86/missing-ag-updater/actions)
[![PyPI Version](https://img.shields.io/pypi/v/missing-ag-updater.svg)](https://pypi.org/project/missing-ag-updater/)
[![PyPI Downloads](https://img.shields.io/pypi/dm/missing-ag-updater.svg)](https://pypi.org/project/missing-ag-updater/)
[![Python Versions](https://img.shields.io/pypi/pyversions/missing-ag-updater.svg)](https://pypi.org/project/missing-ag-updater/)
[![uv](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/uv/main/assets/badge/v0.json)](https://github.com/astral-sh/uv)
[![Checked with mypy](https://www.mypy-lang.org/static/mypy_badge.svg)](https://mypy-lang.org/)
[![Pydantic](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/pydantic/pydantic/main/docs/badge/v2.json)](https://pydantic.dev)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

```
╔═════════════════════════════════════════════════════════════════════════════╗
║ ███╗   ███╗██╗███████╗███████╗██╗███╗   ██╗ ██████╗        █████╗  ██████╗  ║
║ ████╗ ████║██║██╔════╝██╔════╝██║████╗  ██║██╔════╝       ██╔══██╗██╔════╝  ║
║ ██╔████╔██║██║███████╗███████╗██║██╔██╗ ██║██║  ███╗█████╗███████║██║  ███╗ ║
║ ██║╚██╔╝██║██║╚════██║╚════██║██║██║╚██╗██║██║   ██║╚════╝██╔══██║██║   ██║ ║
║ ██║ ╚═╝ ██║██║███████║███████║██║██║ ╚████║╚██████╔╝      ██║  ██║╚██████╔╝ ║
║ ╚═╝     ╚═╝╚═╝╚══════╝╚══════╝╚═╝╚═╝  ╚═══╝ ╚═════╝       ╚═╝  ╚═╝ ╚═════╝  ║
║                                                                             ║
║         ██╗   ██╗██████╗ ██████╗  █████╗ ████████╗███████╗██████╗           ║
║         ██║   ██║██╔══██╗██╔══██╗██╔══██╗╚══██╔══╝██╔════╝██╔══██╗          ║
║         ██║   ██║██████╔╝██║  ██║███████║   ██║   █████╗  ██████╔╝          ║
║         ██║   ██║██╔═══╝ ██║  ██║██╔══██║   ██║   ██╔══╝  ██╔══██╗          ║
║         ╚██████╔╝██║     ██████╔╝██║  ██║   ██║   ███████╗██║  ██║          ║
║          ╚═════╝ ╚═╝     ╚═════╝ ╚═╝  ╚═╝   ╚═╝   ╚══════╝╚═╝  ╚═╝          ║
╚═════════════════════════════════════════════════════════════════════════════╝
                             Missing-AG-Updater
```

> [!IMPORTANT]
> **Disclaimer:** This project is an unofficial, community-maintained utility. It is **NOT** affiliated with, sponsored by, or supported by Google LLC.

> [!NOTE]
> **Beta Release:** This utility is currently in **beta** stage with extensive cross-platform test coverage. If you discover any edge cases, please report them on GitHub.

This repository contains a fast, reliable installer and auto-updater for the **Google Antigravity** developer suite on Linux, macOS, and Windows.

---

## Why This Project Exists

The Google Antigravity developer suite (incorporating the IDE, Hub, and CLI) is standard tooling for AI agent engineering. However, Google does not provide an official, centralized auto-updater utility to manage upgrades for all three applications under a single interface.

This leads to several developer pain points that this project solves:
* **Manual Cross-Platform Workflows**: Developers have to manually fetch Linux tarballs, mount macOS `.dmg` bundles, or run Windows installer `.exe` files for each component.
* **Corrupted Active Installs**: Attempting to upgrade files while the IDE or Hub is running in the background causes file corruption and locked processes. This tool checks and warns of active processes before writing files.
* **System & User Scope Conflicts**: Managing installations between user directories (`~/opt`) and system-wide paths (`/opt`) often results in duplicate icons and broken symlinks.
* **Ubuntu 24.04+ AppArmor Breakages**: Restrictive unprivileged user namespace policies block Electron sandbox execution unless properly configured with setuid permissions.
* **Lack of Automation for AI Agents**: AI coding agents operating in dev containers or headless environments need a simple CLI command (`antigravity-updater`) to verify and configure their tooling without manual browser navigation.

---

## Features

- **Component Support:** Independently check and upgrade:
  - **Antigravity IDE** (VS Code-based AI Editor)
  - **Antigravity Hub** (Standalone Agent Desktop Application)
  - **Antigravity CLI** (`agy` command line tool)
- **Cross-Platform:** Supports Linux (`.tar.gz`), macOS (`.dmg` mount installation), and Windows (`.exe` silent installation).
- **Scope Flexibility:** Install to user space (`--user`, `~/opt`, no root required) or system-wide (`--system`, `/opt`, requires `sudo`).
- **Machine Diagnostics:** Comprehensive system inspection (`--diagnose`) of paths, active PIDs, registered desktop entries, and AppArmor status.
- **Duplicate Entry Cleanup:** Automated cleanup tool (`--clean-duplicates`) for resolving duplicate launcher icons.
- **Clean Uninstallation:** One-command removal (`--uninstall`) of components, launcher symlinks, desktop entries, and Nautilus extensions.
- **Safe Installation:** Warns if target applications are actively running before attempting file operations (override with `--force`).
- **Checksum Verification:** Verifies SHA-512 hashes for CLI binaries prior to extraction.
- **Desktop & File Manager Integrations:** Automatically installs `.desktop` shortcuts, icon assets, and GNOME Nautilus context-menu extensions ("Open in Antigravity IDE").
- **AppArmor Compatibility:** Built-in SUID root sandbox setup (`--apparmor-sandbox`) for Ubuntu 24.04+.
- **Rich Terminal UI:** Displays progress bars and clear color status feedback.
- **Dry Run Support:** Inspect pending updates (`--check`) without modifying local files.
- **Persistent Configuration:** TOML file support (`config.toml`) and extensive environment variable controls.

---

## 📚 Documentation Guides

- [Linux Troubleshooting & Diagnostics Guide](docs/troubleshooting-linux.md)
- [Advanced Usage, Configuration & Other Platforms (macOS, Windows, Python API)](docs/other-platforms-and-advanced.md)
- [AI Assistant & Agent Instruction Guide](AGENTS.md)

---

## ⚡ Quick Start

### For Users (Recommended)

Install and run in an isolated environment via [`uv`](https://github.com/astral-sh/uv) or [`pipx`](https://github.com/pypa/pipx):

```bash
# Option A: Run immediately without installing (via uvx)
uvx --from git+https://github.com/hellqvio86/missing-ag-updater.git antigravity-updater

# Option B: Install globally using uv tool (Recommended)
uv tool install git+https://github.com/hellqvio86/missing-ag-updater.git

# Option C: Install via pipx from PyPI
pipx install missing-ag-updater
```

Once installed, the `antigravity-updater` command is globally available.

---

### 🔄 Updating the Updater

To upgrade `missing-ag-updater` itself to the newest release:

```bash
# If installed via uv tool:
uv tool upgrade missing-ag-updater
# (or force re-install from git):
uv tool install --force git+https://github.com/hellqvio86/missing-ag-updater.git

# If installed via pipx:
pipx upgrade missing-ag-updater
# (or force re-install from git):
pipx install --force git+https://github.com/hellqvio86/missing-ag-updater.git

# If running directly with uvx (force fetch latest git HEAD):
uvx --refresh --from git+https://github.com/hellqvio86/missing-ag-updater.git antigravity-updater

# If installed via pip:
pip install --upgrade missing-ag-updater
```

---

### For Developers

Create the local virtual environment and install development dependencies (`pytest`, `ruff`, `mypy`) using `uv` and the `Makefile`:

```bash
make venv
```

---

## 🚀 Usage

Run the updater to check for and apply updates across all components:

```bash
antigravity-updater
# or run directly as a Python module:
python -m missing_ag_updater
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

---

## 🛠️ CLI Options

```text
usage: antigravity-updater [-h] [--check] [--ide] [--hub] [--cli] [--force]
                           [--system] [--user] [--diagnose] [--clean-duplicates]
                           [--remove-user-dirs] [--uninstall]
                           [--dir-ide DIR_IDE] [--dir-hub DIR_HUB] [--path-cli PATH_CLI]
                           [--no-desktop] [--no-nautilus]
                           [--apparmor-sandbox] [--no-apparmor-sandbox]
                           [--config CONFIG]

Auto-updater utility for Google Antigravity developer tools (Cross-Platform).

options:
  -h, --help            show this help message and exit
  --check               Check for available updates without installing (dry run)
  --ide                 Update/operate only on the Antigravity IDE
  --hub                 Update/operate only on the Antigravity Hub
  --cli                 Update/operate only on the Antigravity CLI
  --force               Bypass version checks and active process warnings
  --system              Install/manage system-wide (/opt and /usr/local/bin)
  --user                Install/manage for current user (~/opt and ~/.local/bin)
  --diagnose, --diagnostic, --diagnostics, --doctor
                        Run complete system diagnostics on installed components
  --clean-duplicates    Clean duplicate desktop launcher entries
  --remove-user-dirs    Also remove local user opt directories during duplicate cleanup
  --uninstall           Uninstall specified components, desktop entries, and symlinks
  --dir-ide DIR_IDE     Override path to Antigravity IDE folder/bundle
  --dir-hub DIR_HUB     Override path to Antigravity Hub folder/bundle
  --path-cli PATH_CLI   Override path to Antigravity CLI binary
  --no-desktop          Skip installing local .desktop files and application icons on Linux
  --no-nautilus         Skip installing Nautilus context-menu integration on Linux
  --apparmor-sandbox    Force SUID sandbox fix on chrome-sandbox (auto-detected on AppArmor systems)
  --no-apparmor-sandbox Disable automatic SUID sandbox fix even if AppArmor is detected
  --config CONFIG       Path to custom TOML configuration file
```

---

## 💡 Common Workflow Recipes

### 1. Check for Updates (Dry Run)
```bash
antigravity-updater --check
```

### 2. Inspect Installed Versions & System State (Diagnostics)
```bash
antigravity-updater --diagnostic
# (Aliases: --diagnose, --diagnostics, --doctor)
```

### 3. Update Only a Specific Component
```bash
antigravity-updater --ide   # Update only IDE
antigravity-updater --cli   # Update only CLI
antigravity-updater --hub   # Update only Hub
```

### 4. Install / Update System-Wide (`/opt`) with `sudo`
```bash
# When installed via uv tool or pipx:
sudo env "PATH=$PATH" antigravity-updater --system

# When running from a cloned repo / local virtualenv:
sudo ./.venv/bin/antigravity-updater --system
```

### 5. Clean Duplicate Desktop Launcher Icons
If past manual installs or mixed user/system installs created duplicate icons in your application menu:
```bash
# Clean duplicate user desktop files and point launcher to system installation:
antigravity-updater --clean-duplicates --system

# Also remove obsolete local ~/opt installation directories:
antigravity-updater --clean-duplicates --system --remove-user-dirs
```

### 6. Clean Uninstallation
```bash
# Uninstall user-level installation:
antigravity-updater --uninstall --user

# Uninstall system-wide installation:
sudo env "PATH=$PATH" antigravity-updater --uninstall --system

# Uninstall only a specific tool (e.g. IDE):
antigravity-updater --uninstall --ide
```

---

## ⚙️ Environment Variables

You can configure the behavior of the auto-updater using environment variables. These act as fallbacks if CLI arguments are not explicitly provided:

| CLI Option | Environment Variables | Type | Description |
| :--- | :--- | :--- | :--- |
| `--check` | `ANTIGRAVITY_CHECK` or `AG_CHECK` | Boolean | Check for available updates without installing (dry run) |
| `--ide` | `ANTIGRAVITY_IDE` or `AG_IDE` | Boolean | Update only the Antigravity IDE |
| `--hub` | `ANTIGRAVITY_HUB` or `AG_HUB` | Boolean | Update only the Antigravity Hub |
| `--cli` | `ANTIGRAVITY_CLI` or `AG_CLI` | Boolean | Update only the Antigravity CLI |
| `--force` | `ANTIGRAVITY_FORCE` or `AG_FORCE` | Boolean | Bypass version checks and active process warnings |
| `--system` | `ANTIGRAVITY_SYSTEM` or `AG_SYSTEM` | Boolean | Target system-wide installation scope (`/opt`) |
| `--user` | `ANTIGRAVITY_USER` or `AG_USER` | Boolean | Target user installation scope (`~/opt`) |
| `--diagnose` / `--diagnostic` | `ANTIGRAVITY_DIAGNOSE` or `AG_DIAGNOSE` | Boolean | Scan system and display all installed Antigravity components, versions, and desktop files |
| `--dir-ide` | `ANTIGRAVITY_DIR_IDE` or `AG_DIR_IDE` | String | Override path to Antigravity IDE folder/bundle |
| `--dir-hub` | `ANTIGRAVITY_DIR_HUB` or `AG_DIR_HUB` | String | Override path to Antigravity Hub folder/bundle |
| `--path-cli` | `ANTIGRAVITY_PATH_CLI` or `AG_PATH_CLI` | String | Override path to Antigravity CLI binary |
| `--config` | `ANTIGRAVITY_CONFIG` or `AG_CONFIG` | String | Path to custom TOML configuration file |
| `--no-desktop` | `ANTIGRAVITY_DESKTOP` / `AG_DESKTOP` (`true`) or `ANTIGRAVITY_NO_DESKTOP` / `AG_NO_DESKTOP` (`false`) | Boolean | Set to `false` or `1` (for `NO_DESKTOP`) to skip installing `.desktop` launchers and icons |
| `--no-nautilus` | `ANTIGRAVITY_NAUTILUS` / `AG_NAUTILUS` (`true`) or `ANTIGRAVITY_NO_NAUTILUS` / `AG_NO_NAUTILUS` (`false`) | Boolean | Set to `false` or `1` (for `NO_NAUTILUS`) to skip installing the Nautilus context-menu extension |
| `--apparmor-sandbox` | `ANTIGRAVITY_APPARMOR_SANDBOX` or `AG_APPARMOR_SANDBOX` | Boolean | **(Ubuntu only)** Configure `root:root 4755` permissions on `chrome-sandbox` |

> [!NOTE]
> Boolean environment variables accept `1`, `true`, `yes`, or `on` as `True`, and any other value (or unset) as `False`.

---

## 📝 Configuration File (`config.toml`)

Save persistent configuration settings in a TOML file. The updater searches for configuration in the following standard locations:

- **Linux**: `~/.config/missing-ag-updater/config.toml` (honors `XDG_CONFIG_HOME`)
- **macOS**: `~/Library/Application Support/missing-ag-updater/config.toml`
- **Windows**: `%APPDATA%\missing-ag-updater\config.toml`

A template is provided in [`config.example.toml`](config.example.toml).

### Settings Resolution Hierarchy

Settings are resolved in the following priority order (highest to lowest):
1. **CLI Arguments** (explicitly passed)
2. **Environment Variables**
3. **TOML Configuration File**
4. **Auto-Detection / System Defaults**

### Example `config.toml`

```toml
check = false
ide = true
hub = true
cli = true
force = false
system = false
user = true
apparmor_sandbox = false  # Ubuntu only
dir_ide = "~/opt/Antigravity-IDE"
desktop = true
nautilus = true
```

---

## 📂 Default Installation Paths

When running an update, the tool first downloads packages to a temporary system directory (e.g. `/tmp` on Linux/macOS, or `%TEMP%` on Windows), installs the permanent application files, and cleans up temporary files automatically.

| Platform | Antigravity IDE Path | Antigravity Hub Path | Antigravity CLI Path | Launcher / Symlink Path |
| :--- | :--- | :--- | :--- | :--- |
| **Linux (User Scope)** | `~/opt/Antigravity-IDE` | `~/opt/Antigravity-x64` | `~/.local/bin/agy` | `~/.local/bin/antigravity-ide`<br>`~/.local/bin/antigravity` |
| **Linux (System Scope)** | `/opt/antigravity-ide` | `/opt/antigravity` | `/usr/local/bin/agy` | `/usr/local/bin/antigravity-ide`<br>`/usr/local/bin/antigravity` |
| **macOS** | `/Applications/Antigravity IDE.app` | `/Applications/Antigravity.app` | `~/.local/bin/agy` | *N/A (installed in Applications)* |
| **Windows** | `%LOCALAPPDATA%\Programs\antigravity-ide` | `%LOCALAPPDATA%\Programs\antigravity` | `%LOCALAPPDATA%\Microsoft\WindowsApps\agy.exe` | *N/A (added to PATH)* |

> [!NOTE]
> **Linux Path & Chromium SUID Sandbox Bug:**
> On Linux, the IDE default directory is `~/opt/Antigravity-IDE` (hyphenated without spaces). This avoids an upstream Chromium bug in [`zygote_host_impl_linux.cc`](https://chromium.googlesource.com/chromium/src/+/refs/heads/main/content/browser/zygote_host/zygote_host_impl_linux.cc), where binary paths containing spaces (e.g. `~/opt/Antigravity IDE`) are truncated at space boundaries when executing `chrome-sandbox` via `execvp`, crashing with `FATAL: Check failed: . : Invalid argument (22)`.
> 
> The updater automatically checks both `~/opt/Antigravity-IDE` and legacy `~/opt/Antigravity IDE` paths to resolve existing installations.

---

## 🌐 Upstream Sources (Where Google Stores the Binaries)

All application packages are fetched directly from official Google distribution servers:

* **Antigravity IDE**: Downloaded from Google's stable release CDN domains (`dl.google.com` and `edgedl.me.gvt1.com`).
* **Antigravity Hub**: Downloaded from Google's public Google Cloud Storage bucket (`storage.googleapis.com/antigravity-public`).
* **Antigravity CLI**: Downloaded from URLs specified in official update manifests hosted on Google Cloud.

---

## 🔒 How It Works

1. **Update Resolution**:
   Queries release endpoints to parse the latest version information and official Google release manifests.
2. **Process Integrity Check**:
   Before modifying files, inspects whether the IDE, Hub, or CLI is actively running. If active PIDs are detected, the update safely aborts (unless overridden with `--force`).
3. **Secure CLI Checksum Verification**:
   Validates the SHA-512 cryptographic hash of downloaded CLI archives prior to extraction.
4. **Platform-Specific Installation**:
   - **Linux**: Extracts tarballs to temporary directories, replaces target installation directories under `~/opt` or `/opt`, and creates/updates symlinks in `~/.local/bin` or `/usr/local/bin`.
   - **macOS**: Mounts `.dmg` disk images securely via `hdiutil attach`, syncs `.app` bundles under `/Applications`, and unmounts the volume.
   - **Windows**: Executes installer binaries with silent installation flags (`/S`) for seamless background upgrades.

---

## 🖥️ Launching the Applications

Once updated, launch the tools using standard terminal commands:

- **Antigravity IDE** (VS Code-based AI Editor):
  ```bash
  antigravity-ide
  ```
- **Antigravity Hub** (Standalone agent desktop application):
  ```bash
  antigravity
  ```
- **Antigravity CLI** (Command line interface):
  ```bash
  agy
  ```

---

## 📁 GNOME Nautilus Context Menu Integration (Linux)

On Linux systems running GNOME, the updater installs a context-menu extension for Nautilus, allowing you to right-click folders or files and select **"Open in Antigravity IDE"**.

### Prerequisites

Install `nautilus-python` bindings using your package manager:

- **Ubuntu / Debian**:
  ```bash
  sudo apt install python3-nautilus && nautilus -q
  ```
- **Fedora**:
  ```bash
  sudo dnf install nautilus-python && nautilus -q
  ```
- **Arch Linux**:
  ```bash
  sudo pacman -S python-nautilus && nautilus -q
  ```

---

## 🛡️ Linux Sandbox (Ubuntu 24.04+)

On **Ubuntu 24.04+**, the kernel restricts unprivileged user namespaces via AppArmor (`apparmor_restrict_unprivileged_userns`), breaking the Chromium namespace sandbox used by Electron applications.

Without a fix, the IDE crashes on startup with:
```text
FATAL:zygote_host_impl_linux.cc ... Check failed: . : Invalid argument (22)
```

### The Fix: `--apparmor-sandbox`

Pass `--apparmor-sandbox` to configure the `chrome-sandbox` binary with SUID root permissions (`root:root 4755`):

```bash
# During update:
sudo env "PATH=$PATH" antigravity-updater --apparmor-sandbox

# Or set it in your config.toml:
# ~/.config/missing-ag-updater/config.toml
apparmor_sandbox = true
```

---

## 💻 Development

The project includes a `Makefile` to simplify development tasks:

- **Run updater (via module):**
  ```bash
  make run
  make run ARGS="--check"
  ```
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

### Git Hooks

A local Git `pre-push` hook is configured to automatically run formatting, linting checks, and the unit test suite before code can be pushed:

```bash
.git/hooks/pre-push
```

---

## 🔗 Related Projects

- [Opensnap Antigravity updater](https://github.com/opensnap/antigravity)

---

## 📄 License

This project is licensed under the [MIT License](LICENSE).
