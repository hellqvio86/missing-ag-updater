# Platform Test Matrix (Manual Checklist)

Unit tests are hermetic and run on Linux CI. The checks below cover the OS-specific paths that unit tests mock (DMG mounting, silent EXE installers, AppArmor/SUID, mixed scopes). Run the relevant block before a release and record the result.

Legend: `[ ]` not run, `[x]` passed, `[!]` failed (open an issue with `--debug` output).

---

## Common Preconditions

- [ ] `antigravity-updater --version` (or `python -m missing_ag_updater --version`) works.
- [ ] `antigravity-updater --json` returns valid JSON with `updater_version`, `os`, and `arch`.
- [ ] `antigravity-updater --diagnose --debug` completes without a traceback.
- [ ] `antigravity-updater --check` does not modify the installation.
- [ ] Exit code is `0` for up-to-date / update-available checks and `1` when an operation fails.

```bash
# Quick parse check (Linux/macOS):
antigravity-updater --json | python3 -m json.tool > /dev/null
```

---

## Linux — Ubuntu 24.04+ (AppArmor)

- [ ] `--diagnose` reports `sandbox_status.apparmor_active: true` and `distro_ubuntu_style: true`.
- [ ] User install: `antigravity-updater --user` places the IDE at `~/opt/Antigravity-IDE` (hyphenated).
- [ ] Legacy `~/opt/Antigravity IDE` is migrated to the hyphenated path; a custom `--dir-ide` path is left untouched.
- [ ] `sudo env "PATH=$PATH" antigravity-updater --system` installs under `/opt/antigravity-ide` and `/opt/antigravity`.
- [ ] Launchers exist in `~/.local/bin` (user) or `/usr/local/bin` (system).
- [ ] `sudo env "PATH=$PATH" antigravity-updater --apparmor-sandbox` sets `chrome-sandbox` to `root:root 4755`.
- [ ] IDE launches without `FATAL:zygote_host_impl_linux.cc` errors.
- [ ] `--clean-duplicates --system` removes duplicate user `.desktop` files but leaves system entries intact.
- [ ] `--clean-duplicates --system --remove-user-dirs` removes stale `~/opt/Antigravity*` directories, never `/opt` itself.
- [ ] `--uninstall --user` removes components, launchers, desktop entries, and Nautilus files.

## Linux — Non-Ubuntu (Fedora / Arch / Debian)

- [ ] `--diagnose` reports `distro_ubuntu_style: false`; automatic SUID changes are not applied.
- [ ] Default IDE directory follows the distribution naming rule (`~/opt/Antigravity IDE` on non-Ubuntu-style distros).
- [ ] `--apparmor-sandbox` is a no-op or explains that the distro is not allow-listed (no silent permission change).
- [ ] Desktop launchers use the correct `Exec=` path and icon.
- [ ] Nautilus context menu appears after installing `nautilus-python` and restarting Nautilus.
- [ ] `--uninstall --system` does not remove sibling content under `/opt`.

## Linux — Mixed Scope

- [ ] Install to user scope, then to system scope with `sudo`.
- [ ] `--diagnose` shows both installations with distinct `scope` values.
- [ ] `--clean-duplicates --system` keeps the system installation and removes user launchers.
- [ ] `--json` shows the expected `desktop_files` and `running_processes` entries.

---

## macOS

- [ ] System install: `sudo antigravity-updater --system` copies `.app` bundles into `/Applications`.
- [ ] User install: `antigravity-updater --user` copies bundles into `~/Applications` without `sudo`.
- [ ] DMG is attached with `hdiutil`, the `.app` is copied, and the volume is detached (check `hdiutil info`).
- [ ] A busy/still-mounted DMG produces a clear error rather than a partial install.
- [ ] CLI binary is linked to `~/.local/bin/agy` (user) or `/usr/local/bin/agy` (system).
- [ ] `--diagnose` uses `pgrep` and reports running PIDs.
- [ ] `--uninstall --user` and `--uninstall --system` remove the expected bundles and CLI links.

---

## Windows

- [ ] `antigravity-updater` resolves `%LOCALAPPDATA%` paths for IDE, Hub, and CLI.
- [ ] Silent installer runs with `/S` and produces no interactive window.
- [ ] Running IDE/Hub produces the active-process warning; `--force` proceeds.
- [ ] PATH contains the CLI directory after install; a new terminal can run `agy`.
- [ ] `--diagnose` uses `tasklist` and reports running PIDs.
- [ ] `--uninstall --user` removes installed components and PATH entries created by the updater.
- [ ] `--json` parses with PowerShell: `antigravity-updater --json | ConvertFrom-Json`.

---

## Cross-Platform Failure Modes

- [ ] All release endpoints unreachable: `ReleaseEndpointError` lists each URL and status.
- [ ] Endpoint override with a valid URL succeeds: `ANTIGRAVITY_IDE_RELEASES_URL=... antigravity-updater --ide --check`.
- [ ] Metadata without checksums refuses IDE/Hub installs; `--allow-unverified` overrides.
- [ ] CLI archive with a bad SHA-512 is rejected.
- [ ] Official `agy` self-update detected: CLI update is skipped; `--ignore-self-update` overrides.
- [ ] `--debug` output contains no secrets, tokens, or credentials.
- [ ] `--json` output is not mixed with spinner/progress text.

---

## Record

| Date | Platform | Version | Result | Notes |
| :--- | :--- | :--- | :--- | :--- |
| | | | | |
