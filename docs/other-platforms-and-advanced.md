# Advanced Usage, Configuration & Other Platforms

This document covers detailed usage instructions for **macOS**, **Windows**, advanced CLI overrides, persistent TOML configuration files, environment variables, and the programmatic Python API.

---

## 1. macOS Usage

On macOS, `missing-ag-updater` downloads official `.dmg` installer images from Google, attaches them via `hdiutil`, copies `.app` bundles, and links the `agy` CLI binary.

### Default macOS Locations

| Scope | Antigravity IDE | Antigravity Hub | Antigravity CLI |
| :--- | :--- | :--- | :--- |
| **System** (Default) | `/Applications/Antigravity IDE.app` | `/Applications/Antigravity.app` | `/usr/local/bin/agy` |
| **User** | `~/Applications/Antigravity IDE.app` | `~/Applications/Antigravity.app` | `~/.local/bin/agy` |

### Running on macOS

```bash
# Update standard Applications (may require sudo for /Applications):
sudo antigravity-updater --system

# Update user-local ~/Applications without sudo:
antigravity-updater --user
```

---

## 2. Windows Usage

On Windows, `missing-ag-updater` handles `.exe` installers and sets up binary paths under `%LOCALAPPDATA%`.

### Default Windows Locations

| Component | Default Path |
| :--- | :--- |
| **Antigravity IDE** | `%LOCALAPPDATA%\Programs\antigravity-ide` |
| **Antigravity Hub** | `%LOCALAPPDATA%\Programs\antigravity` |
| **Antigravity CLI** | `%LOCALAPPDATA%\Microsoft\WindowsApps\agy.exe` |

### Running on Windows

```powershell
# Using uvx:
uvx --from git+https://github.com/hellqvio86/missing-ag-updater.git antigravity-updater

# Or after installing via pip / uv tool:
antigravity-updater
```

---

## 3. Advanced CLI Options & Overrides

For custom directory hierarchies or non-standard distributions, you can explicitly override candidate paths and behaviors:

```bash
antigravity-updater \
  --dir-ide "/custom/path/to/ide" \
  --dir-hub "/custom/path/to/hub" \
  --path-cli "/custom/bin/agy"
```

### Full Options Matrix

```text
usage: antigravity-updater [-h] [--check] [--ide] [--hub] [--cli] [--force]
                           [--system] [--user] [--diagnose] [--clean-duplicates]
                           [--remove-user-dirs] [--uninstall]
                           [--dir-ide DIR_IDE] [--dir-hub DIR_HUB] [--path-cli PATH_CLI]
                           [--no-desktop] [--no-nautilus] [--apparmor-sandbox]
                           [--config CONFIG]

options:
  -h, --help           Show this help message and exit
  --check              Check for available updates without installing (dry run)
  --ide                Target only the Antigravity IDE
  --hub                Target only the Antigravity Hub
  --cli                Target only the Antigravity CLI
  --force              Bypass version checks and active process warnings
  --system             Target system-wide installation (/opt, /usr/local/bin)
  --user               Target user-level installation (~/opt, ~/.local/bin)
  --diagnose, --doctor Scan system and display all installed Antigravity components
  --clean-duplicates   Clean duplicate desktop entries and symlinks
  --remove-user-dirs   When cleaning duplicates with system keep scope, also remove ~/opt directories
  --uninstall          Uninstall specified Antigravity components
  --dir-ide DIR_IDE    Override path to Antigravity IDE folder/bundle
  --dir-hub DIR_HUB    Override path to Antigravity Hub folder/bundle
  --path-cli PATH_CLI  Override path to Antigravity CLI binary
  --no-desktop         Skip installing local .desktop files and application icons
  --no-nautilus        Skip installing Nautilus context-menu integration
  --apparmor-sandbox   Configure root:root 4755 permissions on chrome-sandbox
  --config CONFIG      Path to custom TOML configuration file override
```

---

## 4. Configuration File (TOML)

You can persist your preferences across runs using a TOML file. The updater searches the following default locations:

