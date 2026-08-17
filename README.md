# Missing-AG-Updater

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python Versions](https://img.shields.io/badge/python-3.10%20%7C%203.11%20%7C%203.12%20%7C%203.13-blue.svg)](https://www.python.org/)
[![uv](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/uv/main/assets/badge/v0.json)](https://github.com/astral-sh/uv)
[![Checked with mypy](https://www.mypy-lang.org/static/mypy_badge.svg)](https://mypy-lang.org/)
[![Code style: ruff](https://img.shields.io/badge/code%20style-ruff-000000.svg)](https://github.com/astral-sh/ruff)

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
> **Disclaimer:** This project is a community fork of [Kx101/missing-ag-updater](https://github.com/Kx101/missing-ag-updater).
> It is an unofficial utility and is **NOT** affiliated with, sponsored by, or supported by Google LLC.

A fast, reliable installer and auto-updater for the **Google Antigravity** developer suite on Linux:
- **Antigravity IDE** (VS Code-based AI Editor)
- **Antigravity Hub** (Standalone Agent Desktop Application)
- **Antigravity CLI** (`agy` command-line tool)

---

## ⚡ Quick Start (Linux)

### 1. Install the Updater

The fastest and cleanest way to run or install is via [`uv`](https://github.com/astral-sh/uv):

```bash
# Option A: Run immediately without installing
uvx --from git+https://github.com/angrysky56/missing-ag-updater.git antigravity-updater
```

```bash
# Option B: Install globally to ~/.local/bin (Recommended)
uv tool install git+https://github.com/angrysky56/missing-ag-updater.git
```

*(Alternatively, use `pipx install git+https://github.com/angrysky56/missing-ag-updater.git`)*

---

### 2. Install or Upgrade Antigravity

By default, the updater automatically checks Google's release feed, downloads missing or out-of-date tools, creates desktop launcher icons, and configures CLI symlinks:

```bash
# Install / Upgrade to your user directory (Recommended - No sudo required):
antigravity-updater
```

```bash
# Or install system-wide in /opt (Requires sudo):
# 1. If installed globally via uv tool / pipx:
sudo env "PATH=$PATH" antigravity-updater --system

# 2. Or if running directly from this cloned repo / virtualenv:
sudo ./.venv/bin/antigravity-updater --system
```

---

## 📂 Linux Default Locations

The updater places files in standard Linux locations so tools seamlessly show up in your application menu and shell:

| Component | User Scope (Default / Recommended) | System Scope (`--system`) |
| :--- | :--- | :--- |
| **Permissions** | **No `sudo` needed** | Requires `sudo` |
| **Antigravity IDE** | `~/opt/Antigravity-IDE` | `/opt/antigravity-ide` |
| **Antigravity Hub** | `~/opt/Antigravity-x64` | `/opt/antigravity` |
| **Antigravity CLI (`agy`)** | `~/.local/bin/agy` | `/usr/local/bin/agy` |
| **Terminal Launchers** | `~/.local/bin/antigravity-ide`<br>`~/.local/bin/antigravity` | `/usr/local/bin/antigravity-ide`<br>`/usr/local/bin/antigravity` |
| **Desktop Menu Icons** | `~/.local/share/applications/` | `/usr/share/applications/` |

> [!NOTE]
> Make sure `~/.local/bin` is in your `$PATH` (e.g. in `~/.bashrc` or `~/.zshrc`) so you can run `agy` and `antigravity-ide` directly from your terminal.

---

## 🛠️ Common Linux Commands

### Check for Updates (Dry Run)
Check if newer versions of the IDE, Hub, or CLI exist upstream without changing anything:
```bash
antigravity-updater --check
```

### Inspect Installed Components & Versions (Diagnostics)
Scan all existing installations, versions, `.desktop` files, and AppArmor status:
```bash
antigravity-updater --diagnose
```

### Update Only a Specific Component
```bash
antigravity-updater --ide   # Update only IDE
antigravity-updater --cli   # Update only CLI
antigravity-updater --hub   # Update only Hub
```

### Clean Duplicate Desktop Launcher Icons
If past installs or manual extractions left duplicate or broken icons in your app menu:
```bash
antigravity-updater --clean-duplicates
```

### Clean Uninstall
Remove installed applications, launcher symlinks, desktop entries, and icons:
```bash
# Uninstall user-level installation:
antigravity-updater --uninstall

# Uninstall system-wide installation:
sudo env "PATH=$PATH" antigravity-updater --uninstall --system
# (or from cloned repo: sudo ./.venv/bin/antigravity-updater --uninstall --system)
```

---

## 📁 GNOME Nautilus Integration

On GNOME desktops, the updater automatically installs a context-menu extension so you can right-click any folder and choose **"Open in Antigravity IDE"**.

### Prerequisites:
```bash
# Ubuntu / Debian / Pop!_OS:
sudo apt install python3-nautilus && nautilus -q

# Fedora:
sudo dnf install nautilus-python && nautilus -q

# Arch Linux:
sudo pacman -S python-nautilus && nautilus -q
```

---

## 📚 Additional Documentation

- 🐧 **[Linux Troubleshooting Guide](docs/troubleshooting-linux.md)**: Fix AppArmor / Chromium sandbox crashes (`--apparmor-sandbox`), PATH issues (`command not found: agy`), desktop duplicates, or sudo permission errors.
- ⚙️ **[Advanced Usage & Other Platforms](docs/other-platforms-and-advanced.md)**: macOS & Windows installation instructions, custom path overrides (`--dir-ide`), persistent `config.toml` options, and environment variables.
- 🤖 **[AI Agent Integration Guide](AGENTS.md)**: Diagnostic protocols, headless operation, troubleshooting recipes, and programmatic Python API.

---

## 💻 Development & Testing

```bash
# Clone repository
git clone https://github.com/angrysky56/missing-ag-updater.git
cd missing-ag-updater

# Set up virtual environment
uv venv && source .venv/bin/activate
uv pip install -e ".[dev]"

# Run tests
uv run pytest

# Lint and type check
uv run ruff check src
uv run mypy src
```

---

## 📄 License

This project is licensed under the [MIT License](LICENSE).
