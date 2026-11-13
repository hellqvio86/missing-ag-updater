# AI Assistant & Agent Instruction Guide (`AGENTS.md`)

This document provides system knowledge, decision trees, diagnostic workflows, and automated recipes for AI coding assistants (e.g. Antigravity Agent, Claude Code, Cursor, Copilot, Gemini, Aider) helping users install, configure, diagnose, and troubleshoot `missing-ag-updater` and the **Google Antigravity** developer suite.

---

## 🧭 System Architecture & Component Overview

The Google Antigravity developer suite consists of three distinct components:

| Component | Description | Default User Path (`--user`) | Default System Path (`--system`) | Executable Name |
| :--- | :--- | :--- | :--- | :--- |
| **Antigravity IDE** | VS Code-based AI editor | `~/opt/Antigravity-IDE` | `/opt/antigravity-ide` | `antigravity-ide` |
| **Antigravity Hub** | Standalone AI Agent desktop application | `~/opt/Antigravity-x64` | `/opt/antigravity` | `antigravity` |
| **Antigravity CLI** | Fast command-line interface | `~/.local/bin/agy` | `/usr/local/bin/agy` | `agy` |

---

## 🛠️ Step-by-Step Diagnostic & Action Protocol

When assisting a user with setup, unexpected duplicate icons, hanging processes, or version issues, execute the following protocol in order:

1. **Diagnose System State**:
   Always start by inspecting the live environment to detect active PIDs, paths, `.desktop` files, and AppArmor status:
   ```bash
   antigravity-updater --diagnostic
   ```
   For scripts or agents, prefer the stable JSON form and add `--debug` when you need URL/checksum/process decisions:
   ```bash
   antigravity-updater --json
   antigravity-updater --diagnose --debug
   ```

