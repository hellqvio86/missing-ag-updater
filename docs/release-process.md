# Release Process

This checklist keeps releases reproducible and ensures the version, changelog, tags, GitHub release, and PyPI package stay in sync.

The version has a **single source of truth**: `__version__` in `src/missing_ag_updater/const.py`. `pyproject.toml` reads it dynamically through Hatchling. Do not add a static version anywhere else.

---

## 1. Prepare the release

- [ ] Ensure `main` is clean and up to date (`git switch main && git pull --ff-only`).
- [ ] Run the full quality gate:
  ```bash
  make lint
  make test          # mypy + pytest with --cov-fail-under=85
  make secrets       # TruffleHog (verified secrets only)
  make trivy         # HIGH/CRITICAL vulnerabilities
  ```
  Or run everything at once:
  ```bash
  make release-check
  ```
- [ ] Run the relevant rows of the [platform test matrix](platform-test-matrix.md) (at minimum the platform affected by the change).
- [ ] Confirm no `shell=True`, no new download domains, and no unverified install paths slipped in.

## 2. Bump the version and update the changelog

```bash
# patch (0.6.0 -> 0.6.1), minor (0.6.1 -> 0.7.0), or major (0.7.0 -> 1.0.0)
make version BUMP=minor
```

- [ ] Confirm `src/missing_ag_updater/const.py` contains the new `__version__`.
- [ ] Add a new version section to `CHANGELOG.md` with today's date (or move entries from an existing `Unreleased` section).
- [ ] Add the compare link at the bottom of `CHANGELOG.md` if a new version section was added.
- [ ] Check that README examples do not pin an old version.

## 3. Commit and push

```bash
git add src/missing_ag_updater/const.py CHANGELOG.md
git commit -m "chore(release): bump version to X.Y.Z"
git push origin main
```

On a push to `main`, CI:

1. Runs lint, type checks, and tests on Python 3.12–3.15.
2. Detects that `__version__` changed compared with `HEAD~1`.
3. Creates and pushes the `vX.Y.Z` tag automatically.
4. Builds the wheel/sdist and SBOM.
5. Creates a **draft** GitHub release with generated release notes.

- [ ] Wait for the `All Checks Passed` and `Draft Release` jobs to succeed.
- [ ] Confirm the `vX.Y.Z` tag exists: `git fetch --tags && git tag --list 'v*' | tail`.

## 4. Review the draft release

- [ ] Open the draft GitHub release and verify the tag, artifacts (`.whl`, `.tar.gz`, `sbom.spdx.json`), and notes.
- [ ] Replace the auto-generated notes with the `CHANGELOG.md` section for this version if it is clearer.
- [ ] Confirm the package metadata shows the correct version:
  ```bash
  ./.venv/bin/python -c "import missing_ag_updater; print(missing_ag_updater.__version__)"
  ```
  (or `uv run python -c ...`).

## 5. Publish

- [ ] Publish the GitHub release (this triggers the `publish` job on `release: published`).
- [ ] Wait for the PyPI publish job to finish successfully (trusted publishing, environment `pypi`).
- [ ] Verify PyPI:
  ```bash
  pip index versions missing-ag-updater
  uvx --from missing-ag-updater==X.Y.Z antigravity-updater --version
  ```

## 6. Post-release verification

- [ ] Install from PyPI in a clean environment and run:
  ```bash
  antigravity-updater --version
  antigravity-updater --json
  antigravity-updater --check
  ```
- [ ] Confirm the coverage badge on `main` was updated by the badge job (commit contains `[skip ci]`).
- [ ] If something is wrong, publish a patch release; do not rewrite a published tag.

---

## Troubleshooting the release jobs

| Symptom | Likely cause | Action |
| :--- | :--- | :--- |
| Draft release job skipped | `__version__` did not change, or `HEAD~1` had no readable `const.py` | Bump the version and push again. |
| Tag already exists | Re-ran a release for the same version | Do not force-push tags; bump to the next patch version. |
| PyPI upload rejected | Version already published | Bump the version; PyPI does not allow overwriting. |
| Coverage job fails | Coverage below 85% | Add tests before retrying the release. |
