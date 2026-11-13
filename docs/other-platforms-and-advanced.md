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

**Gotchas:** writing to `/Applications` requires `sudo`; use `--user` for a rootless install. The updater mounts the DMG with `hdiutil attach`, copies the `.app`, then detaches it. If a volume is busy, check Finder for a still-mounted Antigravity image before retrying. macOS process detection uses `pgrep`, so a renamed or wrapped binary may not be detected; verify with `--diagnose`.

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

**Gotchas:** installers run silently with `/S`; close Antigravity windows first because Windows cannot replace locked files. PATH changes may only appear in a newly opened terminal. Process detection uses `tasklist`, so Electron child processes and renamed binaries can be missed; `--debug` shows the decisions.

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
                           [--ignore-self-update] [--allow-unverified] [--debug]
                           [--system] [--user] [--diagnose] [--json]
                           [--clean-duplicates] [--remove-user-dirs] [--uninstall]
                           [--dir-ide DIR_IDE] [--dir-hub DIR_HUB] [--path-cli PATH_CLI]
                           [--no-desktop] [--no-nautilus]
                           [--apparmor-sandbox] [--no-apparmor-sandbox]
                           [--config CONFIG]

options:
  -h, --help            Show this help message and exit
  --check               Check for available updates without installing (dry run)
  --ide                 Target only the Antigravity IDE
  --hub                 Target only the Antigravity Hub
  --cli                 Target only the Antigravity CLI
  --force               Bypass version checks and active process warnings
  --ignore-self-update  Update the CLI even if the official 'agy' self-updater is detected
  --allow-unverified    Install IDE/Hub archives without a checksum (fails closed by default)
  --debug               Log exact URLs, checksum results, and process decisions to stderr
  --system              Target system-wide installation (/opt, /usr/local/bin)
  --user                Target user-level installation (~/opt, ~/.local/bin)
  --diagnose, --diagnostic, --diagnostics, --doctor
                        Scan system and display all installed Antigravity components
  --json                Print diagnostics as JSON and exit (implies --diagnose)
  --clean-duplicates    Clean duplicate desktop entries and symlinks
  --remove-user-dirs    When cleaning duplicates with system keep scope, also remove ~/opt directories
  --uninstall           Uninstall specified Antigravity components
  --dir-ide DIR_IDE     Override path to Antigravity IDE folder/bundle
  --dir-hub DIR_HUB     Override path to Antigravity Hub folder/bundle
  --path-cli PATH_CLI   Override path to Antigravity CLI binary
  --no-desktop          Skip installing local .desktop files and application icons
  --no-nautilus         Skip installing Nautilus context-menu integration
  --apparmor-sandbox    Configure root:root 4755 permissions on chrome-sandbox
  --no-apparmor-sandbox Disable automatic SUID sandbox fix even on AppArmor systems
  --config CONFIG       Path to custom TOML configuration file override
```

### Machine-readable diagnostics

```bash
# Structured JSON for agents and CI:
antigravity-updater --json | jq '.ide_installations'

