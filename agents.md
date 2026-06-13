# AI Agent Integration Guide

Welcome! If you are an AI coding agent or an automated workspace manager, this document outlines how you can programmatically and via CLI use the `missing-ag-updater` to keep the Antigravity developer suite (IDE, Hub, and CLI) up to date.

---

## Workspace Agent Checklists

Before starting your developer workflows, you can query and update the Antigravity tools using these recipes.

### 1. Verification Checklist (Dry Run)

To check if the developer tools are up-to-date without modifying files, run:
```bash
antigravity-updater --check
```
An exit code of `0` indicates no updates are needed or everything is already up-to-date.

### 2. Force Updating in Headless Environments

If you are running in a CI/CD environment or a sandbox terminal, process checks might flag parent terminal launchers. To bypass active process warnings and force download the latest versions, run:
```bash
antigravity-updater --force
```

---

## Programmatic Python API

If you are writing custom script automations, you can import functions directly from the package instead of shelling out to the CLI.

### Importing Update Managers

```python
from missing_ag_updater.updater import update_ide, update_hub, update_cli
from missing_ag_updater.const import DEFAULT_IDE_DIR, DEFAULT_HUB_DIR, DEFAULT_CLI_BINARY

# 1. Update the IDE
ide_success = update_ide(
    ide_dir=DEFAULT_IDE_DIR,
    launcher_path="/home/user/.local/bin/antigravity-ide",
    dry_run=False,
    force=True
)

# 2. Update the CLI
cli_success = update_cli(
    cli_binary=DEFAULT_CLI_BINARY,
    dry_run=False,
    force=True
)
```

---

## Exit Code Reference

Automated scripts should verify exit codes to determine execution status:

| Exit Code | Meaning | Action for Agent |
| :--- | :--- | :--- |
| `0` | Success / Up-to-date | Proceed with developer task. |
| `1` | Error (Network, Verification, or Locked process) | Inspect logs. Try running with `--force` if processes are locked. |

---

## Path & Binary Schema Overrides

If your execution environment uses custom sandbox paths, you can override default directories via CLI arguments:

```bash
antigravity-updater \
  --dir-ide "/home/sandbox/opt/Antigravity" \
  --dir-hub "/home/sandbox/opt/Hub" \
  --path-cli "/home/sandbox/bin/agy"
```

---

## Enforced Code Style & Development Standards

If you are an AI agent contributing code or writing tests for this repository, you must adhere to the following standards:

1. **Coding Style & Formatting**:
   * All code must conform to the formatting rules enforced by **Ruff**.
   * Run code formatting before submitting:
     ```bash
     make format
     ```
   * Verify linting passes with:
     ```bash
     make lint
     ```

2. **Static Typing**:
   * The codebase is **strictly typed**. All functions, arguments, and return types must be fully annotated using standard Python type hints.
   * Run type checking on the source files:
     ```bash
     uv run mypy src
     ```
   * All type checks must pass cleanly with no warnings or errors.

3. **Function Arguments**:
   * Always prefer **named (keyword) arguments** when calling functions with multiple parameters (e.g. `update_ide(ide_dir=..., launcher_path=..., dry_run=...)`). This increases clarity and reduces signature mismatch risks.

4. **Testing Requirements**:
   * **Every new module or change requires corresponding tests** in the `src/tests/` directory.
   * The test suite is executed using:
     ```bash
     make test
     ```
   * All tests must pass, and the coverage badge should be updated automatically by the test script.