2. **Analyze Output & Execute Matching Action**:
   - **Duplicate `.desktop` entries / launcher icons**: Run `antigravity-updater --clean-duplicates` (use `--system` and optionally `--remove-user-dirs`).
   - **Broken Permissions / `/opt` Installation**: Run with `sudo` using local venv (`sudo ./.venv/bin/antigravity-updater --system`) or forwarded PATH (`sudo env "PATH=$PATH" antigravity-updater --system`).
   - **AppArmor / chrome-sandbox startup failure**: Run `sudo env "PATH=$PATH" antigravity-updater --apparmor-sandbox`.
   - **Missing command in PATH (`agy` / `antigravity-ide`)**: Add `~/.local/bin` to the active shell configuration (`~/.bashrc`, `~/.zshrc`).
   - **Uninstallation Requested**: Run `antigravity-updater --uninstall` (with `--user` or `--system`).
   - **Out of date versions**: Run `antigravity-updater` (or target specific components with `--ide`, `--hub`, `--cli`). Preview first with `--check`.
   - **Release endpoint failure**: Read the `ReleaseEndpointError` output, which lists every attempted URL and HTTP status. Re-run with `--debug`, then override endpoints with the `ANTIGRAVITY_*_URL` variables if Google moved them.
   - **Checksum refusal (`Refusing to install an unverified archive`)**: The release endpoint supplied no SHA-512/SHA-256. Prefer waiting for metadata to recover; use `--allow-unverified` only when the endpoint is explicitly trusted.
   - **CLI shows `Self-update: managed by official updater`**: The CLI update is skipped on purpose. Follow [Recipe 7](#recipe-7-official-cli-self-update-conflicts) instead of forcing it.
   - **Running inside WSL** (`"wsl": true` in `--json`): Only the CLI is managed by default. Pass `--ide` / `--hub` explicitly only if the user actually wants GUI apps under WSLg. `--uninstall` still covers all components.

---

## 📋 Common Troubleshooting Recipes for AI Agents

### Recipe 1: Fixing Duplicate Icons & Conflicting Scopes
**Symptom:** User has multiple icons for Antigravity IDE or Hub in their GNOME application launcher.  
**Cause:** The user has both system-wide (`/usr/share/applications/*.desktop`) and user-level (`~/.local/share/applications/*.desktop`) desktop files.  
**Agent Action:**
```bash
# Clean user duplicates and point launcher to system installation:
antigravity-updater --clean-duplicates --system

# If user also wants to delete stale user-level ~/opt directories:
antigravity-updater --clean-duplicates --system --remove-user-dirs
```

---

### Recipe 2: Running System (`/opt`) Updates with `sudo`
**Symptom:** `sudo uv run ...` or `sudo antigravity-updater ...` fails with `sudo: command not found`.  
**Cause:** `/etc/sudoers` has `secure_path` enabled, resetting `$PATH` and stripping `~/.local/bin` and virtualenvs.  
**Agent Action:** Use one of these two verified commands:

1. **When running directly from a cloned repo / local virtualenv:**
   ```bash
   sudo ./.venv/bin/antigravity-updater --system
   ```

2. **When `antigravity-updater` is installed via `uv tool` or `pipx`:**
   ```bash
   sudo env "PATH=$PATH" antigravity-updater --system
   ```

---

### Recipe 3: Ubuntu 24.04+ AppArmor / Sandbox Fix
**Symptom:** Antigravity IDE crashes on startup with `FATAL:zygote_host_impl_linux.cc` or fails to launch on Ubuntu 24.04+.  
**Cause:** AppArmor unprivileged user namespaces (`apparmor_restrict_unprivileged_userns`) block Electron namespace sandboxes.  
**Agent Action:**
Configure the SUID sandbox helper binary with `root:root 4755`:
```bash
# Via updater:
sudo env "PATH=$PATH" antigravity-updater --apparmor-sandbox

# Or direct venv:
sudo ./.venv/bin/antigravity-updater --apparmor-sandbox
```

---

### Recipe 4: Fixing `bash: agy: command not found`
**Symptom:** User installed via user scope (`--user` / default), but typing `agy` or `antigravity-ide` in terminal is not recognized.  
**Cause:** `~/.local/bin` is missing from the user's shell `$PATH`.  
**Agent Action:** Add `~/.local/bin` to the user's active shell configuration:
```bash
# Bash:
echo 'export PATH="$HOME/.local/bin:$PATH"' >> ~/.bashrc && source ~/.bashrc

# Zsh:
echo 'export PATH="$HOME/.local/bin:$PATH"' >> ~/.zshrc && source ~/.zshrc

# Fish:
fish_add_path ~/.local/bin
```

---

### Recipe 5: Clean Uninstallation
**Symptom:** User wants to completely remove components, launcher shortcuts, and context menu integrations.  
**Agent Action:**
```bash
# To uninstall user-level installation:
antigravity-updater --uninstall --user

# To uninstall system-wide installation (/opt):
sudo env "PATH=$PATH" antigravity-updater --uninstall --system

# To uninstall only a specific tool (e.g. IDE):
antigravity-updater --uninstall --ide
```

---

### Recipe 6: GNOME Nautilus "Open in Antigravity IDE" Setup
**Symptom:** Context menu in GNOME Files is missing.  
**Agent Action:**
Install python bindings and restart Nautilus:
```bash
# Ubuntu / Debian:
sudo apt install python3-nautilus && nautilus -q

# Fedora:
sudo dnf install nautilus-python && nautilus -q

# Arch Linux:
sudo pacman -S python-nautilus && nautilus -q
```

---

### Recipe 7: Official CLI Self-Update Conflicts
**Symptom:** `antigravity-updater` prints `Official CLI self-updater detected ... Skipping CLI update`, or `--diagnose` shows `Self-update: managed by official updater`.
**Cause:** The official `agy` binary updates itself. If `missing-ag-updater` also replaced it, the two updaters would fight over the same file. The updater treats the CLI as officially managed when it finds either of these:
1. Backup files from the official updater next to the binary (`agy.<digits>.old`).
2. The official updater state folder `~/.gemini/antigravity-cli/updater/` (`update.lock` / `update_status.json`). This only counts for **user-scope** binaries.

**Decision tree:**
```text
Is a newer CLI version available? (antigravity-updater --cli --check)
├── No  → Nothing to do.
└── Yes → Is self-update detected? (antigravity-updater --diagnose)
    ├── No  → antigravity-updater --cli
    └── Yes → Does `agy update` work?
        ├── Yes → Use `agy update` (preferred, official channel). Done.
        └── No / user wants this tool to own the CLI
            → antigravity-updater --cli --ignore-self-update
              (prefer this over --force, which also reinstalls the same version
               and ignores running processes)
```
**Agent Action:**
```bash
# Preferred: let the official binary update itself
agy update

# Override detection for a single run
antigravity-updater --cli --ignore-self-update

# Override detection permanently (env var or TOML: ignore_self_update = true)
export ANTIGRAVITY_IGNORE_SELF_UPDATE=1
```

> Never delete the `agy.*.old` backups or the official updater state folder just to get around detection. They belong to the official updater.

---

### Recipe 8: Headless / CI / Container Usage
**Symptom:** The updater needs to run without a desktop session (CI runners, Docker images, SSH-only servers).
**Agent Action:**
```bash
# Non-interactive, no desktop integration, explicit scope:
antigravity-updater --cli --user --no-desktop --no-nautilus --no-apparmor-sandbox

# The same thing with environment variables only (useful in Dockerfiles / CI YAML):
export ANTIGRAVITY_CLI=1 ANTIGRAVITY_USER=1 \
       ANTIGRAVITY_NO_DESKTOP=1 ANTIGRAVITY_NO_NAUTILUS=1 \
       ANTIGRAVITY_APPARMOR_SANDBOX=0
antigravity-updater

# Inside a root container (no sudo needed; system paths are used automatically when running as root):
antigravity-updater --cli --system --no-desktop --no-nautilus
```
**Notes for agents:**
- Always pass an explicit scope (`--user` or `--system`). When running as root without a scope, the system paths (`/opt`, `/usr/local/bin`) are used.
- Exit codes: `0` = success (including "up to date", "update available" in `--check` mode, and "skipped because of official self-update"). `1` = at least one operation failed. `--check` does **not** return a non-zero code when updates are available, so read the output instead.
- In containers the official `agy` self-updater usually has no state folder, so detection rarely triggers. In CI images, pin the version by building a new image rather than updating in place.

---

### Recipe 9: Machine Diagnostics, Endpoint Failures & Checksums
**Symptom:** An agent needs to decide what to do without scraping colored output, the updater reports a `ReleaseEndpointError`, or it refuses to install an archive without a checksum.
**Agent Action:**
```bash
# Stable machine-readable diagnostics (JSON, sorted keys):
antigravity-updater --json

# Include URL/checksum/process decisions on stderr:
antigravity-updater --diagnose --debug

# Point at alternative metadata endpoints (comma-separated fallbacks):
export ANTIGRAVITY_IDE_RELEASES_URL="https://primary.example/releases,https://backup.example/releases"
export ANTIGRAVITY_HUB_RELEASES_URL="https://primary.example/releases"
export ANTIGRAVITY_CLI_MANIFEST_URL="https://primary.example/manifests/linux_amd64.json"
antigravity-updater --check
```

`--json` prints diagnostics only and exits; it does not update anything. The payload includes `updater_version`, `os`, `arch`, `wsl`, `ide_installations`, `hub_installations`, `cli_installations`, `running_processes`, `desktop_files`, and `sandbox_status`.

If the updater refuses an IDE/Hub archive because no checksum was supplied, do **not** immediately reach for `--allow-unverified`. First confirm the endpoint is the expected Google URL. Only opt out when the user explicitly trusts that source:
```bash
antigravity-updater --ide --allow-unverified
export ANTIGRAVITY_ALLOW_UNVERIFIED=1
```

---

## ⚙️ Configuration Precedence

Settings are resolved in this order (first match wins):

1. **CLI flags** (e.g. `--force`, `--ignore-self-update`, `--path-cli`)
2. **Environment variables** (`ANTIGRAVITY_*`, with `AG_*` short aliases)
3. **TOML config file** (`--config PATH`, `ANTIGRAVITY_CONFIG`, or the default location below)
4. **Auto-detection / defaults**

| Platform | Default TOML location |
| :--- | :--- |
| Linux | `$XDG_CONFIG_HOME/missing-ag-updater/config.toml` (falls back to `~/.config/...`) |
| macOS | `~/Library/Application Support/missing-ag-updater/config.toml` |
| Windows | `%APPDATA%\missing-ag-updater\config.toml` |

Boolean environment variables accept `1/true/yes/on` and `0/false/no/off`. An explicitly given config file (`--config` / `ANTIGRAVITY_CONFIG`) that is missing or invalid is a hard error. A missing default file is ignored.

TOML keys mirror the CLI flags: `check`, `ide`, `hub`, `cli`, `force`, `ignore_self_update`, `allow_unverified`, `debug`, `system`, `user`, `apparmor_sandbox`, `desktop`, `nautilus`, `dir_ide`, `dir_hub`, and `path_cli`. Release endpoint overrides are **environment-only** and are not read from TOML.

---

## 🔒 Security Model & Verification

Because `missing-ag-updater` downloads binaries, extracts archives, and can mutate system paths or escalate privileges via `sudo`, it follows strict security practices:

1. **Integrity Verification**:
   - **CLI**: Mandatory SHA-512 checksum validation against the manifest before extraction.
   - **IDE & Hub**: SHA-512 and SHA-256 checksum verification when supplied by release endpoints. Missing checksums **fail closed**; the explicit `--allow-unverified` / `ANTIGRAVITY_ALLOW_UNVERIFIED` / TOML `allow_unverified` opt-out exists only for trusted private endpoints.
   - Full download URLs from release metadata (`download_url`, `url`, `downloads`) are used only after the Google domain allowlist check; hard-coded CDN construction is a fallback.
2. **Strict Domain Allowlists**:
   - Downloads are restricted exclusively to official Google HTTPS distribution endpoints (`dl.google.com`, `edgedl.me.gvt1.com`, `storage.googleapis.com`, and `*.google.com` / `*.googleapis.com` / `*.gvt1.com` / `*.googleusercontent.com`).
3. **Subprocess & Execution Safety**:
   - **Zero `shell=True` usage**: All subprocess operations use literal, structured argv lists (`hdiutil`, `sudo`, `tasklist`, `pgrep`, etc.) preventing shell injection attacks.
   - Windows silent installers are executed strictly with fixed arguments `[exe_path, "/S"]`.
4. **Filesystem & Extraction Guardrails**:
   - **Zip-Slip Protection**: Zip extraction explicitly guards against directory traversal attacks via path verification.
   - **Tarball Data Filter**: Tar archive extraction uses Python 3.12+ safe `filter="data"` semantics.
   - **Uninstall Scope Isolation**: Uninstallation safeguards parent directories to avoid removing non-empty custom sibling directories.
5. **AppArmor & SUID Sandbox Security**:
   - `chrome-sandbox` configuration strictly allowlists Ubuntu-style distributions and verifies AppArmor status before applying `root:root 4755` permissions.

### Process Detection Limitations

Process checks are a safety net, not a guarantee:

- Linux reads `/proc/<pid>/cmdline` (falling back to `pgrep`), macOS uses `pgrep`, and Windows uses `tasklist`.
- Matching combines executable names with install-path hints. Renamed binaries, wrapper scripts, containerized processes, and some IDE child processes can evade detection.
- The updater filters itself, plain shell commands that only mention a path, and unrelated `agy` binaries to avoid blocking legitimate runs.
- Use `--debug` to log each match/ignore decision and `--diagnose` / `--json` to see reported PIDs. Prefer closing apps over using `--force`.

### Release Endpoint Resilience

Release metadata endpoints are unofficial Cloud Run services. Each component supports ordered fallbacks via `ANTIGRAVITY_IDE_RELEASES_URL`, `ANTIGRAVITY_HUB_RELEASES_URL`, and `ANTIGRAVITY_CLI_MANIFEST_URL` (comma-separated). `ReleaseEndpointError` reports every attempted URL and status. When a payload provides a full download URL, it takes precedence over the hard-coded CDN path, subject to the domain allowlist.

---

## 🐍 Programmatic Python API for Custom Automation

You can import functions directly in Python scripts or subagents:

```python
from missing_ag_updater import (
    __version__,
    ReleaseEndpointError,
    clean_duplicate_desktop_entries,
    detect_cli_self_update,
    diagnose_all,
    find_all_cli_installations,
    find_all_hub_installations,
    find_all_ide_installations,
    resolve_config,
    set_debug_enabled,
    uninstall_ide,
    update_cli,
    update_ide,
)

print(f"missing-ag-updater {__version__}")

# Enable debug logging exactly like `--debug` (writes to stderr):
set_debug_enabled(True)

# 1. Run complete machine diagnostics (returns structured dict)
diag = diagnose_all()
print(f"OS: {diag['os']} arch: {diag['arch']}")

# 1b. Fail clearly when every release endpoint is unreachable:
from missing_ag_updater.updater import fetch_release_payload

try:
    releases = fetch_release_payload("ide")
except ReleaseEndpointError as endpoint_error:
    print(f"Metadata endpoints failed: {endpoint_error}")
for inst in diag["ide_installations"]:
    print(f"Found IDE version {inst['version']} at {inst['install_dir']} [{inst['scope']}]")

# Or inspect typed InstallationInfo dataclasses:
for inst in find_all_ide_installations():
    print(f"Found IDE {inst.version} (writable={inst.is_writable}) at {inst.install_dir}")

# CLI installations report official self-update detection (None if not detected):
for cli_inst in find_all_cli_installations():
    print(f"CLI {cli_inst.version} at {cli_inst.launcher_path}: self_update={cli_inst.self_update}")

# 2. Clean duplicate desktop entries
removed_files = clean_duplicate_desktop_entries(keep_scope="system", remove_user_dirs=True)

# 3. Resolve paths the same way the CLI does (CLI args > env > TOML > auto-detect), then dry-run
cfg = resolve_config()
success = update_ide(cfg.dir_ide, cfg.ide_launcher, dry_run=True, scope=cfg.scope)

# 4. CLI update that respects the official self-updater (skips if detected unless overridden)
if detect_cli_self_update(cfg.path_cli) is None:
    update_cli(cfg.path_cli, dry_run=True)
else:
    update_cli(cfg.path_cli, ignore_self_update=True)  # only when explicitly requested

# 5. Perform clean uninstallation
uninstall_success = uninstall_ide(scope="user", force=True)
```

---

## 💻 Development, Testing & Verification Commands

When modifying `missing-ag-updater` source code:

```bash
# 1. Run complete test suite with coverage (CI enforces >=85%):
./.venv/bin/pytest --cov=missing_ag_updater --cov-report=term-missing --cov-fail-under=85

# 2. Run linter, formatting, and type checks:
./.venv/bin/ruff check src
./.venv/bin/ruff format --check src
./.venv/bin/mypy src

# 3. Format code:
./.venv/bin/ruff format src

# Or use the Makefile quality gate (equivalent, plus security scans):
make lint          # ruff check + format --check
make test          # mypy + pytest-cov (>=85%) + coverage badge
make secrets       # TruffleHog (needs trufflehog or docker)
make trivy         # Trivy HIGH/CRITICAL scan (needs trivy or docker)
make release-check # all of the above, before tagging a release
```

The full release sequence (version bump, changelog, tag, GitHub release, PyPI publish) is documented in [`docs/release-process.md`](docs/release-process.md).

**Maintainer rules of thumb:**
- Start with `antigravity-updater --diagnose` (or `diagnose_all()`) before changing anything, and prefer `--check` before real updates.
- When touching download/URL logic, add a regression test that mocks the release endpoints and checks the checksum and extraction paths.
- Never remove the download domain allowlist or introduce `shell=True`.
- Tests must be hermetic: never depend on host state such as `~/.gemini/antigravity-cli`. The autouse fixture in `src/tests/conftest.py` already isolates the official CLI updater state folder.
- Keep the version in `src/missing_ag_updater/const.py` only; `pyproject.toml` reads it dynamically. Use `make version BUMP=minor`.
- All module-level constants (paths, allowlists, patterns, env var names, marker tuples) belong in `src/missing_ag_updater/const.py`, never in other modules. Import them from `.const`.

All contributions must maintain:
- **100% type safety** (`mypy` strict mode with full annotations).
- **Zero `ruff` lint/format warnings**.
- **Comprehensive test coverage** via `pytest`.
- **Pythonic code style ("Write Python like a true Pythonista")**:
  - A true Pythonista never nests endless `with patch(...)` context managers inside tests — write clean, declarative tests using `@patch` decorators and pytest fixtures.
  - Use pytest's built-in `monkeypatch` fixture (`monkeypatch.setenv()` / `monkeypatch.delenv()`) for all environment variable manipulations instead of manual dictionary patching.
  - Always specify explicit `encoding="utf-8"` on all text-mode `open()` operations.
  - Avoid single-letter variable names across all test and source files; choose descriptive, idiomatic names.
  - Keep code flat, explicit, readable, and structured around clean type hints and dataclasses.