# Debug logs (stderr) include endpoint URLs, checksum outcomes, and process decisions:
antigravity-updater --check --debug
```

`--json` prints diagnostics and exits without updating anything. Keys: `updater_version`, `os`, `arch`, `ide_installations`, `hub_installations`, `cli_installations`, `running_processes`, `desktop_files`, `sandbox_status`.

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
ignore_self_update = false
allow_unverified = false  # only for explicitly trusted endpoints
debug = false

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
| `--ignore-self-update` | `ANTIGRAVITY_IGNORE_SELF_UPDATE` or `AG_IGNORE_SELF_UPDATE` | Boolean | Update the CLI even when the official `agy` self-updater is detected |
| `--allow-unverified` | `ANTIGRAVITY_ALLOW_UNVERIFIED` or `AG_ALLOW_UNVERIFIED` | Boolean | Install IDE/Hub archives even without a checksum (default: fail closed) |
| `--debug` | `ANTIGRAVITY_DEBUG` or `AG_DEBUG` | Boolean | Log URLs, checksum results, and process decisions to stderr |
| `--system` | `ANTIGRAVITY_SYSTEM` or `AG_SYSTEM` | Boolean | Target system-wide installation scope |
| `--user` | `ANTIGRAVITY_USER` or `AG_USER` | Boolean | Target user-level installation scope |
| `--dir-ide` | `ANTIGRAVITY_DIR_IDE` or `AG_DIR_IDE` | String (Path) | Override path to Antigravity IDE directory |
| `--dir-hub` | `ANTIGRAVITY_DIR_HUB` or `AG_DIR_HUB` | String (Path) | Override path to Antigravity Hub directory |
| `--path-cli` | `ANTIGRAVITY_PATH_CLI` or `AG_PATH_CLI` | String (Path) | Override path to Antigravity CLI binary |
| `--config` | `ANTIGRAVITY_CONFIG` or `AG_CONFIG` | String (Path) | Explicit TOML configuration file |
| `--no-desktop` | `ANTIGRAVITY_NO_DESKTOP` / `AG_NO_DESKTOP` | Boolean | Skip installing `.desktop` launchers and icons |
| `--no-nautilus` | `ANTIGRAVITY_NO_NAUTILUS` / `AG_NO_NAUTILUS` | Boolean | Skip Nautilus file manager extension |
| `--apparmor-sandbox` | `ANTIGRAVITY_APPARMOR_SANDBOX` / `AG_APPARMOR_SANDBOX` | Boolean | Set SUID permissions on `chrome-sandbox` |
| *(none)* | `ANTIGRAVITY_IDE_RELEASES_URL` / `AG_IDE_RELEASES_URL` | String | IDE release endpoint override (comma-separated fallbacks) |
| *(none)* | `ANTIGRAVITY_HUB_RELEASES_URL` / `AG_HUB_RELEASES_URL` | String | Hub release endpoint override (comma-separated fallbacks) |
| *(none)* | `ANTIGRAVITY_CLI_MANIFEST_URL` / `AG_CLI_MANIFEST_URL` | String | CLI manifest endpoint override (comma-separated fallbacks) |

> Boolean values accept `1/true/yes/on` and `0/false/no/off`. Release endpoint overrides are environment-only; they are not read from the TOML file.

---

## 6. Programmatic Python API

If you are writing custom Python scripts or integrating into automated agent pipelines, you can import functions directly:

```python
from missing_ag_updater import (
    ReleaseEndpointError,
    __version__,
    diagnose_all,
    resolve_config,
    set_debug_enabled,
    update_cli,
    update_ide,
)
from missing_ag_updater.updater import fetch_release_payload

print(f"missing-ag-updater {__version__}")

# Optional: mirror `--debug` logging (stderr).
set_debug_enabled(True)

# 1. Run system diagnostics (structured dict).
diagnostics = diagnose_all()
print(f"Discovered {len(diagnostics['ide_installations'])} IDE installations.")

# 2. Resolve paths exactly like the CLI (flags > env > TOML > auto-detect).
cfg = resolve_config()

# 3. Dry-run an IDE update. `allow_unverified` defaults to False (fail closed).
try:
    fetch_release_payload("ide")
    ide_success = update_ide(
        cfg.dir_ide,
        cfg.ide_launcher,
        dry_run=True,
        allow_unverified=cfg.allow_unverified,
        scope=cfg.scope,
    )
except ReleaseEndpointError as endpoint_error:
    print(f"All IDE metadata endpoints failed: {endpoint_error}")

# 4. Update the CLI (respects official self-update detection).
cli_success = update_cli(
    cfg.path_cli,
    dry_run=True,
    ignore_self_update=cfg.ignore_self_update,
    scope=cfg.scope,
)
```
