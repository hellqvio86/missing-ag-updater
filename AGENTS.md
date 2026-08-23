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

2. **Analyze Output & Execute Matching Action**:
   - **Duplicate `.desktop` entries / launcher icons**: Run `antigravity-updater --clean-duplicates` (use `--system` and optionally `--remove-user-dirs`).
   - **Broken Permissions / `/opt` Installation**: Run with `sudo` using local venv (`sudo ./.venv/bin/antigravity-updater --system`) or forwarded PATH (`sudo env "PATH=$PATH" antigravity-updater --system`).
   - **AppArmor / chrome-sandbox startup failure**: Run `sudo env "PATH=$PATH" antigravity-updater --apparmor-sandbox`.
   - **Missing command in PATH (`agy` / `antigravity-ide`)**: Add `~/.local/bin` to the active shell configuration (`~/.bashrc`, `~/.zshrc`).
   - **Uninstallation Requested**: Run `antigravity-updater --uninstall` (with `--user` or `--system`).
   - **Out of date versions**: Run `antigravity-updater` (or target specific components with `--ide`, `--hub`, `--cli`).

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

## 🔒 Security Model & Verification

Because `missing-ag-updater` downloads binaries, extracts archives, and can mutate system paths or escalate privileges via `sudo`, it follows strict security practices:

1. **Integrity Verification**:
   - **CLI**: Mandatory SHA-512 checksum validation against the manifest before extraction.
   - **IDE & Hub**: SHA-512 and SHA-256 checksum verification when hashes are supplied by release endpoints.
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

---

## 🐍 Programmatic Python API for Custom Automation

You can import functions directly in Python scripts or subagents:

```python
from missing_ag_updater import (
    clean_duplicate_desktop_entries,
    diagnose_all,
    find_all_cli_installations,
    find_all_hub_installations,
    find_all_ide_installations,
    resolve_config,
    uninstall_cli,
    uninstall_hub,
    uninstall_ide,
    update_cli,
    update_hub,
    update_ide,
)

# 1. Run complete machine diagnostics (returns structured dict)
diag = diagnose_all()
print(f"OS: {diag['os']}")
for inst in diag["ide_installations"]:
    print(f"Found IDE version {inst['version']} at {inst['install_dir']} [{inst['scope']}]")

# Or inspect typed InstallationInfo dataclasses:
ide_installs = find_all_ide_installations()
for inst in ide_installs:
    print(f"Found IDE {inst.version} (writable={inst.is_writable}) at {inst.install_dir}")

# 2. Clean duplicate desktop entries
removed_files = clean_duplicate_desktop_entries(keep_scope="system", remove_user_dirs=True)

# 3. Perform silent dry-run check or force update
success = update_ide(dry_run=True, force=False, scope="user")

# 4. Perform clean uninstallation
uninstall_success = uninstall_ide(scope="user", force=True)
```

---

## 💻 Development, Testing & Verification Commands

When modifying `missing-ag-updater` source code:

```bash
# 1. Run complete test suite with coverage:
./.venv/bin/pytest --cov=missing_ag_updater --cov-report=term-missing

# 2. Run linter, formatting, and type checks:
./.venv/bin/ruff check src
./.venv/bin/ruff format --check src
./.venv/bin/mypy src

# 3. Format code:
./.venv/bin/ruff format src
```

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
