# Linux Troubleshooting & Diagnostics Guide

This document covers common issues, system quirks, and diagnostic steps when installing, running, and updating the Google Antigravity developer suite on Linux distributions (Ubuntu, Debian, Fedora, Arch Linux, etc.).

---

## 1. Diagnostics First: Inspecting Your System State

If you run into issues with versions, multiple icons, or missing commands, run the built-in diagnostic tool first:

```bash
antigravity-updater --diagnose

# Machine-readable JSON for scripts/agents:
antigravity-updater --json

# Include endpoint URLs, checksum results, and process decisions on stderr:
antigravity-updater --diagnose --debug
```

This will print a complete system report detailing:
- All discovered IDE, Hub, and CLI installations across user (`~/opt`, `~/.local/bin`) and system (`/opt`, `/usr/local/bin`) scopes.
- Permissions (whether each path is writable or requires `sudo`).
- Active `.desktop` launcher files and their registered `Exec=` commands.
- Currently running Antigravity processes (PIDs).
- AppArmor / sandbox status.

The `--json` payload is stable for automation: `updater_version`, `os`, `arch`, `ide_installations`, `hub_installations`, `cli_installations`, `running_processes`, `desktop_files`, and `sandbox_status`.

---

## 2. Fixing Multiple / Duplicate Launcher Icons

### Symptom
Your application launcher shows multiple icons for Antigravity IDE or Antigravity Hub.

### Cause
You may have installed Antigravity to both user-level directories (`~/opt`) and system-wide directories (`/opt`), or manually installed `.desktop` files in both `~/.local/share/applications` and `/usr/share/applications`.

### Solution
Use the automated `--clean-duplicates` tool:

```bash
# Keep system-wide installation and purge user-level desktop shortcuts:
antigravity-updater --clean-duplicates --system

# Optional: Also remove stale user installation folders (~/opt/Antigravity*):
antigravity-updater --clean-duplicates --system --remove-user-dirs
```

---

## 3. Ubuntu 24.04+ AppArmor / Sandbox Crashes

### Symptom
Launching Antigravity IDE crashes immediately with errors such as:
```text
[FATAL:zygote_host_impl_linux.cc] Check failed: . : Invalid argument (22)
```
or
```text
The SUID sandbox helper binary was found, but is not configured with proper permissions.
```

### Cause
1. **AppArmor Unprivileged User Namespaces:** Ubuntu 24.04 enables kernel-level AppArmor restrictions on unprivileged user namespaces (`apparmor_restrict_unprivileged_userns`). Chromium-based Electron applications require either a setuid root sandbox helper (`chrome-sandbox`) or an unprivileged namespace profile.
2. **Directory Spaces Bug:** An upstream Chromium bug in `zygote_host_impl_linux.cc` causes crashes if the application directory path contains spaces (e.g., `~/opt/Antigravity IDE`). The updater defaults to hyphenated names (`~/opt/Antigravity-IDE`) on Ubuntu to avoid this.

### Solution

#### Option A: Configure Setuid Root Permissions (Recommended for Sandbox Issues)
Run the updater with the `--apparmor-sandbox` flag using `sudo`:

```bash
sudo env "PATH=$PATH" antigravity-updater --apparmor-sandbox
```

This sets `root:root` ownership and `4755` permissions on the `chrome-sandbox` binary.

#### Option B: Clean Existing Duplicate/Spaced Folders
If an older installation used a folder name with spaces, the updater resolves the legacy path and migrates it to the hyphenated name automatically, but only when it lives under the default `~/opt` or `/opt` parent. Custom `--dir-ide` paths are never moved automatically.

To inspect or clean duplicate launchers left behind by mixed scopes:

```bash
antigravity-updater --clean-duplicates
```

The hyphenated `~/opt/Antigravity-IDE` name exists because Chromium truncates paths containing spaces when launching `chrome-sandbox`, producing `FATAL: Check failed: . : Invalid argument (22)`. The updater uses the hyphenated name on Ubuntu-style distributions; other distributions may still use the spaced name unless overridden.

---

## 4. "Command not found: `agy`" or "`antigravity-ide`"

### Symptom
After installing or updating as a regular user, running `agy` or `antigravity-ide` in the terminal returns:
```text
bash: agy: command not found
```

### Cause
User-level symlinks are placed in `~/.local/bin/`. On some Linux distributions, `~/.local/bin` is not included in the default `$PATH`.

### Solution
Add `~/.local/bin` to your shell's configuration file:

- **For Bash** (`~/.bashrc` or `~/.profile`):
  ```bash
  echo 'export PATH="$HOME/.local/bin:$PATH"' >> ~/.bashrc
  source ~/.bashrc
  ```

- **For Zsh** (`~/.zshrc`):
  ```bash
  echo 'export PATH="$HOME/.local/bin:$PATH"' >> ~/.zshrc
  source ~/.zshrc
  ```

- **For Fish** (`~/.config/fish/config.fish`):
  ```fish
  fish_add_path ~/.local/bin
  ```

---