- **Linux**: `~/.config/missing-ag-updater/config.toml` (honors `XDG_CONFIG_HOME`)
- **macOS**: `~/Library/Application Support/missing-ag-updater/config.toml`
- **Windows**: `%APPDATA%\missing-ag-updater\config.toml`

### Example `config.toml`

```toml
# General settings
check = false
force = false

# Component selection
ide = true
hub = true
cli = true

# Scope selection
# system = true
# user = true

# Linux integration options
desktop = true
nautilus = true
apparmor_sandbox = false

# Custom path overrides (optional)
# dir_ide = "/opt/antigravity-ide"
# dir_hub = "/opt/antigravity"
# path_cli = "/usr/local/bin/agy"
```

To load an explicit configuration file from any custom path:

```bash
antigravity-updater --config /path/to/custom-config.toml
```

---

## 5. Environment Variables

You can configure updater defaults using environment variables. These are useful in automated workflows, Docker containers, and CI/CD pipelines:

| CLI Option | Environment Variables | Type | Description |
| :--- | :--- | :--- | :--- |
| `--check` | `ANTIGRAVITY_CHECK` or `AG_CHECK` | Boolean (`1`/`0`, `true`/`false`) | Dry run: check updates without modifying files |
| `--ide` | `ANTIGRAVITY_IDE` or `AG_IDE` | Boolean | Target only Antigravity IDE |
| `--hub` | `ANTIGRAVITY_HUB` or `AG_HUB` | Boolean | Target only Antigravity Hub |
| `--cli` | `ANTIGRAVITY_CLI` or `AG_CLI` | Boolean | Target only Antigravity CLI |
| `--force` | `ANTIGRAVITY_FORCE` or `AG_FORCE` | Boolean | Bypass version and active process checks |
| `--system` | `ANTIGRAVITY_SYSTEM` or `AG_SYSTEM` | Boolean | Target system-wide installation scope |
| `--user` | `ANTIGRAVITY_USER` or `AG_USER` | Boolean | Target user-level installation scope |
| `--dir-ide` | `ANTIGRAVITY_DIR_IDE` or `AG_DIR_IDE` | String (Path) | Override path to Antigravity IDE directory |
| `--dir-hub` | `ANTIGRAVITY_DIR_HUB` or `AG_DIR_HUB` | String (Path) | Override path to Antigravity Hub directory |
| `--path-cli` | `ANTIGRAVITY_PATH_CLI` or `AG_PATH_CLI` | String (Path) | Override path to Antigravity CLI binary |
| `--no-desktop` | `ANTIGRAVITY_NO_DESKTOP` / `AG_NO_DESKTOP` | Boolean | Skip installing `.desktop` launchers and icons |
| `--no-nautilus` | `ANTIGRAVITY_NO_NAUTILUS` / `AG_NO_NAUTILUS` | Boolean | Skip Nautilus file manager extension |
| `--apparmor-sandbox` | `ANTIGRAVITY_APPARMOR_SANDBOX` / `AG_APPARMOR_SANDBOX` | Boolean | Set SUID permissions on `chrome-sandbox` |

---

## 6. Programmatic Python API

If you are writing custom Python scripts or integrating into automated agent pipelines, you can import functions directly:

```python
from missing_ag_updater.updater import update_ide, update_hub, update_cli
from missing_ag_updater.const import DEFAULT_IDE_DIR, DEFAULT_HUB_DIR, DEFAULT_CLI_BINARY
from missing_ag_updater.discovery import diagnose_all

# 1. Run system diagnostics
diagnostics = diagnose_all()
print(f"Discovered {len(diagnostics['ide_installations'])} IDE installations.")

# 2. Update the IDE
ide_success = update_ide(
    ide_dir=DEFAULT_IDE_DIR,
    launcher_path=None,
    dry_run=False,
    force=False,
)

# 3. Update the CLI
cli_success = update_cli(
    cli_binary=DEFAULT_CLI_BINARY,
    dry_run=False,
    force=False,
)
```
