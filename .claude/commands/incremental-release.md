# Incremental Release

Run this after every feature update to bump the version, push to GitHub, build locally, and update the local Debian installation.

## Steps

Follow these steps in order:

### 1. Commit any uncommitted changes

Check `git status`. If there are uncommitted changes, stage and commit them with an appropriate message describing what was changed. Ask the user for a commit message if the changes are unclear.

### 2. Bump the patch version

Run the release script in deb-only mode (this bumps the version in `pyproject.toml` and `app/src/about_widget.py`, then builds the .deb):

```bash
./build.sh --release-deb
```

This will:
- Increment the patch version (e.g., 1.14.7 -> 1.14.8)
- Build the Debian package to `dist/` as `X.Y.Z~local<timestamp>` (a local build; see Notes)

### 3. Commit the version bump

Stage and commit the version bump files:
- `pyproject.toml`
- `app/src/about_widget.py`

Use the commit message format: `chore: bump version to X.Y.Z`

### 4. Push to GitHub

```bash
git push origin main
```

### 5. Install the new .deb locally

```bash
./build.sh --install
```

This installs/upgrades the local Debian package using `sudo dpkg -i`.

### 6. Report completion

Tell the user:
- The old and new version numbers
- That the package was pushed to GitHub
- That the local installation was updated
- Remind them to restart the app if it's currently running

## Notes

- This is a **patch release** (third version number). For minor/major bumps, the user should specify explicitly.
- The build uses `--deb-only` mode since this is for personal local use, not a full public release with AppImage/tarball.
- If the build or install fails, stop and report the error rather than continuing.
- **Local builds are versioned `X.Y.Z~local<timestamp>`** (since 1.14.26). The `~` sorts below
  `X.Y.Z`, so when a `vX.Y.Z` tag is released, the CI build (Ubuntu 26.04 container, the one
  on GitHub and in the APT repo at apps.danielrosehill.com/apt) replaces the local one via
  `apt upgrade`. Before this, a local and a CI build both claimed 1.14.25 and apt showed
  "upgradable from 1.14.25 to 1.14.25".
- The .deb bundles a venv tied to the build machine's Python minor, and `Depends` pins it
  (`python3 (>= 3.14), python3 (<< 3.15)` on Ubuntu 26.04). It will not install on another
  Ubuntu release; that is deliberate. The 1.14.25 CI build shipped a Python 3.10 venv and
  could not run on 3.14.

$ARGUMENTS