## 5. Permission Denied or `sudo: command not found` During System (`/opt`) Updates

### Symptom
Running `antigravity-updater --system` fails with:
```text
PermissionError: [Errno 13] Permission denied: '/opt/antigravity-ide'
```
or running with `sudo` fails with:
```text
sudo: uv: command not found
```
or
```text
sudo: antigravity-updater: command not found
```

### Cause
1. System-wide installations in `/opt` and `/usr/local/bin` require `root` write privileges.
2. `sudo` uses a security policy called `secure_path` in `/etc/sudoers`, which resets the `$PATH` environment variable and ignores user directories like `~/.local/bin` or your current virtual environment. Therefore, `sudo uv` or `sudo antigravity-updater` cannot find tools installed in user space.

### Solutions

#### Solution A: Direct Virtualenv Binary Path (When running from a cloned Git repo)
If you are developing or running from a local repository with a virtual environment:
```bash
sudo ./.venv/bin/antigravity-updater --system
```
This directly calls the virtual environment binary as `root` without relying on `$PATH` lookup.

#### Solution B: Pass Current User `$PATH` to `sudo` (When installed via `uv tool` or `pipx`)
If `antigravity-updater` is installed in `~/.local/bin`:
```bash
sudo env "PATH=$PATH" antigravity-updater --system
```
Or for `uv run`:
```bash
sudo env "PATH=$PATH" uv run antigravity-updater --system
```

#### Solution C: Stick to User Scope (No `sudo` needed)
If you do not want to manage system permissions in `/opt`, install to your user home directory:
```bash
antigravity-updater --user
```

---

## 6. Active Process Lockup Warnings

### Symptom
The updater warns that Antigravity IDE or Hub is currently running and halts:
```text
[WARNING] Active Antigravity IDE process detected (PID: 12345).
```

### Cause
Updating files while an Electron application or VS Code instance is actively running can corrupt open extensions, crash active language servers, or cause file lock errors.

### Solution
1. **Standard:** Save your work and close all open Antigravity IDE or Hub windows, then rerun `antigravity-updater`.
2. **Verify the detected process:** Run `antigravity-updater --json | jq '.running_processes'` or `antigravity-updater --diagnose --debug` to see which PIDs matched and why.
3. **Force Update:** If you are running in a CI/CD environment or headless terminal where you know it is safe to proceed:
   ```bash
   antigravity-updater --force
   ```

> [!NOTE]
> Process detection is a safety net, not a guarantee. It matches executable names plus install-path hints from `/proc/<pid>/cmdline` (Linux), `pgrep` (macOS), or `tasklist` (Windows). Wrapper scripts, renamed binaries, containerized processes, and some IDE child processes may not be detected. The updater filters out its own process and shell commands that merely mention a path. If a false positive still blocks you, confirm with `--debug` before using `--force`.

---

## 8. Release Endpoint Failures or Checksum Refusals

### Symptom

```text
Failed to check IDE updates: Could not fetch release metadata for 'ide' from any endpoint ...
```

or

```text
Refusing to install an unverified archive. Re-run with --allow-unverified ...
```

### Cause

Release metadata comes from unofficial Cloud Run endpoints that Google may move or retire. IDE/Hub installs also fail closed when the endpoint supplies no SHA checksum.

### Solution

1. **Inspect every attempted URL** (the error lists each one with its HTTP status), or re-run with `--debug` for the exact requests.
2. **Override the endpoint** with a comma-separated fallback list:
   ```bash
   export ANTIGRAVITY_IDE_RELEASES_URL="https://primary.example/releases,https://backup.example/releases"
   export ANTIGRAVITY_HUB_RELEASES_URL="https://primary.example/releases"
   export ANTIGRAVITY_CLI_MANIFEST_URL="https://primary.example/manifests/linux_amd64.json"
   antigravity-updater --check
   ```
3. **Checksum refusal:** prefer waiting for metadata to recover. Use `--allow-unverified` (or `allow_unverified = true`) only if you explicitly trust the endpoint.
4. **Report the outage** on GitHub with the failed URLs and status codes so the defaults can be updated.

---

## 7. Nautilus Context Menu ("Open in Antigravity IDE") Missing

### Symptom
Right-clicking a file or directory in GNOME Files (Nautilus) does not display the **"Open in Antigravity IDE"** context menu item.

### Cause
GNOME requires the `nautilus-python` binding to be installed, and the Nautilus process must be restarted to load newly registered Python extensions.

### Solution

1. **Install `nautilus-python` for your distribution:**

   - **Ubuntu / Debian**:
     ```bash
     sudo apt install python3-nautilus
     ```
   - **Fedora / RHEL**:
     ```bash
     sudo dnf install nautilus-python
     ```
   - **Arch Linux / Manjaro**:
     ```bash
     sudo pacman -S python-nautilus
     ```
   - **openSUSE**:
     ```bash
     sudo zypper install python3-nautilus
     ```

2. **Restart Nautilus:**
   ```bash
   nautilus -q
   ```

3. **Re-run the updater:**
   ```bash
   antigravity-updater
   ```
